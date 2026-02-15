import cv2
import os
import sys
import json
import time
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from backend.services.vlm_service import vlm_service

class OfflineProcessor:
    def __init__(self, storage_dir="storage/recordings", metadata_file="storage/metadata.json"):
        self.storage_dir = storage_dir
        self.metadata_file = metadata_file
        self.ensure_metadata_file()

    def ensure_metadata_file(self):
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump([], f)
            print(f"Created metadata registry: {self.metadata_file}")

    def load_metadata(self):
        with open(self.metadata_file, 'r') as f:
            return json.load(f)

    def save_metadata(self, data):
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=4)

    def process_video(self, video_filename):
        video_path = os.path.join(self.storage_dir, video_filename)
        if not os.path.exists(video_path):
            print(f"Error: Video not found {video_path}")
            return

        print(f"Processing video: {video_filename}...")
        
        # Load existing metadata to check if already processed
        metadata_db = self.load_metadata()
        if any(item['filename'] == video_filename for item in metadata_db):
            print(f"Skipping {video_filename} (Already processed)")
            return

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video Info: {duration:.1f}s, {fps}fps")

        # Configuration
        ANALYSIS_INTERVAL = 5 # Analyze every 5 seconds
        frame_step = int(fps * ANALYSIS_INTERVAL)
        
        events = []
        current_frame = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if current_frame % frame_step == 0:
                timestamp = current_frame / fps
                print(f"  Analyzing frame at {timestamp:.1f}s...")
                
                # Convert to PIL/Bytes for VLM
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                
                # Prompt - STRICT JSON & THREAT DETECTION
                # Prompt - ENHANCED FORENSIC ANALYSIS
                # prompt = (
                #     "You are a critical surveillance AI. Analyze this scene for security threats. "
                #     "Describe any fighting, weapons, aggression, or suspicious behavior immediately. "
                #     "Do not use soft language. If people are fighting, say 'Physical Altercation'. "
                #     "If safe, be concise. Focus on: Weapons, Violence, Crowds, Distress."
                #     "Analyze this surveillance frame. Return a valid JSON object only. "
                #     "Format: {\"summary\": \"concise description\", \"threats\": [\"list\", \"of\", \"weapons\", \"or\", \"violence\"], \"severity\": \"low/medium/high\", \"confidence\": 0-100}. "
                #     "Focus strictly on: Guns, Knives, Fighting, Blood, Fire. "
                #     "If safe, severity is 'low'. Do not hallucinate."
                
                prompt = (
                    "You are a forensic video analyst."
                    "You analyze surveillance images for security monitoring."

                    "You are a JSON-only response generator."
                    "Return a single valid JSON object and NOTHING else."
                    "No markdown. No explanations. No extra text."

                    "TASKS:"
                    "1) SUMMARY: Describe in detail what is happening in the scene. Focus on people, posture, actions, interactions, and likely intent."
                    "2) THREATS: Look for: firearms, knives, fire, blood, and active fighting (punching, kicking)."
                    "3) SEVERITY:"
                    "   - high: visible weapon, active violence, fire."
                    "   - medium: aggressive posture, ambiguous object, heated dispute."
                    "   - low: walking, standing, talking, normal behavior."

                    "SCHEMA:"
                    "{"
                    "  \"summary\": \"string\","
                    "  \"threats\": [\"string\"],"
                    "  \"severity\": \"low\" | \"medium\" | \"high\","
                    "  \"confidence\": number (0-100)"
                    "}"
                )


                # Call VLM
                result = vlm_service.analyze_scene(pil_img, prompt)
                
                # Try to parse the result as JSON. If fails, perform fallback.
                
                # Robust JSON Extraction
                raw_text = result.get('description', '{}')
                parsed_data = {}
                
                def extract_json(text):
                    try:
                        # 1. Strip Markdown Code Blocks (```json ... ```)
                        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
                        text = re.sub(r'```\s*', '', text)
                        
                        # 2. Find outermost braces
                        match = re.search(r'\{.*\}', text, re.DOTALL)
                        if match:
                            candidate = match.group(0)
                            
                            # 3. Fix simple trailing commas (common LLM error)
                            candidate = re.sub(r',\s*}', '}', candidate)
                            candidate = re.sub(r',\s*]', ']', candidate)
                            
                            return json.loads(candidate)
                    except:
                        pass
                    return None

                json_obj = extract_json(raw_text)
                
                if json_obj:
                    # Success!
                    parsed_data = {
                        "summary": json_obj.get("summary", "No summary provided"),
                        "threats": json_obj.get("threats", []),
                        "severity": json_obj.get("severity", "low").lower(),
                        "confidence": json_obj.get("confidence", 0)
                    }
                else:
                    # Fallback for plain text or failed parse
                    # If raw_text is really just markdown JSON that failed regex, we might still want to clean it for display
                    clean_text = raw_text.replace('```json', '').replace('```', '').strip()
                    parsed_data = {
                        "summary": clean_text[:200] + "..." if len(clean_text) > 200 else clean_text,
                        "threats": [],
                        "severity": "unknown",
                        "confidence": 0
                    }

                # Save structured data
                event = {
                    "timestamp": round(timestamp, 2),
                    "description": parsed_data.get('summary', raw_text),
                    "threats": parsed_data.get('threats', []),
                    "severity": parsed_data.get('severity', 'low'),
                    "confidence": parsed_data.get('confidence', 0),
                    "provider": vlm_service.provider_name
                }
                
                # Store text for semantic search (combine fields)
                # We store the rich text description for searching, but keep structured data for UI
                events.append(event)
                
                print(f"  [Time: {round(timestamp, 2)}s] {parsed_data.get('summary', 'Processed')[:50]}... | Severity: {parsed_data.get('severity')}")
            
            current_frame += 1
            
        cap.release()
        
        # ---------------------------------------------------------------------
        # AUDIO ANALYSIS (New Phase)
        # ---------------------------------------------------------------------
        from backend.services.audio_service import audio_service
        
        print("  Starting Audio Analysis...")
        audio_events = audio_service.analyze_video(video_path)
        print(f"  Audio Analysis Complete. Found {len(audio_events)} events.")
        
        # Merge Video and Audio Events
        # We just append them. The frontend sorts by timestamp.
        all_events = events + audio_events
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])

        # Save results
        record = {
            "id": f"vid_{int(time.time())}",
            "filename": video_filename,
            "processed_at": datetime.now().isoformat(),
            "events": all_events
        }
        
        metadata_db.append(record)
        self.save_metadata(metadata_db)
        print(f"Finished processing {video_filename}. Metadata saved.")

    def scan_and_process(self):
        print(f"Scanning {self.storage_dir} for new videos...")
        if not os.path.exists(self.storage_dir):
            print(f"Storage directory {self.storage_dir} does not exist.")
            return

        files = [f for f in os.listdir(self.storage_dir) if f.endswith(('.mp4', '.avi', '.mkv'))]
        
        if not files:
            print("No videos found.")
            return

        for video_file in files:
            self.process_video(video_file)

if __name__ == "__main__":
    processor = OfflineProcessor()
    processor.scan_and_process()
