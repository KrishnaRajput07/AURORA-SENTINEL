from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.ml_service import ml_service
from backend.services.video_storage_service import video_storage_service
from backend.services.vlm_service import vlm_service
from backend.db.database import SessionLocal
from backend.db.models import Alert
import cv2
import numpy as np
import asyncio
import base64
from datetime import datetime
import time
from PIL import Image
import sys
import os

# Load config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
try:
    import config
except ImportError:
    config = None

router = APIRouter()

# --- Lightweight change-point detection (independent of ML risk) ---
def _motion_metrics(frame, prev_gray_small, ema_motion: float):
    """
    Returns: (gray_small, diff_mean, ema_motion, is_motion_spike, is_scene_change)
    Uses mean absolute difference on a downscaled grayscale frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_small = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)

    if prev_gray_small is None:
        return gray_small, 0.0, 0.0, False, False

    diff_mean = float(np.mean(cv2.absdiff(gray_small, prev_gray_small)))
    alpha = 0.12
    ema_motion = (1 - alpha) * float(ema_motion) + alpha * diff_mean

    # Dynamic thresholds: adapt to camera noise/lighting changes.
    spike_th = max(10.0, ema_motion * 2.5)
    scene_th = max(22.0, ema_motion * 4.0)
    return gray_small, diff_mean, ema_motion, diff_mean > spike_th, diff_mean > scene_th


# Helper for non-blocking DB write
def save_alert_sync(alert_data):
    try:
        db = SessionLocal()
        new_alert = Alert(
            level=alert_data['level'],
            risk_score=float(alert_data['score']),
            camera_id="CAM-01",
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

@router.websocket("/vlm-feed") # NEW ENDPOINT
async def websocket_vlm_feed(websocket: WebSocket):
    """
    VLM-Enhanced WebSocket endpoint
    Integrates Gemini/Ollama analysis into the loop.
    """
    await websocket.accept()
    print("WebSocket connected (VLM Mode)")
    
    frame_count = 0
    SKIP_FRAMES = 1
    
    # State
    last_alert_time = 0
    ALERT_COOLDOWN = getattr(config, 'ALERT_COOLDOWN_SECONDS', 10) if config else 10
    
    # VLM State
    last_vlm_time = 0
    VLM_INTERVAL = getattr(config, 'VLM_ANALYSIS_INTERVAL', 10) if config else 10
    current_narrative = "Initializing AI Analysis..."
    vlm_task = None

    # Change-point / motion state
    prev_gray_small = None
    ema_motion = 0.0
    last_change_trigger_time = 0.0
    CHANGE_TRIGGER_COOLDOWN = getattr(config, 'CHANGE_TRIGGER_COOLDOWN', 3.0) if config else 3.0
    last_motion_diff = 0.0
    last_scene_change = False
    
    cached_result = {
        "detection": {"poses": [], "objects": []}, 
        "risk_score": 0, 
        "alert": None,
        "faces": []
    }

    try:
        while True:
            try:
                data = await websocket.receive_bytes()
            except Exception:
                break

            if not ml_service.detector:
                await websocket.send_json({"error": "Models Loading..."})
                await asyncio.sleep(0.5)
                continue

            # Decode
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None: continue

            # Initialize from cache so VLM completion logic always has a value.
            risk_score = cached_result.get("risk_score", 0) or 0
            risk_factors = []
            
            start_proc = time.time()

            # Motion/change-point metrics (independent of ML)
            try:
                prev_gray_small, last_motion_diff, ema_motion, is_motion_spike, is_scene_change = _motion_metrics(
                    frame, prev_gray_small, ema_motion
                )
                last_scene_change = bool(is_scene_change)
            except Exception:
                is_motion_spike = False
                is_scene_change = False
            
            if frame_count % (SKIP_FRAMES + 1) == 0:
                try:
                    # 1. Check for completed VLM task (Non-Blocking Check)
                    if vlm_task and vlm_task.done():
                        try:
                            vlm_result = vlm_task.result()
                            print(f"Received VLM Result: {vlm_result.get('description', 'Error')[:50]}...")
                            current_narrative = vlm_result.get("description", "Analysis Failed")
                            
                            # Update risk score if VLM suggested a higher one
                            vlm_suggested_risk = vlm_result.get("risk_score", 0)
                            if vlm_suggested_risk > risk_score:
                                print(f"Escalating risk from {risk_score}% to {vlm_suggested_risk}% based on VLM")
                                risk_score = vlm_suggested_risk
                        except Exception as e:
                            print(f"VLM Task Error: {e}")
                        finally:
                            vlm_task = None # Reset for next run

                    is_vlm_running = (vlm_task is not None)

                    if is_vlm_running:
                        # OPTIMIZATION: System is busy with AI (16s+ load).
                        # Skip heavy YOLO inference to prevent video freeze.
                        # Reuse last known detection.
                        detection = cached_result["detection"]
                        risk_score = cached_result["risk_score"]
                        # Optional: Add visual indicator
                        current_narrative = "AI Thinking... (Video smooth)" 
                    else:
                        # Normal Mode: Run YOLO High FPS
                        detection = ml_service.detector.process_frame(frame)
                        risk_score, risk_factors = ml_service.risk_engine.calculate_risk(detection)
                        risk_score = risk_score or 0
                        
                        # 3. Trigger New VLM Analysis (If idle)
                        now = time.time()
                        _vlm_high_risk_interval = getattr(config, 'VLM_HIGH_RISK_INTERVAL', 3) if config else 3
                        should_trigger = (
                            (risk_score > 60 and (now - last_vlm_time > _vlm_high_risk_interval)) or
                            (now - last_vlm_time > VLM_INTERVAL) or
                            ((is_motion_spike or is_scene_change) and (now - last_change_trigger_time > CHANGE_TRIGGER_COOLDOWN))
                        )
                        
                        if should_trigger:
                            print(f"Triggering VLM Analysis (Interval: {now - last_vlm_time:.1f}s)...")
                            
                            # Prepare args (Copy frame to avoid race conditions)
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(rgb_frame)
                            prompt = (
                                "Analyze this surveillance frame. Focus on aggressive behavior (shoving/punching), "
                                "weapons, and whether this is sport/authorized activity. Be concise. "
                                "If safe, say why it is safe."
                            )
                            risk_for_prompt = max(float(risk_score), 35.0) if (is_motion_spike or is_scene_change) else float(risk_score)
                            
                            # Launch Background Task (Non-Blocking)
                            loop = asyncio.get_event_loop()
                            vlm_task = loop.create_task(
                                loop.run_in_executor(None, vlm_service.analyze_scene, pil_img, prompt, risk_for_prompt)
                            )
                            last_vlm_time = now
                            if is_motion_spike or is_scene_change:
                                last_change_trigger_time = now
                            current_narrative = "Analyzing Scene..." 

                    # Alert Logic
                    alert = None
                    _live_alert_th = getattr(config, 'LIVE_ALERT_THRESHOLD', 65) if config else 65
                    if risk_score > _live_alert_th:
                        alert = ml_service.risk_engine.generate_alert(risk_score, risk_factors if not is_vlm_running else [])
                        alert['level'] = alert['level'].upper()
                        alert['ai_analysis'] = current_narrative
                        
                        _recording_th = getattr(config, 'RECORDING_THRESHOLD', 80) if config else 80
                        if risk_score > _recording_th:
                            video_storage_service.start_recording("CAM-01")
                        
                        now_ts = datetime.utcnow().timestamp()
                        if alert and (now_ts - last_alert_time > ALERT_COOLDOWN):
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, save_alert_sync, alert)
                            last_alert_time = now_ts

                    video_storage_service.add_frame("CAM-01", frame)

                    cached_result.update({
                        "detection": detection,
                        "risk_score": risk_score,
                        "alert": alert
                    })
                except Exception as e:
                    print(f"ML Processing Failed: {e}")
            else:
                detection = cached_result["detection"]
                risk_score = cached_result["risk_score"]
                alert = cached_result["alert"]

            # Adapt Skip
            if time.time() - start_proc > 0.05:
                SKIP_FRAMES = 1
            else:
                SKIP_FRAMES = 0

            frame_count += 1
            
            # Anonymization (Reuse existing logic)
            anon_frame = frame # distinct VLM mode might skip this for raw analysis, but keeping for display
            if ml_service.anonymizer:
                try:
                     anon_frame = ml_service.anonymizer.anonymize_frame(
                        frame, detection.get('poses', []), mode='blur'
                    )
                except: pass

            # Draw Overlays (Simplified for VLM Mode)
            if detection:
                for obj in detection.get('objects', []):
                    x1, y1, x2, y2 = map(int, obj['bbox'])
                    cv2.rectangle(anon_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Encode
            _, buffer = cv2.imencode('.jpg', anon_frame)
            
            # Send Data
            try:
                if frame_count % 3 == 0 or alert:
                    await websocket.send_json({
                        "risk_score": risk_score,
                        "vlm_narrative": current_narrative, # NEW FIELD
                        "alert": alert,
                        "provider": vlm_service.provider_name,
                        "motion_diff": round(float(last_motion_diff or 0), 2),
                        "scene_change": bool(last_scene_change)
                    })
                await websocket.send_bytes(buffer.tobytes())
            except Exception:
                break

    except WebSocketDisconnect:
        print("VLM WebSocket disconnected")
    finally:
        try: await websocket.close()
        except: pass
