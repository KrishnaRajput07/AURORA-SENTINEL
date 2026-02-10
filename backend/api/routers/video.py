from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import cv2
import numpy as np
from datetime import datetime
import tempfile
import shutil
from backend.services.ml_service import ml_service
from models.scoring.risk_engine import RiskScoringEngine
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
    
    # Initialize a FRESH local engine for this specific forensic analysis
    # Use bypass_calibration=True for forensic analysis to get results immediately
    video_engine = RiskScoringEngine(fps=fps, bypass_calibration=True)
    
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
    
    frame_count, alerts, max_p = 0, [], 0
    motion_patterns_set = set()  # Track unique patterns
    db = SessionLocal()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if frame_count % 6 == 0:
                det = ml_service.detector.process_frame(frame)
                timestamp = frame_count / fps
                risk, facts = video_engine.calculate_risk(det, {
                    'hour': datetime.now().hour,
                    'timestamp': timestamp
                })
                
                # Detect motion patterns
                patterns = video_engine.detect_motion_patterns(det['poses'])
                for pattern in patterns:
                    motion_patterns_set.add(pattern)
                
                for obj in det['objects']:
                    b = obj['bbox']
                    cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 0, 0), 2)
                for p in det['poses']:
                    draw_skeleton(frame, np.array(p['keypoints']), np.array(p['confidence']))
                
                if risk > 20: # Lowered threshold for internal metrics to ensure visibility
                    alt = video_engine.generate_alert(risk, facts)
                    alt['level'] = alt['level'].upper() # Standardize
                    alt['timestamp_seconds'] = frame_count / fps
                    alerts.append(alt)
                max_p = max(max_p, len(det['poses']))
            
            out.write(frame)
            frame_count += 1
    finally:
        cap.release()
        out.release()
        db.close()
    
    # Convert motion patterns set to list
    motion_patterns_list = sorted(list(motion_patterns_set))[:10]  # Top 10 patterns
    if not motion_patterns_list:
        motion_patterns_list = ["No aggressive motion vectors detected"]
    
    return {
        "alerts": alerts,
        "alerts_found": len(alerts),
        "processed_url": f"/archive/download/{out_name}?source=processed",
        "metrics": {
            "max_persons": max_p,
            "suspicious_patterns": motion_patterns_list,
            "fight_probability": max([a['score'] for a in alerts] + [0])
        }
    }

@router.post("/process/video")
async def process_video(file: UploadFile = File(...)):
    try:
        os.makedirs("storage/temp", exist_ok=True)
        # Use a stable path instead of tempfile to avoid handle/permission issues on Windows
        safe_filename = file.filename.replace(" ", "_").replace("(", "").replace(")", "")
        v_path = os.path.abspath(os.path.join("storage", "temp", f"raw_{datetime.now().timestamp()}_{safe_filename}"))
        
        with open(v_path, "wb") as b: 
            content = await file.read()
            b.write(content)
        
        print(f"DEBUG: Processing video at {v_path}")
        results = await process_video_file_task(v_path)
        
        # PERSISTENCE & SMART BIN
        print(f"DEBUG: Alerts found: {results.get('alerts_found', 0)}")
        if results.get("alerts_found", 0) > 0:
            peak_alert = max(results["alerts"], key=lambda x: x['score'])
            print(f"DEBUG: Peak Score detected: {peak_alert['score']}%")
            if peak_alert['score'] >= 30: # Use >= 30 as requested
                try:
                    db = SessionLocal()
                    factors = {
                        'is_forensic': True,
                        'peak_score': peak_alert['score'],
                        'top_factors': peak_alert.get('top_factors', []),
                        'all_detections': results["alerts"],
                        'total_events': len(results["alerts"])
                    }
                    
                    new_alert = Alert(
                        level=peak_alert['level'].upper(),
                        risk_score=float(peak_alert['score']),
                        camera_id="FORENSIC-01",
                        location=f"Forensic: {file.filename}",
                        risk_factors=factors,
                        status="pending",
                        timestamp=datetime.utcnow(),
                        video_clip_path=results["processed_url"]
                    )
                    db.add(new_alert)
                    db.commit()
                    db.refresh(new_alert)
                    db.close()
                    print(f"SUCCESS: Forensic Alert Persisted. ID: {new_alert.id}")
                    
                    # SMART BIN: Move to secure storage
                    bin_dir = os.path.abspath(os.path.join("storage", "bin"))
                    os.makedirs(bin_dir, exist_ok=True)
                    bin_filename = f"threat_{int(datetime.now().timestamp())}_{safe_filename}"
                    bin_path = os.path.join(bin_dir, bin_filename)
                    
                    shutil.copy2(os.path.abspath(v_path), bin_path)
                    print(f"SUCCESS: Archived video to {bin_path}")
                    results["archived_to_bin"] = True
                except Exception as db_err:
                    print(f"CRITICAL ERROR in Forensic Persistence: {db_err}")
        
        # Cleanup temp if not moved to bin
        if os.path.exists(v_path):
            os.remove(v_path)

        return {
            "status": "success", "filename": file.filename,
            "alerts_found": len(results["alerts"]), "alerts": results["alerts"],
            "processed_url": results["processed_url"], "metrics": results["metrics"],
            "archived_to_bin": results.get("archived_to_bin", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
