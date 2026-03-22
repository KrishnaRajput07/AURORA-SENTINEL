import cv2
import os
import sys
import json
import time
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from backend.services.vlm_service import vlm_service
from backend.services.ml_service import ml_service

class OfflineProcessor:
    def __init__(self, storage_dir="storage/clips", metadata_file="storage/metadata.json"):
        self.storage_dir = storage_dir
        self.metadata_file = metadata_file
        self.lock = threading.Lock() # NEW: Thread safety lock
        self.ensure_metadata_file()

    def ensure_metadata_file(self):
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump([], f)
            print(f"Created metadata registry: {self.metadata_file}")

    def load_metadata(self):
        with open(self.metadata_file, 'r') as f:
            return json.load(f)

    def add_record_to_metadata(self, record):
        """Atomic Load -> Append -> Save operation to prevent race conditions."""
        with self.lock:
            metadata_db = self.load_metadata()
            # Avoid duplicate filenames
            if not any(item['filename'] == record['filename'] for item in metadata_db):
                metadata_db.append(record)
                with open(self.metadata_file, 'w') as f:
                    json.dump(metadata_db, f, indent=4)
                print(f"  [METADATA] Successfully registered {record['filename']}")
            else:
                print(f"  [METADATA] {record['filename']} already in registry, skipping save.")

    def process_video(self, video_filename):
        video_path = os.path.join(self.storage_dir, video_filename)
        if not os.path.exists(video_path):
            print(f"Error: Video not found {video_path}")
            return

        print(f"Processing video: {video_filename}...")
        
        # Quick check without lock for skipping
        with open(self.metadata_file, 'r') as f:
            quick_db = json.load(f)
            if any(item['filename'] == video_filename for item in quick_db):
                print(f"Skipping {video_filename} (Already in registry)")
                return

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video Info: {duration:.1f}s, {fps}fps")
        # ml_service.load_models() # MOVED to scan_and_process
        
        # Configuration
        ANALYSIS_INTERVAL = 2 # Check ML every 2 seconds
        frame_step = int(fps * ANALYSIS_INTERVAL)
        
        events = []
        current_frame = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if current_frame % frame_step == 0:
                timestamp = current_frame / fps
                
                # 1. FAST FILTER (YOLO on Hardware)
                ml_results = ml_service.detector.process_frame(frame)
                
                yolo_objects = ml_results.get('objects', [])
                yolo_weapons = ml_results.get('weapons', [])
                
                # Logic: Trigger VLM if:
                # 1. YOLO sees high-risk items (weapons)
                # 2. YOLO sees people (validation check to ensure no hidden actions)
                # 3. Periodic health check every 6 seconds (regardless of ML)
                has_people = any(obj['class'] == 'person' for obj in yolo_objects)
                needs_vlm = len(yolo_weapons) > 0 or has_people
                is_periodic = (int(timestamp) % 6 == 0) # Higher frequency periodic check
                
                if needs_vlm or is_periodic:
                    print(f"  [BRAIN] Forensic validation at {timestamp:.1f}s (ML Score: {'High' if len(yolo_weapons) > 0 else '0% - Sanity Check'})...")
                    # Convert to PIL/Bytes for VLM
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    
                    prompt = (
                        "SURVEILLANCE ANALYSIS: Provide a high-fidelity description of all human activities. "
                        "Identify ANY signs of aggression, grappling, chasing, or weapons. "
                        "If you see boxing/sparring, mention it specifically. "
                        "Be extremely detailed about the interaction logic between subjects."
                    )
                    
                    result = vlm_service.analyze_scene(pil_img, prompt, risk_score=70 if needs_vlm else 20)
                    description = result.get('description', '').strip()
                    suggested_risk = result.get('risk_score', 0)

                    # Metadata extraction
                    detected_threats = []
                    severity = "low"
                    lower_desc = description.lower()
                    
                    import re
                    threat_keywords = {
                        "fight": "fight", "gun": "gun", "knife": "knife", "fire": "fire",
                        "boxing": "sport_boxing", "referee": "sport_boxing", "sparring": "sport_boxing"
                    }
                    for k, v in threat_keywords.items():
                        if re.search(r'\b' + re.escape(k) + r'\b', lower_desc):
                            detected_threats.append(v)

                    if any(x in ["sport_boxing"] for x in detected_threats):
                        severity = "low"
                        suggested_risk = min(suggested_risk, 15)
                    elif suggested_risk >= 65: severity = "high"
                    elif suggested_risk >= 35: severity = "medium"

                    # Enrich description with ML findings if VLM is too generic
                    if len(description) < 40:
                        description = f"Detected {', '.join(detected_threats) if detected_threats else 'activity'} with risk factor {suggested_risk}%."

                    event = {
                        "timestamp": round(timestamp, 2),
                        "description": description,
                        "threats": detected_threats + ml_results.get('patterns', []),
                        "severity": severity,
                        "provider": result.get("provider", "CORTEX-VLM"),
                        "confidence": round(result.get('risk_score', 0) / 100, 2)
                    }
                    events.append(event)
                    print(f"  [Time: {round(timestamp, 2)}s] {severity.upper()} detected via {result.get('provider')}")
                
            current_frame += 1
            
        cap.release()
        
        # 2. AUDIO ANALYSIS
        from backend.services.audio_service import audio_service
        print("  Starting Audio Analysis...")
        audio_events = audio_service.analyze_video(video_path)
        print(f"  Audio Analysis Complete. Found {len(audio_events)} events.")
        
        all_events = events + audio_events
        all_events.sort(key=lambda x: x['timestamp'])

        # Save results atomically
        record = {
            "id": f"vid_{int(time.time())}_{video_filename[:8]}",
            "filename": video_filename,
            "processed_at": datetime.now().isoformat(),
            "events": all_events
        }
        
        self.add_record_to_metadata(record)
        print(f"Finished processing {video_filename}.")
        
        # Index into Vector DB
        from backend.services.search_service import search_service
        search_service.index_metadata()

    def scan_and_process(self):
        print(f"Scanning {self.storage_dir} for new videos...")
        if not os.path.exists(self.storage_dir): return
        files = [f for f in os.listdir(self.storage_dir) if f.endswith(('.mp4', '.avi', '.mkv'))]
        if not files:
            print("No videos found.")
            return

        print(f"Starting parallel processing with 4 workers for {len(files)} videos...")
        ml_service.load_models() # Load once per scan
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(self.process_video, files)

# Singleton instance for use in API and background tasks
offline_processor = OfflineProcessor()

if __name__ == "__main__":
    offline_processor.scan_and_process()
