
import sys
import os
import argparse
import numpy as np
from moviepy import VideoFileClip
from transformers import pipeline

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(description="Debug Audio Model Raw Output")
    parser.add_argument("video_path", help="Path to the video file")
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        return

    print(f"DEBUGGING RAW AUDIO OUTPUT: {video_path}")
    print("------------------------------------------------")

    # Load Model
    print("Loading Model...")
    pipe = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593", device="cpu")

    # Extract Audio
    try:
        video = VideoFileClip(video_path)
        if video.audio is None:
            print("ERROR: No audio track found in video.")
            return

        temp_audio = "debug_temp.wav"
        video.audio.write_audiofile(temp_audio, logger=None)
        video.close()
        
        # Chunk and Predict
        import librosa
        y, sr = librosa.load(temp_audio, sr=16000)
        chunk_samples = int(5 * sr) # 5 seconds
        
        for i in range(0, len(y), chunk_samples):
            chunk = y[i:i+chunk_samples]
            if len(chunk) < sr: continue
            
            timestamp = i / sr
            print(f"\n--- Chunk at {timestamp:.1f}s ---")
            
            # Predict
            results = pipe({"array": chunk, "sampling_rate": sr}, top_k=5)
            
            for res in results:
                print(f"  {res['label']}: {res['score']:.4f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists("debug_temp.wav"):
            os.remove("debug_temp.wav")

if __name__ == "__main__":
    main()
