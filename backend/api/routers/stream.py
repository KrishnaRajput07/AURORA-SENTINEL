from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.ml_service import ml_service
from backend.services.video_storage_service import video_storage_service
from backend.services.clip_capture_service import clip_capture_service
from backend.db.database import SessionLocal
from backend.db.models import Alert, SystemSetting
import cv2
import numpy as np
import asyncio
import base64
from datetime import datetime
import time

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
    SKIP_FRAMES = 1 # Process 1 out of every 2 frames (Increased from 1/3)
    
    # State for deduping alerts (prevent spamming DB)
    last_alert_time = 0
    ALERT_COOLDOWN = 10 # Seconds between persistent alerts
    
    cached_result = {
        "detection": {"poses": [], "objects": []}, 
        "risk_score": 0, 
        "risk_factors": {},
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
                await asyncio.sleep(0.5) # Reduced backoff
                continue

            # Decode frame
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            # Optimization: Use native resolution (do not force upscale)
            # frame = cv2.resize(frame, (640, 480)) 

            # 3. Dynamic Skip: Adaptive based on processing time
            # Process frame and measure duration
            start_proc = time.time()
            
            if frame_count % (SKIP_FRAMES + 1) == 0:
                try:
                    # 1. Detect Objects/Poses/Weapons (Parallelized)
                    detection = ml_service.detector.process_frame(frame)
                    
                    # 2. Detect Faces
                    faces = []
                    if ml_service.anonymizer:
                        # Use YOLO poses for better face detection (uses the robust padding logic)
                        faces = ml_service.anonymizer.detect_faces(frame, poses=detection.get('poses'))
                    
                    # 3. Calculate Risk
                    risk_score, risk_factors = ml_service.risk_engine.calculate_risk(detection)
                    risk_score = risk_score or 0
                    print(f"[DEBUG] risk_score={risk_score:.1f}, weapons={len(detection.get('weapons',[]))}, objects={[o['class'] for o in detection.get('objects',[]) if o['class'] in ['knife','scissors','baseball bat']]}")
                        
                    alert = None
                    if risk_score > 65: # New threshold from previous task
                        alert = ml_service.risk_engine.generate_alert(risk_score, risk_factors)
                        alert['level'] = alert['level'].upper()
                        print(f"[ClipCapture] Risk={risk_score:.1f} > 65, alert generated")
                        
                        now = datetime.utcnow().timestamp()
                        if alert and (now - last_alert_time > ALERT_COOLDOWN):
                            loop = asyncio.get_event_loop()
                            alert_id = await loop.run_in_executor(None, save_alert_sync, alert)
                            last_alert_time = now
                            print(f"[ClipCapture] Alert saved id={alert_id}, score={risk_score:.1f}")

                            if alert_id is not None:
                                capture_ts = datetime.utcnow()
                                async def _delayed_capture(aid, ts, score):
                                    db = SessionLocal()
                                    try:
                                        row = db.query(SystemSetting).filter(
                                            SystemSetting.key == "clip_duration_seconds"
                                        ).first()
                                        total_duration = int(row.value) if row else 10
                                    except Exception:
                                        total_duration = 10
                                    finally:
                                        db.close()
                                    post_seconds = max(1, int(total_duration * 0.3))
                                    await asyncio.sleep(post_seconds)
                                    result = await clip_capture_service.handle_threshold_crossing(
                                        camera_id="CAM-01",
                                        timestamp=ts,
                                        final_score=float(score),
                                        alert_id=aid,
                                    )
                                    if result:
                                        print(f"[ClipCapture] Clip saved: id={result.id} path={result.file_path}")
                                    else:
                                        print(f"[ClipCapture] Clip capture returned None — check smart_bin_enabled and storage/clips/")
                                asyncio.create_task(_delayed_capture(alert_id, capture_ts, risk_score))

                    # Start rolling buffer when risk escalates so footage is ready for clip capture
                    if risk_score > 30:
                        video_storage_service.start_recording("CAM-01")

                    # Always add frame to active recording
                    video_storage_service.add_frame("CAM-01", frame)

                    # Update cache
                    cached_result["detection"] = detection
                    cached_result["risk_score"] = risk_score
                    cached_result["risk_factors"] = risk_factors or {}
                    cached_result["alert"] = alert
                    cached_result["faces"] = faces
                except Exception as e:
                    import traceback
                    print(f"ML Processing Failed: {e}")
                    traceback.print_exc()
            else:
                detection = cached_result["detection"]
                risk_score = cached_result["risk_score"]
                risk_factors = cached_result.get("risk_factors", {})
                alert = cached_result["alert"]
                faces = cached_result["faces"]

            proc_duration = time.time() - start_proc
            # Adapt SKIP_FRAMES: If processing takes > 50ms, skip 1 frame to stay real-time
            if proc_duration > 0.05:
                SKIP_FRAMES = 1
            else:
                SKIP_FRAMES = 0

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
                        sub_cls = weapon.get('sub_class', 'weapon')
                        
                        # Use Red for weapons
                        color = (0, 0, 255)
                        cv2.rectangle(anon_frame, (x1, y1), (x2, y2), color, 3)
                        cv2.putText(anon_frame, f"THREAT: {sub_cls.upper()} {int(conf*100)}%", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Encode frame
            _, buffer = cv2.imencode('.jpg', anon_frame)
            
            # Send results
            try:
                # Only send full metadata every 3 frames to save bandwidth/CPU
                if frame_count % 3 == 0 or alert is not None:
                    active_threats = set()
                    for w in detection.get('weapons', []):
                        active_threats.add(w.get('sub_class', 'weapon'))
                    for o in detection.get('objects', []):
                        cls = o.get('class', '')
                        if cls in ['knife', 'baseball bat', 'scissors', 'gun', 'fire']:
                            active_threats.add(cls)

                    await websocket.send_json({
                        "risk_score": risk_score,
                        "risk_factors": risk_factors,
                        "alert": alert,
                        "detections": {
                            "person_count": len(detection.get('poses', [])),
                            "object_count": len(detection.get('objects', [])),
                            "weapon_count": len(detection.get('weapons', [])),
                            "active_threats": list(active_threats)
                        }
                    })
                # Then the heavy frame data
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
