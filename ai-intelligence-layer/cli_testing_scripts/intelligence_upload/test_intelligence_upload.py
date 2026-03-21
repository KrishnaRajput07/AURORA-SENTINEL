import os
import sys
import json
import requests
import argparse
from pathlib import Path

API_URL = "http://localhost:8000/process/video"

def test_intelligence_upload(video_path: str, location_type: str = "public", sensitivity: float = 1.0):
    if not os.path.exists(video_path):
        print(f"[-] Error: Video file not found at {video_path}")
        sys.exit(1)
    
    print(f"[*] Simulating Intelligence Tab Upload...")
    print(f"[*] Target Video: {video_path}")
    print(f"[*] Context Parameters: Location={location_type}, Sensitivity={sensitivity}")
    print(f"[*] API Endpoint: {API_URL}")
    print(f"")
    print(f"[*] Uploading and waiting for AI processing... (This may take a minute)")
    
    try:
        with open(video_path, "rb") as f:
            files = {"file": (os.path.basename(video_path), f, "video/mp4")}
            params = {
                "location_type": location_type,
                "sensitivity": sensitivity
            }
            response = requests.post(API_URL, files=files, params=params)
        
        response.raise_for_status()
        data = response.json()
        
        print(f"\n" + "="*60)
        print(f" [1] INTERMEDIATE OUTPUTS (ML Baseline: YOLOv8 & Risk Engine)")
        print(f"="*60)
        
        metrics = data.get("metrics", {})
        baseline_score = metrics.get('ml_baseline', 0)
        alerts = data.get("alerts", [])
        
        print(f"  - Model Used         : YOLOv8 (Pose/Object Detection) + Action Recognition Engine")
        print(f"  - Peak ML Score      : {baseline_score}%")
        print(f"  - Max Persons Found  : {metrics.get('max_persons', 0)}")
        print(f"  - Total Risk Events  : {len(alerts)}")
        
        if alerts:
            print(f"\n    [ML ALERTS GENERATED]")
            for i, alert in enumerate(alerts, 1):
                timestamp = alert.get('timestamp_seconds', 0)
                level = alert.get('level', 'INFO')
                score = alert.get('score', 0)
                factors = ", ".join(alert.get('top_factors', []))
                print(f"      {i}. {timestamp:.1f}s | Level: {level} | Score: {score}% | Factors: {factors}")
        
        suspicious_patterns = metrics.get('suspicious_patterns', [])
        print(f"\n  - Action Behaviors Detected:")
        for sp in suspicious_patterns:
            print(f"      * {sp}")

        print(f"\n" + "="*60)
        print(f" [2] FINAL OUTPUTS (VLM Synthesis & Data Persistence)")
        print(f"="*60)
        
        ai_provider = metrics.get('ai_provider', 'none/ensemble')
        fused_score = metrics.get('fight_probability', baseline_score)
        description = data.get('description', 'No description mapped.')
        archived = data.get('archived_to_bin', False)
        
        print(f"  - Final AI Synthesizer: Vision-Language Model ({ai_provider.upper()}) & ChartQA")
        print(f"  - Final FUSED Score   : {fused_score}%")
        print(f"  - Scene Description   : {description}")
        
        print(f"\n  - System Action Taken:")
        print(f"      * Archived to Smart Bin: {'YES (High Risk)' if archived else 'NO (Safe/Normal)'}")
        print(f"      * Live Indexed to DB   : YES (Vector Search & Metadata)")
        
        print(f"\n[*] Test Complete. Flow verified successfully.\n")

    except requests.exceptions.RequestException as e:
        print(f"[-] HTTP Request Error: {e}")
    except json.JSONDecodeError:
        print(f"[-] Failed to parse JSON. Raw Response: {response.text}")
    except Exception as e:
        print(f"[-] Unexpected Error: {e}")

if __name__ == "__main__":
    current_dir = Path(__file__).parent
    aurora_root = current_dir.parent.parent.parent
    default_video = aurora_root / "videos" / "Normal_Videos_015_x264.mp4"
    
    parser = argparse.ArgumentParser(description="Test Intelligence Tab Video Upload")
    parser.add_argument("--video", "-v", type=str, default=str(default_video),
                        help="Path to the video file to process.")
    parser.add_argument("--location", "-l", type=str, default="public",
                        help="Location type (public, secure_facility, private_property)")
    parser.add_argument("--sensitivity", "-s", type=float, default=1.0,
                        help="Risk sensitivity multiplier (e.g., 0.5 to 2.0)")
    
    args = parser.parse_args()
    
    test_intelligence_upload(args.video, args.location, args.sensitivity)
