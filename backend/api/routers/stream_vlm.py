import asyncio
import json
import os
import sys
import time
from collections import deque
from datetime import datetime

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from PIL import Image

from backend.db.database import SessionLocal
from backend.db.models import Alert
from backend.services.alert_service import AlertService
from backend.services.ml_service import ml_service
from backend.services.scoring_service import TwoTierScoringService
from backend.services.system_settings_service import (
    get_vlm_interval_seconds,
    set_vlm_interval_seconds,
)
from backend.services.video_storage_service import video_storage_service
from backend.services.vlm_service import vlm_service

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
try:
    import config
except Exception:
    config = None

router = APIRouter()


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

    spike_th = max(10.0, ema_motion * 2.5)
    scene_th = max(22.0, ema_motion * 4.0)
    return gray_small, diff_mean, ema_motion, diff_mean > spike_th, diff_mean > scene_th


def _infer_scene_type_from_text(text: str) -> str:
    lower = (text or "").lower()
    if any(k in lower for k in ["boxing", "sparring", "referee"]):
        return "organized_sport"
    if any(k in lower for k in ["fight", "punch", "assault", "brawl"]):
        return "real_fight"
    if any(k in lower for k in ["suspicious", "crowd", "covering face"]):
        return "suspicious"
    return "normal"


def save_alert_sync(alert_data):
    try:
        db = SessionLocal()
        risk_score = float(alert_data.get("risk_score", alert_data.get("score", 0.0)))
        new_alert = Alert(
            level=str(alert_data.get("level", "HIGH")).upper(),
            risk_score=risk_score,
            camera_id=alert_data.get("camera_id", "CAM-01"),
            location=alert_data.get("location", "Main Feed"),
            risk_factors=alert_data.get("risk_factors", alert_data.get("top_factors", [])),
            status=alert_data.get("status", "pending"),
            timestamp=alert_data.get("timestamp", datetime.utcnow()),
            ml_score=float(alert_data.get("ml_score", 0.0) or 0.0),
            ai_score=float(alert_data.get("ai_score", 0.0) or 0.0),
            final_score=float(alert_data.get("final_score", risk_score) or risk_score),
            detection_source=alert_data.get("detection_source"),
            ai_explanation=alert_data.get("ai_explanation") or alert_data.get("ai_analysis"),
            ai_scene_type=alert_data.get("ai_scene_type"),
            ai_confidence=float(alert_data.get("ai_confidence", 0.0) or 0.0),
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        db.close()
        return new_alert.id
    except Exception as e:
        print(f"DB Write Error: {e}")
        return None


@router.websocket("/vlm-feed")
async def websocket_vlm_feed(websocket: WebSocket):
    """
    VLM-enhanced WebSocket endpoint.
    - rolling VLM narrative context
    - two-tier score aggregation in live loop
    - persisted VLM interval runtime control
    """
    await websocket.accept()
    print("WebSocket connected (VLM Mode)")

    frame_count = 0
    skip_frames = 1

    alert_cooldown = getattr(config, "ALERT_COOLDOWN_SECONDS", 10) if config else 10
    last_alert_time = 0.0

    default_vlm_interval = getattr(config, "VLM_ANALYSIS_INTERVAL", 10) if config else 10
    vlm_interval = get_vlm_interval_seconds(default_value=default_vlm_interval)
    vlm_high_risk_interval = getattr(config, "VLM_HIGH_RISK_INTERVAL", 3) if config else 3
    change_trigger_cooldown = getattr(config, "CHANGE_TRIGGER_COOLDOWN", 3.0) if config else 3.0
    context_window = getattr(config, "LIVE_VLM_CONTEXT_WINDOW", 4) if config else 4
    interval_min = getattr(config, "VLM_INTERVAL_MIN_SECONDS", 2) if config else 2
    interval_max = getattr(config, "VLM_INTERVAL_MAX_SECONDS", 30) if config else 30

    last_vlm_time = 0.0
    last_change_trigger_time = 0.0
    current_narrative = "Initializing AI Analysis..."
    narrative_history = deque(maxlen=max(1, int(context_window)))
    vlm_task = None

    prev_gray_small = None
    ema_motion = 0.0
    last_motion_diff = 0.0
    last_scene_change = False

    two_tier_service = TwoTierScoringService(ml_service.risk_engine, ai_client=None)
    alert_service = AlertService()
    latest_scoring_result = None
    latest_ml_score = 0.0
    latest_ml_factors = {}

    cached_result = {
        "detection": {"poses": [], "objects": [], "weapons": []},
        "risk_score": 0.0,
        "risk_factors": {},
        "alert": None,
    }

    try:
        while True:
            try:
                packet = await websocket.receive()
            except Exception:
                break

            if packet.get("type") == "websocket.disconnect":
                break

            # Runtime control message path.
            if packet.get("text") is not None:
                try:
                    payload = json.loads(packet["text"])
                    if payload.get("type") == "set_vlm_interval":
                        requested = int(payload.get("seconds", vlm_interval))
                        if interval_min <= requested <= interval_max:
                            vlm_interval = set_vlm_interval_seconds(requested)
                            await websocket.send_json(
                                {
                                    "type": "config_ack",
                                    "vlm_interval_seconds": int(vlm_interval),
                                }
                            )
                        else:
                            await websocket.send_json(
                                {
                                    "type": "config_error",
                                    "message": f"seconds must be between {interval_min} and {interval_max}",
                                }
                            )
                except Exception as e:
                    print(f"[VLM] Control message parse error: {e}")
                continue

            data = packet.get("bytes")
            if data is None:
                continue

            if not ml_service.detector:
                if ml_service.load_error:
                    await websocket.send_json({"error": f"Model load failed: {ml_service.load_error}"})
                else:
                    await websocket.send_json({"error": "Models Loading..."})
                await asyncio.sleep(0.5)
                continue

            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            risk_score = float(cached_result.get("risk_score", 0.0) or 0.0)
            risk_factors = dict(cached_result.get("risk_factors", {}) or {})
            alert = cached_result.get("alert")
            detection = cached_result.get("detection", {"poses": [], "objects": [], "weapons": []})

            start_proc = time.time()

            try:
                prev_gray_small, last_motion_diff, ema_motion, is_motion_spike, is_scene_change = _motion_metrics(
                    frame, prev_gray_small, ema_motion
                )
                last_scene_change = bool(is_scene_change)
            except Exception:
                is_motion_spike = False
                is_scene_change = False

            if frame_count % (skip_frames + 1) == 0:
                try:
                    # Consume completed VLM task.
                    if vlm_task and vlm_task.done():
                        try:
                            vlm_result = vlm_task.result()
                            current_narrative = vlm_result.get("description", "Analysis Failed")
                            narrative_history.append(
                                {
                                    "timestamp": time.time(),
                                    "narrative": current_narrative,
                                    "risk_score": float(vlm_result.get("risk_score", 0) or 0),
                                }
                            )

                            ai_score = float(vlm_result.get("risk_score", 0) or 0)
                            ai_scene_type = vlm_result.get("scene_type") or _infer_scene_type_from_text(
                                current_narrative
                            )
                            ai_confidence = min(1.0, max(0.0, ai_score / 100.0))
                            latest_scoring_result = two_tier_service.aggregate_existing_scores(
                                ml_score=latest_ml_score,
                                ml_factors=latest_ml_factors,
                                ai_score=ai_score,
                                ai_explanation=current_narrative,
                                ai_scene_type=ai_scene_type,
                                ai_confidence=ai_confidence,
                                ai_provider=vlm_result.get("provider", "vlm"),
                                nemotron_verification=vlm_result.get("nemotron_verification"),
                            )
                            risk_score = float(latest_scoring_result.get("final_score", risk_score))
                            risk_factors = latest_scoring_result.get("ml_factors", risk_factors)
                        except Exception as e:
                            print(f"VLM Task Error: {e}")
                        finally:
                            vlm_task = None

                    is_vlm_running = vlm_task is not None

                    if is_vlm_running:
                        detection = cached_result["detection"]
                        risk_score = float(cached_result["risk_score"] or 0.0)
                        risk_factors = cached_result.get("risk_factors", {}) or {}
                        current_narrative = "AI Thinking... (Video smooth)"
                    else:
                        detection = ml_service.detector.process_frame(frame)
                        latest_ml_score, latest_ml_factors = ml_service.risk_engine.calculate_risk(detection)
                        latest_ml_score = float(latest_ml_score or 0.0)
                        latest_ml_factors = latest_ml_factors or {}

                        latest_scoring_result = two_tier_service.aggregate_existing_scores(
                            ml_score=latest_ml_score,
                            ml_factors=latest_ml_factors,
                            ai_score=None,
                            ai_explanation="",
                            ai_scene_type="normal",
                            ai_confidence=0.0,
                            ai_provider="none",
                            nemotron_verification=None,
                        )
                        risk_score = float(latest_scoring_result.get("final_score", latest_ml_score))
                        risk_factors = latest_scoring_result.get("ml_factors", latest_ml_factors)

                        now = time.time()
                        should_trigger = (
                            (risk_score > 60 and (now - last_vlm_time > vlm_high_risk_interval))
                            or (now - last_vlm_time > vlm_interval)
                            or (
                                (is_motion_spike or is_scene_change)
                                and (now - last_change_trigger_time > change_trigger_cooldown)
                            )
                        )

                        if should_trigger:
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(rgb_frame)
                            context_lines = []
                            for entry in list(narrative_history):
                                context_lines.append(
                                    f"- Prior ({round(float(entry.get('risk_score', 0)), 1)}%): {entry.get('narrative', '')}"
                                )
                            context_block = "\n".join(context_lines[: context_window])
                            prompt = (
                                "Analyze this surveillance frame. Focus on aggressive behavior, weapons, and "
                                "whether activity appears organized sport.\n"
                            )
                            if context_block:
                                prompt += f"Recent scene history:\n{context_block}\n"
                            prompt += "Be concise and include whether risk is escalating or de-escalating."

                            risk_for_prompt = max(float(risk_score), 35.0) if (is_motion_spike or is_scene_change) else float(risk_score)
                            loop = asyncio.get_event_loop()
                            vlm_task = loop.create_task(
                                loop.run_in_executor(None, vlm_service.analyze_scene, pil_img, prompt, risk_for_prompt)
                            )
                            last_vlm_time = now
                            if is_motion_spike or is_scene_change:
                                last_change_trigger_time = now
                            current_narrative = "Analyzing Scene..."

                    alert = None
                    live_alert_th = getattr(config, "LIVE_ALERT_THRESHOLD", 65) if config else 65
                    if risk_score > live_alert_th:
                        if latest_scoring_result:
                            alert = alert_service.generate_alert(
                                latest_scoring_result,
                                {
                                    "camera_id": "CAM-01",
                                    "location": "Main Feed",
                                    "timestamp": datetime.utcnow(),
                                },
                            )
                            alert["level"] = str(alert["level"]).upper()
                            alert["ai_analysis"] = current_narrative
                        else:
                            alert = ml_service.risk_engine.generate_alert(risk_score, risk_factors)
                            alert["level"] = str(alert["level"]).upper()
                            alert["ai_analysis"] = current_narrative

                        recording_th = getattr(config, "RECORDING_THRESHOLD", 80) if config else 80
                        if risk_score > recording_th:
                            video_storage_service.start_recording("CAM-01")

                        now_ts = datetime.utcnow().timestamp()
                        if alert and (now_ts - last_alert_time > alert_cooldown):
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, save_alert_sync, alert)
                            last_alert_time = now_ts

                    video_storage_service.add_frame("CAM-01", frame)

                    cached_result.update(
                        {
                            "detection": detection,
                            "risk_score": risk_score,
                            "risk_factors": risk_factors or {},
                            "alert": alert,
                        }
                    )
                except Exception as e:
                    print(f"ML Processing Failed: {e}")
            else:
                detection = cached_result["detection"]
                risk_score = float(cached_result["risk_score"] or 0.0)
                risk_factors = cached_result.get("risk_factors", {}) or {}
                alert = cached_result["alert"]

            if time.time() - start_proc > 0.05:
                skip_frames = 1
            else:
                skip_frames = 0

            frame_count += 1

            anon_frame = frame
            if ml_service.anonymizer:
                try:
                    anon_frame = ml_service.anonymizer.anonymize_frame(
                        frame, detection.get("poses", []), mode="blur"
                    )
                except Exception:
                    pass

            if detection:
                for obj in detection.get("objects", []):
                    x1, y1, x2, y2 = map(int, obj["bbox"])
                    cv2.rectangle(anon_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            _, buffer = cv2.imencode(".jpg", anon_frame)

            try:
                if frame_count % 3 == 0 or alert:
                    active_threats = set()
                    for w in detection.get("weapons", []):
                        active_threats.add(w.get("sub_class", "weapon"))
                    for f in detection.get("fire", []):
                        active_threats.add(f.get("class", "fire"))
                    for o in detection.get("objects", []):
                        cls = o.get("class", "")
                        if cls in ["knife", "baseball bat", "scissors", "gun", "fire"]:
                            active_threats.add(cls)
                    await websocket.send_json(
                        {
                            "risk_score": risk_score,
                            "risk_factors": risk_factors,
                            "vlm_narrative": current_narrative,
                            "alert": alert,
                            "provider": vlm_service.provider_name,
                            "motion_diff": round(float(last_motion_diff or 0), 2),
                            "scene_change": bool(last_scene_change),
                            "vlm_interval_seconds": int(vlm_interval),
                            "ml_score": (latest_scoring_result or {}).get("ml_score", latest_ml_score),
                            "ai_score": (latest_scoring_result or {}).get("ai_score", 0.0),
                            "final_score": (latest_scoring_result or {}).get("final_score", risk_score),
                            "detections": {
                                "person_count": len(detection.get("poses", [])),
                                "object_count": len(detection.get("objects", [])),
                                "weapon_count": len(detection.get("weapons", [])),
                                "fire_count": len(detection.get("fire", [])),
                                "active_threats": list(active_threats),
                            },
                        }
                    )
                await websocket.send_bytes(buffer.tobytes())
            except Exception:
                break

    except WebSocketDisconnect:
        print("VLM WebSocket disconnected")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
