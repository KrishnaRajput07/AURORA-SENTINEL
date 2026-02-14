import os
import torch
import numpy as np
from moviepy import VideoFileClip
from transformers import pipeline
import gc

class AudioService:
    def __init__(self, model_name="MIT/ast-finetuned-audioset-10-10-0.4593"):
        self.model_name = model_name
        self.pipeline = None
        # Critical sounds we care about
        # AudioSet labels are specific. We map them to user-friendly terms.
        self.target_labels = {
            "Gunshot, gunfire": "Gunshot",
            "Explosion": "Explosion",
            "Screaming": "Screaming",
            "Glass": "Glass Breaking",
            "Shatter": "Glass Breaking",
            "Yell": "Shouting",
            "Shout": "Shouting",
            "Aggressive": "Aggression"
        }
        print("Audio Service Initialized (Lazy Loading).")

    def load_model(self):
        """Loads model into RAM only when needed."""
        if self.pipeline is None:
            print(f"Loading Audio Model: {self.model_name}...")
            self.pipeline = pipeline(
                "audio-classification", 
                model=self.model_name, 
                device="cpu" # Force CPU to save GPU for NVR
            )

    def unload_model(self):
        """Frees RAM immediately."""
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
            gc.collect()
            print("Audio Model Unloaded.")

    def analyze_video(self, video_path):
        """
        Extracts audio from video and analyzes it for target sounds.
        Returns a list of detected events with timestamps.
        """
        if not os.path.exists(video_path):
            return []

        events = []
        temp_audio = "temp_audio.wav"
        
        try:
            # 1. Extract Audio
            video = VideoFileClip(video_path)
            if video.audio is None:
                print("No audio track found.")
                video.close()
                return []
                
            duration = video.duration
            video.audio.write_audiofile(temp_audio, logger=None)
            video.close()
            
            # 2. Load Model
            self.load_model()
            
            # 3. Analyze in Chunks (Smart Splitting)
            # AST expects specific input, but pipeline handles raw audio files well.
            # We'll rely on the pipeline's sliding window if available, or manual chunking.
            # For simplicity and memory, we use the pipeline on the whole file 
            # but usually it truncates. Let's use a sliding window approach manually.
            
            # Re-read audio for chunking (using librosa or just feeding pipeline)
            # The pipeline 'audio-classification' can accept a filename.
            # However, for long files, it might only classify the first few seconds.
            # We need to manually chunk it.
            
            # Let's keep it simple: Split audio into 5s segments using ffmpeg/moviepy logic relies on file I/O
            # actually, standard pipeline returns top labels for the clip.
            # We need accurate timestamps.
            
            # Better approach: Use the pipeline on specific intervals
            step = 5.0 # seconds
            for t in np.arange(0, duration, step):
                # Create a sub-clip (conceptually) or just pass start/end if supported
                # MoviePy subclip is slow. 
                # Alternative: Just process the whole file and hope for the best? No.
                # Let's return a single 'Audio Summary' for now to start, 
                # or implement robust chunking later if needed.
                # WAIT: pipeline calls on large files are problematic.
                pass 

            # REVISED STRATEGY: 
            # We will use the pipeline on the whole file, but we really need chunks.
            # Let's use a specialized library or raw torchaudio.
            # Actually, standard transformers pipeline handles long audio by truncating.
            # We MUST chunk.
            
            # Simple Chunking Loop
            import librosa
            import soundfile as sf
            
            y, sr = librosa.load(temp_audio, sr=16000)
            chunk_samples = int(5 * sr) # 5 seconds
            
            for i in range(0, len(y), chunk_samples):
                chunk = y[i:i+chunk_samples]
                if len(chunk) < sr: # Skip < 1 sec
                    continue
                    
                # Save temp chunk
                sf.write("temp_chunk.wav", chunk, sr)
                
                # Predict
                results = self.pipeline("temp_chunk.wav", top_k=5)
                
                # Check for threats
                timestamp = i / sr
                for res in results:
                    label = res['label']
                    score = res['score']
                    
                    # Check if label matches our targets
                    for target, display_name in self.target_labels.items():
                        if target in label and score > 0.3: # Threshold
                            print(f"  [Audio] {display_name} detected at {timestamp:.1f}s ({score:.2f})")
                            events.append({
                                "timestamp": round(timestamp, 2),
                                "description": f"Audio Detection: {display_name}",
                                "threat_type": display_name,
                                "confidence": round(score, 2),
                                "provider": "audio-ast"
                            })
                            break # One tag per chunk is enough usually

        except Exception as e:
            print(f"Audio Analysis Failed: {e}")
        finally:
            self.unload_model()
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            if os.path.exists("temp_chunk.wav"):
                os.remove("temp_chunk.wav")
                
        return events

# Singleton
audio_service = AudioService()
