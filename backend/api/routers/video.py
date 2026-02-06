from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
import os
import cv2
import numpy as np
from datetime import datetime
import tempfile
from backend.services.ml_service import ml_service
from backend.db.database import SessionLocal
from backend.db.models import Alert

router = APIRouter()

async def process_video_file_task(video_path: str):
    """
    Process video file in background/async
    """
    if not ml_service.detector:
        return {"error": "Models not loaded"}

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30
    
    frame_count = 0
    alerts = []
    
    db = SessionLocal()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every 10th frame for speed
            if frame_count % 10 == 0 and ml_service.detector and ml_service.risk_engine:
                # Detect
                detection = ml_service.detector.process_frame(frame)
                
                # Calculate risk
                risk_score, risk_factors = ml_service.risk_engine.calculate_risk(
                    detection,
                    context={'hour': datetime.now().hour}
                )
                
                # Generate alert if high risk
                if risk_score > 50:
                    alert_data = ml_service.risk_engine.generate_alert(risk_score, risk_factors)
                    alert_data['timestamp_seconds'] = frame_count / fps
                    alert_data['frame_number'] = frame_count
                    alerts.append(alert_data)
                    
                    # Save to DB
                    new_alert = Alert(
                        level=alert_data['level'],
                        risk_score=alert_data['score'],
                        camera_id="UPLOADED_VIDEO",
                        location="Unknown",
                        risk_factors=alert_data['top_factors'],
                        status="pending"
                    )
                    db.add(new_alert)
                    db.commit()

            frame_count += 1
    except Exception as e:
        print(f"Error processing video: {e}")
    finally:
        cap.release()
        db.close()
    
    return alerts

@router.post("/process/video")
async def process_video(file: UploadFile = File(...)):
    """
    Process uploaded video and return analysis
    """
    try:
        # Ensure temp directory
        os.makedirs("/tmp", exist_ok=True)
        # On windows /tmp might not work or exist. Use local tmp.
        
        # Create a temp file
        fd, video_path = tempfile.mkstemp(suffix=f"_{file.filename}")
        os.close(fd)
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process video (awaiting here for demo simplicity, ideally background task)
        alerts = await process_video_file_task(video_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "alerts_found": len(alerts),
            "alerts": alerts
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



