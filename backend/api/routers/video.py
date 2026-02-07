from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import cv2
import numpy as np
from datetime import datetime
import tempfile
from backend.services.ml_service import ml_service
from backend.db.database import SessionLocal
from backend.db.models import Alert

router = APIRouter()

def draw_skeleton(frame, kpts, conf):
    connections = [
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), 
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)
    ]
    for start, end in connections:
        if start < len(conf) and end < len(conf) and conf[start] > 0.4 and conf[end] > 0.4:
            cv2.line(frame, tuple(map(int, kpts[start])), tuple(map(int, kpts[end])), (0, 255, 0), 2)
    for i, (x, y) in enumerate(kpts):
        if i < len(conf) and conf[i] > 0.4:
            cv2.circle(frame, (int(x), int(y)), 3, (0, 0, 255), -1)

async def process_video_file_task(video_path: str):
    if not ml_service.detector:
        return {"error": "Models not loaded", "alerts": [], "processed_url": "", "metrics": {}}

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    out_name = f"proc_{os.path.basename(video_path)}"
    out_dir = os.path.join("storage", "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)
    
    fourcc = cv2.VideoWriter_fourcc(*'H264') # Higher compatibility, fallback to 'avc1' if needed
    if os.name == 'nt':
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not out.isOpened():
        print(f"Warning: Failed to open VideoWriter with fourcc {fourcc}. Falling back to mp4v.")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    
    frame_count, alerts, patterns, max_p = 0, [], [], 0
    db = SessionLocal()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if frame_count % 6 == 0:
                det = ml_service.detector.process_frame(frame)
                risk, facts = ml_service.risk_engine.calculate_risk(det, {'hour': datetime.now().hour})
                
                for obj in det['objects']:
                    b = obj['bbox']
                    cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 0, 0), 2)
                for p in det['poses']:
                    draw_skeleton(frame, np.array(p['keypoints']), np.array(p['confidence']))
                
                if risk > 35:
                    alt = ml_service.risk_engine.generate_alert(risk, facts)
                    alt['timestamp_seconds'] = frame_count / fps
                    alerts.append(alt)
                max_p = max(max_p, len(det['poses']))
            
            out.write(frame)
            frame_count += 1
    finally:
        cap.release()
        out.release()
        db.close()
    
    return {
        "alerts": alerts,
        "processed_url": f"/archive/download/{out_name}?source=processed",
        "metrics": {
            "max_persons": max_p,
            "suspicious_patterns": sorted(list(set([f"Significant risk at {a['timestamp_seconds']:.1f}s" for a in alerts if a['score'] > 60])))[:5],
            "fight_probability": max([a['score'] for a in alerts] + [0])
        }
    }

@router.post("/process/video")
async def process_video(file: UploadFile = File(...)):
    try:
        os.makedirs("storage/temp", exist_ok=True)
        fd, v_path = tempfile.mkstemp(suffix=f"_{file.filename}", dir="storage/temp")
        os.close(fd)
        with open(v_path, "wb") as b: b.write(await file.read())
        
        results = await process_video_file_task(v_path)
        return {
            "status": "success", "filename": file.filename,
            "alerts_found": len(results["alerts"]), "alerts": results["alerts"],
            "processed_url": results["processed_url"], "metrics": results["metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
