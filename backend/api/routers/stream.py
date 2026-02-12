from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.ml_service import ml_service
from backend.services.video_storage_service import video_storage_service
from backend.db.database import SessionLocal
from backend.db.models import Alert
import cv2
import numpy as np
import asyncio
import base64
from datetime import datetime

router = APIRouter()

# Helper for non-blocking DB write
def save_alert_sync(alert_data):
    try:
        db = SessionLocal()
        new_alert = Alert(
            level=alert_data['level'],
            risk_score=float(alert_data['score']),
            camera_id="CAM-01", # Placeholder
            location="Main Feed",
            risk_factors=alert_data.get('top_factors', []),
            status="pending",
            timestamp=datetime.utcnow()
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        db.close()
        return new_alert.id
    except Exception as e:
        print(f"DB Write Error: {e}")
        return None

@router.websocket("/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video processing
    Optimized: Frame skipping + Resizing + Non-blocking DB
    """
    await websocket.accept()
    print("WebSocket connected (Robust)")
    
    frame_count = 0
    SKIP_FRAMES = 2 # Process 1 out of every 3 frames
    
    # State for deduping alerts (prevent spamming DB)
    last_alert_time = 0
    ALERT_COOLDOWN = 10 # Seconds between persistent alerts
    
    cached_result = {
        "detection": {"poses": [], "objects": []}, 
        "risk_score": 0, 
        "alert": None,
        "faces": []
    }

    try:
        while True:
            # Receive frame from client
            try:
                data = await websocket.receive_bytes()
            except Exception:
                break # Client disconnected

            if not ml_service.detector:
                await websocket.send_json({"error": "Models Loading..."})
                await asyncio.sleep(1) # Backoff
                continue

            # Decode frame
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            # Optimization: Use native resolution (do not force upscale)
            # frame = cv2.resize(frame, (640, 480)) 

            # Process every Nth frame
            # Only skip if we are processing faster than input (simple logic for now: process all or skip less)
            # If input is 320x240 (Performance Mode), we can process every frame or every 2nd frame.
            
            # Dynamic Skip: If frame is small, skip less
            height, width = frame.shape[:2]
            CURRENT_SKIP = 0 if width <= 320 else SKIP_FRAMES

            if frame_count % (CURRENT_SKIP + 1) == 0:
                try:
                    # 1. Detect Objects/Poses
                    detection = ml_service.detector.process_frame(frame)
                    
                    # 2. Detect Faces
                    faces = []
                    if ml_service.anonymizer:
                        faces = ml_service.anonymizer.detect_faces(frame)
                    
                    # 3. Calculate Risk
                    risk_score, risk_factors = ml_service.risk_engine.calculate_risk(detection)
                    risk_score = risk_score or 0
                        
                    alert = None
                    if risk_score > 50:
                        alert = ml_service.risk_engine.generate_alert(risk_score, risk_factors)
                        # Ensure level is uppercase for consistency
                        alert['level'] = alert['level'].upper()
                        
                        # SMART STORAGE: Trigger recording for significant threats
                        if risk_score > 70:
                            video_storage_service.start_recording("CAM-01")
                        
                        # PERSISTENCE: Save to DB if Critical and cooldown passed
                        now = datetime.utcnow().timestamp()
                        if alert and (now - last_alert_time > ALERT_COOLDOWN):
                            # Run DB write in thread pool to avoid blocking WS loop
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, save_alert_sync, alert)
                            last_alert_time = now

                    # Always add frame to active recording if any
                    video_storage_service.add_frame("CAM-01", frame)

                    # Update cache
                    cached_result["detection"] = detection
                    cached_result["risk_score"] = risk_score
                    cached_result["alert"] = alert
                    cached_result["faces"] = faces
                
                except Exception as e:
                    print(f"ML Processing Failed: {e}")
                    # Keep valid cache data but maybe reset score?
                    # Using cached is safer to prevent flashing
            else:
                detection = cached_result["detection"]
                risk_score = cached_result["risk_score"]
                alert = cached_result["alert"]
                faces = cached_result["faces"]

            frame_count += 1
            
            # Anonymize frame
            try:
                if ml_service.anonymizer:
                    anon_frame = ml_service.anonymizer.anonymize_frame(
                        frame,
                        poses=detection.get('poses', []),
                        mode='blur',
                        face_rects=faces
                    )
                else:
                    anon_frame = frame
            except Exception:
                anon_frame = frame
            
            # DRAWING: Draw Tracking Overlays
            if detection:
                # Draw Objects
                if 'objects' in detection:
                    for obj in detection['objects']:
                        x1, y1, x2, y2 = map(int, obj['bbox'])
                        track_id = obj.get('track_id', -1)
                        cls_name = obj.get('class', 'obj')
                        
                        # VISUALIZATION FIX: Highlight weapons from standard model
                        is_weapon = cls_name in ['knife', 'baseball bat', 'scissors', 'gun']
                        
                        if is_weapon:
                            color = (0, 0, 255) # Red for weapons
                            thickness = 3
                            label = f"THREAT: {cls_name.upper()}"
                        else:
                            # Standard Object Logic
                            color = (0, 255, 0)
                            thickness = 2
                            label = f"{cls_name} {track_id if track_id!=-1 else ''}"
                            if track_id != -1:
                                np.random.seed(int(track_id))
                                color = np.random.randint(0, 255, size=3).tolist()
                        
                        cv2.rectangle(anon_frame, (x1, y1), (x2, y2), color, thickness)
                        cv2.putText(anon_frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Draw Weapons (NEW)
                if 'weapons' in detection:
                    for weapon in detection['weapons']:
                        x1, y1, x2, y2 = map(int, weapon['bbox'])
                        conf = weapon['confidence']
                        
                        # Use Red for weapons
                        color = (0, 0, 255)
                        cv2.rectangle(anon_frame, (x1, y1), (x2, y2), color, 3)
                        cv2.putText(anon_frame, f"WEAPON {int(conf*100)}%", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Encode frame
            _, buffer = cv2.imencode('.jpg', anon_frame)
            
            # Send results
            try:
                await websocket.send_json({
                    "risk_score": risk_score,
                    "risk_factors": risk_factors, # Added detailed factors
                    "alert": alert,
                    "detections": {
                        "person_count": len(detection.get('poses', [])),
                        "object_count": len(detection.get('objects', [])),
                        "weapon_count": len(detection.get('weapons', []))
                    }
                })
                await websocket.send_bytes(buffer.tobytes())
            except Exception:
                break # Socket likely closed during send

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket Loop Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
