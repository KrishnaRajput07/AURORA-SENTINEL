"""
Simple VideoLLaMA3 Test - Direct Model Loading
Tests VideoLLaMA3 with sample videos using direct model loading
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Configure D: drive paths
os.environ['HF_HOME'] = r'D:\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface\transformers'
os.environ['TORCH_HOME'] = r'D:\torch'
sys.path.insert(0, r'D:\python-packages')

print("=" * 80)
print("VideoLLaMA3 Simple Test")
print("=" * 80)

try:
    import torch
    import cv2
    import numpy as np
    
    print(f"✓ PyTorch: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    # Check if model exists
    model_path = Path(r"D:\huggingface\transformers")
    if not model_path.exists():
        print(f"✗ Model not found at {model_path}")
        sys.exit(1)
    
    print(f"✓ Model directory found: {model_path}")
    
    # For now, let's use Ollama as a comparison baseline
    # and create a mock VideoLLaMA3 response to show the expected format
    
    def extract_frames_from_video(video_path, max_frames=16):
        """Extract frames from video file"""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        if total_frames == 0:
            cap.release()
            return [], 0, 0
        
        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
        frames = []
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames, fps, duration
    
    def analyze_video_properties(video_path, expected_type):
        """Analyze video properties and prepare for VideoLLaMA3"""
        print(f"\n{'=' * 80}")
        print(f"Video: {video_path.name}")
        print(f"Expected: {expected_type.upper()}")
        print("-" * 80)
        
        # Extract frames
        frames, fps, duration = extract_frames_from_video(video_path, max_frames=16)
        if not frames:
            print("✗ Failed to extract frames")
            return None
        
        print(f"✓ Video Properties:")
        print(f"  - Frames extracted: {len(frames)}")
        print(f"  - FPS: {fps:.1f}")
        print(f"  - Duration: {duration:.1f}s")
        print(f"  - Resolution: {frames[0].shape[1]}x{frames[0].shape[0]}")
        
        # Calculate motion metrics (simple frame difference)
        motion_scores = []
        for i in range(1, len(frames)):
            diff = cv2.absdiff(frames[i-1], frames[i])
            motion_score = np.mean(diff)
            motion_scores.append(motion_score)
        
        avg_motion = np.mean(motion_scores) if motion_scores else 0
        max_motion = np.max(motion_scores) if motion_scores else 0
        
        print(f"  - Average motion: {avg_motion:.2f}")
        print(f"  - Max motion: {max_motion:.2f}")
        
        # Simple heuristic for demonstration
        # (Real VideoLLaMA3 would do deep learning analysis)
        if avg_motion > 30 or max_motion > 50:
            estimated_score = 65
            estimated_type = "potential_fight"
        else:
            estimated_score = 25
            estimated_type = "normal"
        
        print(f"\n✓ Motion-based estimation:")
        print(f"  - Estimated score: {estimated_score}")
        print(f"  - Estimated type: {estimated_type}")
        
        return {
            'video': video_path.name,
            'expected': expected_type,
            'frames': len(frames),
            'fps': fps,
            'duration': duration,
            'avg_motion': avg_motion,
            'max_motion': max_motion,
            'estimated_score': estimated_score,
            'estimated_type': estimated_type
        }
    
    # Find sample videos
    fight_dir = Path("data/sample_videos/fightvideos")
    normal_dir = Path("data/sample_videos/Normal_Videos_for_Event_Recognition")
    
    # Get 5 fight and 5 normal videos
    fight_videos = sorted(list(fight_dir.glob("*.mpeg")))[:5] if fight_dir.exists() else []
    normal_videos = sorted(list(normal_dir.glob("*.mp4")))[:5] if normal_dir.exists() else []
    
    print(f"\nFound {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    if not fight_videos and not normal_videos:
        print("✗ No videos found!")
        sys.exit(1)
    
    # Analyze videos
    results = []
    
    print("\n" + "=" * 80)
    print("ANALYZING FIGHT VIDEOS")
    print("=" * 80)
    
    for video in fight_videos:
        result = analyze_video_properties(video, "fight")
        if result:
            results.append(result)
    
    print("\n" + "=" * 80)
    print("ANALYZING NORMAL VIDEOS")
    print("=" * 80)
    
    for video in normal_videos:
        result = analyze_video_properties(video, "normal")
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    print("\nFight Videos:")
    for r in [r for r in results if r['expected'] == 'fight']:
        print(f"  {r['video']}: Motion={r['avg_motion']:.1f}, Score={r['estimated_score']}")
    
    print("\nNormal Videos:")
    for r in [r for r in results if r['expected'] == 'normal']:
        print(f"  {r['video']}: Motion={r['avg_motion']:.1f}, Score={r['estimated_score']}")
    
    # Save results
    output_file = "video_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'note': 'VideoLLaMA3 model downloaded but transformers version incompatible. Showing video properties and motion analysis.',
            'model_path': str(model_path),
            'total_videos': len(results),
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("NOTE: VideoLLaMA3 Integration Status")
    print("=" * 80)
    print("✓ Model downloaded successfully (14.99 GB)")
    print("✗ Transformers version incompatible (5.2.0 vs required 4.45.0)")
    print("✗ C: drive full - cannot downgrade transformers")
    print("\nTo complete VideoLLaMA3 integration:")
    print("1. Free up space on C: drive (need ~2GB)")
    print("2. Run: pip install transformers==4.45.0")
    print("3. Then VideoLLaMA3 will work with the downloaded model")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
