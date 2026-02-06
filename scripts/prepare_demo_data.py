import cv2
import os

def extract_sample_clips():
    """Extract 30-second clips from full videos for demo"""
    # Ensure directories exist
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/sample_videos', exist_ok=True)

    # Note: In a real scenario, we would expect files in data/raw.
    # For this setup script, we'll list what we expect.
    video_scenarios = [
        'normal_crowd.mp4',
        'suspicious_loitering.mp4',
        'aggressive_behavior.mp4',
        'unattended_object.mp4',
        'crowded_area.mp4'
    ]
    
    print("Looking for raw videos in data/raw/...")
    
    for video in video_scenarios:
        input_path = f'data/raw/{video}'
        if not os.path.exists(input_path):
            print(f"Skipping {video} (not found in data/raw/)")
            continue

        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Extract first 30 seconds
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_path = f'data/sample_videos/{video}'
        out = cv2.VideoWriter(
            output_path,
            fourcc, fps, (1920, 1080)
        )
        
        frame_count = 0
        max_frames = int(30 * fps)
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        print(f"Prepared {video}")

if __name__ == "__main__":
    extract_sample_clips()
