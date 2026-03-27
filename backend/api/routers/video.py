from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import cv2
import numpy as np
from datetime import datetime
import tempfile
import shutil
import subprocess
from backend.services.ml_service import ml_service
from models.scoring.risk_engine import RiskScoringEngine
from backend.services.scoring_service import TwoTierScoringService
from backend.services.alert_service import AlertService
from backend.db.database import SessionLocal
from backend.db.models import Alert
from backend.services.offline_processor import offline_processor
from backend.services.search_service import search_service
from PIL import Image

router = APIRouter()

# Initialize services for two-tier scoring
alert_service = AlertService()

# Flag to enable/disable two-tier scoring (can be configured via env var)
ENABLE_TWO_TIER_SCORING = os.getenv("ENABLE_TWO_TIER_SCORING", "true").lower() == "true"

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

async def process_video_file_task(video_path: str, context_params: dict = None):
    # Wait up to 60s for models to finish loading
    if not ml_service.loaded:
        print("[VideoProcess] Models not ready, waiting up to 60s...")
        import asyncio
        for _ in range(30):
            await asyncio.sleep(2)
            if ml_service.loaded:
                break
        if not ml_service.loaded:
            print("[VideoProcess] ERROR: Models failed to load after 60s")
            return {"error": "Models not loaded", "alerts": [], "processed_url": "", "metrics": {}}

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    
    # Initialize a FRESH local engine for this specific forensic analysis
    # Use bypass_calibration=True for forensic analysis to get results immediately
    video_engine = RiskScoringEngine(fps=fps, bypass_calibration=True)
    
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    out_name = f"proc_{os.path.basename(video_path)}"
    out_dir = os.path.abspath(os.getenv("PROCESSED_PATH", "storage/processed"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)

    # Always write frames to a temporary mp4v file first (OpenCV-compatible on all platforms).
    # Then transcode to H.264 + faststart via ffmpeg for browser compatibility.
    # mp4v is NOT playable in browsers; H.264 in an MP4 container is required.
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir=out_dir) as _tmp:
        tmp_raw_path = _tmp.name

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(tmp_raw_path, fourcc, fps, (w, h))

    if not out or not out.isOpened():
        print("CRITICAL: Failed to open VideoWriter with mp4v. Output will be unavailable.")
    
    frame_count, alerts, max_p = 0, [], 0
    motion_patterns_set = set()  # Track unique patterns
    db = SessionLocal()
    vlm_provider = "none"

    # Motion spike capture (fallback when ML misses fights)
    prev_gray_small = None
    best_motion = 0.0
    best_motion_ts = 0.0
    best_motion_frame = None
    
    # Initialize CLAHE for Poor Lighting Compensation (Innovation #14)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    
    # Concurrent Processing Queue (Innovation #7: Parallel Intelligence)
    import queue
    import threading
    
    frame_queue = queue.Queue(maxsize=16)
    results = {"alerts": [], "max_p": 0, "patterns": set()}
    
    def ml_worker():
        while True:
            item = frame_queue.get()
            if item is None: break
            
            f, f_count = item
            try:
                if f_count % 2 == 0:
                    det = ml_service.detector.process_frame(f)
                    ts = f_count / fps
                    # ENHANCED FIGHT DETECTION: Two-Tier Scoring Integration Point
                    # When ENABLE_TWO_TIER_SCORING is true, use TwoTierScoringService
                    # instead of direct risk_engine.calculate_risk()
                    #
                    # Example integration:
                    # if ENABLE_TWO_TIER_SCORING:
                    #     scoring_service = TwoTierScoringService(video_engine, ai_client=None)
                    #     scoring_result = await scoring_service.calculate_scores(
                    #         frame=f, detection_data=det, context=context_params
                    #     )
                    #     risk = scoring_result['final_score']
                    #     facts = scoring_result['ml_factors']
                    #     # Store additional fields: ml_score, ai_score, detection_source, etc.
                    # else:
                    #     risk, facts = video_engine.calculate_risk(det, context_params)
                    
                    risk, facts = video_engine.calculate_risk(det, context_params or {
                        'hour': datetime.now().hour,
                        'timestamp': ts
                    })
                    
                    # Motion Patterns
                    pats = video_engine.detect_motion_patterns(det['poses'])
                    for p in pats: results["patterns"].add(p)
                    
                    # Visual Feedback
                    for obj in det['objects']:
                        b = obj['bbox']
                        cv2.rectangle(f, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 0, 0), 2)
                    
                    if 'weapons' in det:
                        for weapon in det['weapons']:
                            b, c = weapon['bbox'], weapon['confidence']
                            cv2.rectangle(f, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 0, 255), 3)
                            cv2.putText(f, f"WEAPON {int(c*100)}%", (int(b[0]), int(b[1])-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    for p in det['poses']:
                        draw_skeleton(f, np.array(p['keypoints']), np.array(p['confidence']))
                    
                    if risk > 35:
                        alt = video_engine.generate_alert(risk, facts)
                        alt.update({'level': alt['level'].upper(), 'timestamp_seconds': ts})
                        results["alerts"].append(alt)
                    
                    results["max_p"] = max(results["max_p"], len(det['poses']))
                
                out.write(f)
            except Exception as e:
                print(f"Worker Error on frame {f_count}: {e}")
            finally:
                frame_queue.task_done()

    worker_thread = threading.Thread(target=ml_worker, daemon=True)
    worker_thread.start()
    
    try:
        f_count = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # Apply Light Compensation
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b_chan = cv2.split(lab)
            cl = clahe.apply(l)
            frame = cv2.cvtColor(cv2.merge((cl, a, b_chan)), cv2.COLOR_LAB2BGR)
            
            frame_queue.put((frame, f_count))
            f_count += 1
            
        frame_queue.put(None) # Sentinel
        worker_thread.join()
        
        alerts = results["alerts"]
        max_p = results["max_p"]
        for p in results["patterns"]: motion_patterns_set.add(p)
        
    except Exception as e:
        print(f"Main Loop Error: {e}")
    finally:
        cap.release()
        out.release()
        db.close()

    # Transcode the raw mp4v temp file → H.264 + faststart (required for browser playback).
    # mp4v encoded files play on desktop players but show blank in all browsers.
    try:
        ffmpeg = shutil.which("ffmpeg")
        # Fallback for WinGet installation path
        if not ffmpeg:
            winget_path = r"C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
            if os.path.exists(winget_path):
                ffmpeg = winget_path

        if ffmpeg:
            cmd = [
                ffmpeg, "-y",
                "-i", tmp_raw_path,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-preset", "ultrafast",
                out_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                print(f"SUCCESS: Transcoded to H.264 browser-compatible video: {out_path}")
            else:
                # Transcode failed — copy raw mp4v as fallback so file still exists,
                # but log a warning that it won't play in browsers.
                print(f"WARNING: ffmpeg transcode failed (exit {proc.returncode}). "
                      f"Video saved as mp4v — will NOT play in browsers.\nffmpeg stderr: {proc.stderr[-500:]}")
                shutil.copy2(tmp_raw_path, out_path)
        else:
            # ffmpeg not found — copy raw file and warn loudly
            print("WARNING: ffmpeg not found. Video saved as mp4v — will NOT play in browsers. "
                  "Install ffmpeg to enable H.264 encoding.")
            shutil.copy2(tmp_raw_path, out_path)
    except Exception as e:
        print(f"WARNING: ffmpeg transcode error: {e}. Copying raw mp4v file as fallback.")
        shutil.copy2(tmp_raw_path, out_path)
    finally:
        # Always clean up the raw temp file
        try:
            os.unlink(tmp_raw_path)
        except OSError:
            pass
    
    # 1.5 Alert Deduplication (Innovation #27)
    deduped_alerts = []
    if alerts:
        alerts.sort(key=lambda x: x['timestamp_seconds'])
        for a in alerts:
            if not deduped_alerts:
                deduped_alerts.append(a)
                continue
            
            last = deduped_alerts[-1]
            # Merge if within 2 seconds and same level
            if (a['timestamp_seconds'] - last['timestamp_seconds']) < 2.0 and a['level'] == last['level']:
                last['score'] = max(last['score'], a['score'])
                # Update factors if new alert has more
                if len(a.get('top_factors', [])) > len(last.get('top_factors', [])):
                    last['top_factors'] = a['top_factors']
            else:
                deduped_alerts.append(a)
    
    alerts = deduped_alerts

    # Convert motion patterns set to list
    motion_patterns_list = sorted(list(motion_patterns_set))[:10]  # Top 10 patterns
    if not motion_patterns_list:
        motion_patterns_list = ["No aggressive motion vectors detected"]
    
    # 2. VLM SMART PASS (Layered Intelligence)
    # If ML predicts low, AI checks. If ML predicts high, AI verifies context (e.g. Boxing vs Fighting)
    peak_ml_score = max([a['score'] for a in alerts] + [0])
    vlm_fused_score = peak_ml_score
    vlm_forensic_description = "ML Baseline Analysis Complete."

    # Identify the frame with the highest risk for VLM verification
    if alerts:
        peak_alert = max(alerts, key=lambda x: x['score'])
        target_timestamp = peak_alert['timestamp_seconds']
        
        # Seek and capture that frame
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, target_timestamp * 1000)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            from backend.services.vlm_service import vlm_service
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            
            print(f"  [CORTEX ENSEMBLE] Verifying peak ML risk ({peak_ml_score}%) via Concurrent AI...")
            # Pass the reason (facts) to the VLM for causal analysis
            top_factors = peak_alert.get('top_factors', [])
            
            # Innovation #33: Struct-Before-ML (Priority VQA)
            if vlm_service.chartqa.available:
                print(f"  [CORTEX STRUCT] Running ChartQA on peak frame...")
                struct_res = vlm_service.chartqa.analyze(pil_img, "What is the primary activity in this security footage?")
                if struct_res and "Error" not in struct_res:
                    vlm_forensic_description = f"STRUCTURAL ANALYST: {struct_res}. "
            
            vlm_res = vlm_service.analyze_scene(pil_img, risk_score=top_factors)
            vlm_fused_score = vlm_res.get('risk_score', peak_ml_score)
            vlm_forensic_description += vlm_res.get('description', 'AI Synthesis Complete.')
            vlm_provider = vlm_res.get('provider', 'ensemble')
    else:
        # Fallback: if ML produced no alerts, still verify the most "active" moment.
        if best_motion_frame is not None:
            try:
                from backend.services.vlm_service import vlm_service
                rgb_frame = cv2.cvtColor(best_motion_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                print(f"  [CORTEX ENSEMBLE] ML produced no alerts. Verifying motion-spike frame at {best_motion_ts:.1f}s...")
                vlm_res = vlm_service.analyze_scene(
                    pil_img,
                    prompt="Analyze this surveillance frame. Focus on fights, shoving, punching, or weapons. If safe, say why.",
                    risk_score=35,
                )
                vlm_fused_score = vlm_res.get('risk_score', 0)
                vlm_forensic_description = vlm_res.get('description', 'AI Synthesis Complete.')
                vlm_provider = vlm_res.get('provider', 'ensemble')
            except Exception as e:
                print(f"  [CORTEX] Motion-spike VLM verification failed: {e}")

    return {
        "alerts": alerts,
        "alerts_found": len(alerts),
        "processed_url": f"/archive/download/{out_name}?source=processed",
        "description": vlm_forensic_description, # Full AI Intelligence Synthesis
        "metrics": {
            "max_persons": max_p,
            "suspicious_patterns": motion_patterns_list,
            "fight_probability": vlm_fused_score, # FUSED SCORE FROM ENSEMBLE
            "ml_baseline": peak_ml_score,
            "ai_provider": vlm_provider,
            "is_blurry": any(a.get('is_blurry') for a in alerts),
            "motion_spike": round(best_motion, 2),
            "motion_spike_ts": round(best_motion_ts, 2)
        }
    }

@router.post("/process/video")
async def process_video(
    file: UploadFile = File(...),
    location_type: str = "public",
    sensitivity: float = 1.0,
    hour: int = None
):
    try:
        temp_dir = os.getenv("TEMP_PATH", "storage/temp")
        os.makedirs(temp_dir, exist_ok=True)
        # Use a stable path instead of tempfile to avoid handle/permission issues on Windows
        safe_filename = file.filename.replace(" ", "_").replace("(", "").replace(")", "")
        v_path = os.path.abspath(os.path.join(temp_dir, f"raw_{datetime.now().timestamp()}_{safe_filename}"))
        
        with open(v_path, "wb") as b: 
            content = await file.read()
            b.write(content)
        
        print(f"DEBUG: Processing video at {v_path} with context: {location_type}, {sensitivity}, {hour}")
        results = await process_video_file_task(v_path, {
            'location_type': location_type,
            'sensitivity': sensitivity,
            'hour': hour if hour is not None else datetime.now().hour
        })
        
        # PERSISTENCE & SMART BIN
        print(f"DEBUG: Alerts found: {results.get('alerts_found', 0)}")
        if results.get("alerts_found", 0) > 0:
            peak_alert = max(results["alerts"], key=lambda x: x['score'])
            print(f"DEBUG: Peak Score detected: {peak_alert['score']}%")
            if peak_alert['score'] >= 45: # Increased from 30 to reduce sensitivity
                db = SessionLocal()
                try:
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
                    print(f"SUCCESS: Forensic Alert Persisted. ID: {new_alert.id}")
                    
                    # SMART BIN: Move to secure storage
                    bin_dir = os.path.abspath(os.getenv("BIN_PATH", "storage/bin"))
                    os.makedirs(bin_dir, exist_ok=True)
                    bin_filename = f"threat_{int(datetime.now().timestamp())}_{safe_filename}"
                    bin_path = os.path.join(bin_dir, bin_filename)
                    
                    shutil.copy2(os.path.abspath(v_path), bin_path)
                    print(f"SUCCESS: Archived video to {bin_path}")
                    results["archived_to_bin"] = True
                except Exception as db_err:
                    print(f"CRITICAL ERROR in Forensic Persistence: {db_err}")
                finally:
                    db.close()

        # LIVE INDEXING (Innovation #12/28): Add to metadata.json and Vector DB immediately
        try:
            # Create a professional metadata record for this forensic event
            metadata_record = {
                "id": f"vid_{int(datetime.now().timestamp())}_{safe_filename[:10]}",
                "filename": file.filename,
                "processed_at": datetime.now().isoformat(),
                "events": [
                    {
                        "timestamp": 0.0, # Brief summary at start of clip
                        "description": results.get("description", "No detailed description available."),
                        "threats": results.get("metrics", {}).get("suspicious_patterns", []),
                        "severity": "high" if results.get("metrics", {}).get("fight_probability", 0) > 60 else "medium" if results.get("metrics", {}).get("fight_probability", 0) > 30 else "low",
                        "provider": results.get("metrics", {}).get("ai_provider", "ensemble"),
                        "confidence": results.get("metrics", {}).get("fight_probability", 0) / 100
                    }
                ]
            }
            # Also add sub-alerts as events
            for alert in results.get("alerts", []):
                metadata_record["events"].append({
                    "timestamp": round(alert["timestamp_seconds"], 2),
                    "description": f"Risk Event: {alert['level']} (Factors: {', '.join(alert.get('top_factors', []))})",
                    "threats": alert.get("top_factors", []),
                    "severity": alert["level"].lower(),
                    "provider": "ml-engine",
                    "confidence": alert["score"] / 100
                })

            offline_processor.add_record_to_metadata(metadata_record)
            search_service.upsert_record(metadata_record) # Efficient incremental indexing
            print(f"SUCCESS: Live Indexing complete for {file.filename}")
        except Exception as index_err:
            print(f"Warning: Failed to live index {file.filename}: {index_err}")
        
        # Cleanup temp if not moved to bin
        if os.path.exists(v_path):
            os.remove(v_path)

        return {
            "status": "success", "filename": file.filename,
            "alerts_found": len(results["alerts"]), "alerts": results["alerts"],
            "processed_url": results["processed_url"], "metrics": results["metrics"],
            "description": results.get("description", "Analysis Synthesized."), # FIX: Missing Description
            "archived_to_bin": results.get("archived_to_bin", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
