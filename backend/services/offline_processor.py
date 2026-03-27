import cv2
import os
import sys
import json
import time
import re
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from backend.services.vlm_service import vlm_service
from backend.services.ml_service import ml_service

# Load config safely
try:
    import config
except Exception:
    config = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_negated(text, keyword, window=6):
    """Return True if `keyword` is preceded by a negation word within `window` words."""
    negations = {'not', 'no', 'never', 'without', "isn't", "aren't", "doesn't",
                 "don't", "neither", "nor", 'non', 'nothing', 'nobody'}
    pattern = r'\b' + re.escape(keyword) + r'\b'
    for m in re.finditer(pattern, text):
        preceding = text[:m.start()].split()[-window:]
        if any(neg in preceding for neg in negations):
            return True
    return False


THREAT_KEYWORDS = {
    "fight": "fight", "fighting": "fight", "brawl": "fight", "assault": "fight",
    "punching": "fight", "hitting": "fight", "attacking": "fight", "violence": "fight",
    "gun": "gun", "firearm": "gun", "pistol": "gun", "rifle": "gun", "shooting": "gun",
    "knife": "knife", "blade": "knife", "stabbing": "knife",
    "fire": "fire", "flames": "fire",
    "boxing": "sport_boxing", "referee": "sport_boxing",
    "sparring": "sport_boxing", "boxing gloves": "sport_boxing",
    "prank": "prank", "staged": "prank", "fake": "prank", "acting": "prank",
}


def extract_threats(description: str):
    """Extract threat tags from description with negation awareness."""
    lower = description.lower()
    threats = []
    for k, v in THREAT_KEYWORDS.items():
        if re.search(r'\b' + re.escape(k) + r'\b', lower):
            if not is_negated(lower, k):
                threats.append(v)
    return list(dict.fromkeys(threats))  # deduplicate preserving order


def extract_risk_from_text(text: str, fallback: int = 0) -> int:
    """
    Try to parse an explicit risk score from VLM output.
    Looks for patterns like 'risk: 75', 'risk score: 75%', 'severity: 80/100'.
    """
    patterns = [
        r'risk[:\s]+(\d{1,3})\s*%?',
        r'risk score[:\s]+(\d{1,3})',
        r'threat level[:\s]+(\d{1,3})',
        r'severity[:\s]+(\d{1,3})',
        r'(\d{1,3})\s*/\s*100',
        r'(\d{1,3})%\s*risk',
    ]
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            val = int(m.group(1))
            if 0 <= val <= 100:
                return val
    return fallback


def build_vlm_prompt(ml_objects: list, ml_weapons: list, prev_description: str = "") -> str:
    """
    Build a structured, context-rich prompt for the VLM.
    Injects ML findings so the VLM can focus on what matters.
    """
    ml_context = ""
    if ml_weapons:
        weapon_names = ", ".join(set(w.get('sub_class', w.get('class', 'weapon')) for w in ml_weapons))
        ml_context += f"ML detector flagged: {weapon_names}. "
    if ml_objects:
        person_count = sum(1 for o in ml_objects if o.get('class') == 'person')
        other = [o.get('class') for o in ml_objects if o.get('class') != 'person']
        if person_count:
            ml_context += f"{person_count} person(s) detected. "
        if other:
            ml_context += f"Other objects: {', '.join(set(other))}. "

    context_note = ""
    if prev_description:
        context_note = f"\nPrevious frame context: {prev_description[:120]}"

    return (
        f"SURVEILLANCE FORENSIC ANALYSIS{context_note}\n"
        f"ML pre-scan: {ml_context or 'no specific flags'}\n\n"
        "Analyze this surveillance frame and answer:\n"
        "1. What is happening? Describe all human interactions in detail.\n"
        "2. Is there any violence, aggression, weapons, or threatening behavior? "
        "Be specific — describe body posture, proximity, and actions.\n"
        "3. Is this organized sport (boxing/sparring with referee/ring/gloves), "
        "a prank/staged scene, or a real threat?\n"
        "4. Provide a RISK SCORE from 0-100 where:\n"
        "   0-20 = safe/normal, 21-40 = minor concern, 41-60 = suspicious,\n"
        "   61-80 = high threat, 81-100 = critical/immediate danger\n"
        "Format your last line as: RISK SCORE: [number]"
    )


def compute_motion_score(frame1, frame2) -> float:
    """Return a 0-1 motion score between two frames using frame difference."""
    if frame1 is None or frame2 is None:
        return 0.0
    g1 = cv2.cvtColor(cv2.resize(frame1, (160, 90)), cv2.COLOR_BGR2GRAY).astype(float)
    g2 = cv2.cvtColor(cv2.resize(frame2, (160, 90)), cv2.COLOR_BGR2GRAY).astype(float)
    diff = np.mean(np.abs(g1 - g2))
    return min(1.0, diff / 50.0)  # normalize: 50 mean diff = full motion


class OfflineProcessor:
    def __init__(self, storage_dir="storage/clips", metadata_file="storage/metadata.json"):
        self.storage_dir = storage_dir
        self.metadata_file = metadata_file
        self.lock = threading.Lock() # NEW: Thread safety lock
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
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

        if not ml_service.detector:
            print(f"ERROR: ML detector not loaded, cannot process {video_filename}")
            return

        print(f"Processing video: {video_filename}...")

        with open(self.metadata_file, 'r') as f:
            quick_db = json.load(f)
            if any(item['filename'] == video_filename for item in quick_db):
                print(f"Skipping {video_filename} (Already in registry)")
                return

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        print(f"Video Info: {duration:.1f}s, {fps}fps, {total_frames} frames")

        # Base sampling: every 2s. During high-motion periods we sample every 1s.
        BASE_INTERVAL = 2.0
        HIGH_MOTION_INTERVAL = 1.0
        HIGH_MOTION_THRESHOLD = 0.25  # motion score above this = high activity

        events = []
        prev_frame = None
        prev_description = ""
        current_frame = 0
        next_sample_frame = 0  # adaptive sampling cursor

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if current_frame >= next_sample_frame:
                timestamp = current_frame / fps

                # --- Motion score vs previous frame ---
                motion = compute_motion_score(prev_frame, frame)
                is_high_motion = motion > HIGH_MOTION_THRESHOLD

                # --- ML fast filter ---
                ml_results = ml_service.detector.process_frame(frame)
                yolo_objects = ml_results.get('objects', [])
                yolo_weapons = ml_results.get('weapons', [])
                yolo_poses = ml_results.get('poses', [])

                has_people = any(o['class'] == 'person' for o in yolo_objects)
                has_weapons = len(yolo_weapons) > 0
                has_poses = len(yolo_poses) >= 2  # 2+ people interacting

                # Trigger VLM when: weapons, 2+ people, high motion, or periodic
                needs_vlm = has_weapons or (has_people and (is_high_motion or has_poses))
                is_periodic = (int(timestamp) % 8 == 0)

                if needs_vlm or is_periodic:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)

                    prompt = build_vlm_prompt(yolo_objects, yolo_weapons, prev_description)
                    ml_risk_hint = 80 if has_weapons else (60 if is_high_motion and has_people else 30)

                    result = vlm_service.analyze_scene(pil_img, prompt, risk_score=ml_risk_hint)
                    description = result.get('description', '').strip()

                    # Parse risk score — prefer explicit score in text over VLM's internal score
                    suggested_risk = extract_risk_from_text(description, fallback=result.get('risk_score', 0))

                    # Boost risk if ML found weapons but VLM underscored
                    if has_weapons and suggested_risk < 60:
                        suggested_risk = max(suggested_risk, 70)
                        print(f"  [BOOST] ML weapon detected, boosting risk to {suggested_risk}")

                    # Boost risk if high motion + 2+ people and VLM underscored
                    if is_high_motion and has_poses and suggested_risk < 40:
                        suggested_risk = max(suggested_risk, 45)

                    detected_threats = extract_threats(description)

                    # Add ML weapon detections as threats even if VLM missed them
                    for w in yolo_weapons:
                        wname = w.get('sub_class', 'weapon')
                        if wname not in detected_threats:
                            detected_threats.append(wname)

                    # Severity determination
                    is_sport = any(t == 'sport_boxing' for t in detected_threats)
                    is_prank = any(t == 'prank' for t in detected_threats)
                    _sport_cap = getattr(config, 'SPORT_RISK_CAP', 15) if config else 15
                    _high_th = getattr(config, 'SEVERITY_HIGH_THRESHOLD', 65) if config else 65
                    _med_th = getattr(config, 'SEVERITY_MEDIUM_THRESHOLD', 35) if config else 35
                    if is_sport or is_prank:
                        severity = "low"
                        suggested_risk = min(suggested_risk, _sport_cap)
                    elif suggested_risk >= _high_th:
                        severity = "high"
                    elif suggested_risk >= _med_th:
                        severity = "medium"
                    else:
                        severity = "low"

                    if len(description) < 40:
                        description = (
                            f"ML detected: {', '.join(set(o['class'] for o in yolo_objects))}. "
                            f"Threats: {', '.join(detected_threats) or 'none'}. "
                            f"Risk: {suggested_risk}%."
                        )

                    prev_description = description

                    event = {
                        "timestamp": round(timestamp, 2),
                        "description": description,
                        "threats": detected_threats,
                        "severity": severity,
                        "risk_score": suggested_risk,
                        "motion_score": round(motion, 2),
                        "provider": result.get("provider", "CORTEX-VLM"),
                        "confidence": round(suggested_risk / 100, 2),
                    }
                    events.append(event)
                    print(f"  [{timestamp:.1f}s] {severity.upper()} | risk={suggested_risk} | motion={motion:.2f} | threats={detected_threats} | {result.get('provider','?')}")

                # Adaptive next sample: high motion → sample faster
                interval = HIGH_MOTION_INTERVAL if is_high_motion else BASE_INTERVAL
                next_sample_frame = current_frame + max(1, int(fps * interval))
                prev_frame = frame.copy()

            current_frame += 1

        cap.release()

        # Audio analysis
        from backend.services.audio_service import audio_service
        print("  Starting Audio Analysis...")
        audio_events = audio_service.analyze_video(video_path)
        print(f"  Audio Analysis Complete. Found {len(audio_events)} events.")

        all_events = events + audio_events
        all_events.sort(key=lambda x: x['timestamp'])

        # Build video summary using LLM with fallback
        video_summary = self._build_video_summary(video_filename, all_events)

        record = {
            "id": f"vid_{int(time.time())}_{video_filename[:8]}",
            "filename": video_filename,
            "processed_at": datetime.now().isoformat(),
            "video_summary": video_summary,
            "events": all_events,
            "summary": {
                "duration": round(duration, 1),
                "max_risk": max((e.get('risk_score', 0) for e in events), default=0),
                "high_severity_count": sum(1 for e in events if e.get('severity') == 'high'),
                "threats_detected": list(set(t for e in events for t in e.get('threats', []))),
            }
        }

        self.add_record_to_metadata(record)
        print(f"Finished processing {video_filename}. Max risk: {record['summary']['max_risk']}%")

        from backend.services.search_service import search_service
        search_service.index_metadata()

    def scan_and_process(self):
        # Scan all storage directories for videos
        scan_dirs = [
            self.storage_dir,
            "storage/recordings",
            "storage/temp",
            "storage/uploads",
        ]
        all_files = []
        for d in scan_dirs:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if f.endswith(('.mp4', '.avi', '.mkv', '.mpeg', '.mov')):
                    all_files.append((d, f))

        if not all_files:
            print("No videos found in any storage directory.")
            return

        print(f"Found {len(all_files)} videos across storage directories.")

        # Ensure models are loaded before processing
        if not ml_service.loaded:
            print("Loading ML models for offline processing...")
            ml_service.load_models()

        if not ml_service.detector:
            print("ERROR: ML models failed to load. Cannot process videos.")
            return

        print(f"ML models ready. Processing {len(all_files)} videos...")

        def process_with_dir(args):
            directory, filename = args
            original_dir = self.storage_dir
            self.storage_dir = directory
            try:
                self.process_video(filename)
            finally:
                self.storage_dir = original_dir

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.map(process_with_dir, all_files)

    def _fallback_video_summary(self, all_events):
        if not all_events:
            return "No events detected in this video."
        top_events = sorted(
            all_events,
            key=lambda e: (
                2 if str(e.get("severity", "")).lower() == "high" else
                1 if str(e.get("severity", "")).lower() == "medium" else 0,
                float(e.get("confidence", 0) or 0),
            ),
            reverse=True,
        )[:3]
        snippets = []
        for evt in top_events:
            ts = round(float(evt.get("timestamp", 0) or 0), 1)
            desc = (evt.get("description", "") or "").strip()
            if desc:
                snippets.append(f"At {ts}s: {desc}")
        if snippets:
            return " ".join(snippets)
        return "Video processed successfully, but no descriptive events were generated."

    def _build_video_summary(self, filename, all_events):
        summary = self._fallback_video_summary(all_events)
        provider = "fallback"
        confidence = 0.6 if all_events else 0.2
        try:
            llm_summary = vlm_service.summarize_events(filename, all_events)
            if llm_summary and llm_summary.get("summary"):
                summary = llm_summary["summary"]
                provider = llm_summary.get("provider", "summary")
                confidence = float(llm_summary.get("confidence", confidence))
        except Exception as e:
            print(f"  [SUMMARY] Fallback summary used due to error: {e}")
        return {
            "text": summary,
            "provider": provider,
            "confidence": round(confidence, 2),
            "generated_at": datetime.now().isoformat(),
        }

# Singleton instance for use in API and background tasks
offline_processor = OfflineProcessor()

if __name__ == "__main__":
    offline_processor.scan_and_process()
