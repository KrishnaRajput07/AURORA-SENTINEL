
import sys
import os
import argparse

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.audio_service import audio_service

def main():
    parser = argparse.ArgumentParser(description="Test Audio Service on a video file")
    parser.add_argument("video_path", help="Path to the video file")
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        return

    print(f"Analyzing video: {video_path}")
    print("------------------------------------------------")

    try:
        events = audio_service.analyze_video(video_path)
        print("------------------------------------------------")
        print(f"Analysis Complete. Found {len(events)} events.")
        for event in events:
            print(f"[{event['timestamp']}s] {event['description']} (Conf: {event['confidence']})")
            
    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    main()
