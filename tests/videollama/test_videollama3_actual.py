"""
Real VideoLLaMA3 Test with Actual Sample Videos
Uses the VideoLLaMA integration to test with fight and normal videos
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

# Add ai-intelligence-layer to path
sys.path.insert(0, 'ai-intelligence-layer')

print("=" * 80)
print("VideoLLaMA3 Real Test with Sample Videos")
print("=" * 80)

try:
    import cv2
    import numpy as np
    from videoLLaMA_integration import VideoLLaMAAnalyzer
    
    print("✓ All dependencies loaded")
    
    # Initialize VideoLLaMA analyzer
    print("\nInitializing VideoLLaMA3...")
    analyzer = VideoLLaMAAnalyzer()
    
    def extract_frames_from_video(video_path, max_frames=16):
        """Extract frames from video file"""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames == 0:
            cap.release()
            return [], 0
        
        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
        frames = []
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames, fps
    
    def analyze_video(video_path, expected_type):
        """Analyze video with VideoLLaMA3"""
        print(f"\n{'=' * 80}")
        print(f"Video: {video_path.name}")
        print(f"Expected: {expected_type.upper()}")
        print("-" * 80)
        
        start_time = datetime.now()
        
        # Extract frames
        frames, fps = extract_frames_from_video(video_path, max_frames=16)
        if not frames:
            print("✗ Failed to extract frames")
            return None
        
        print(f"✓ Extracted {len(frames)} frames (FPS: {fps:.1f})")
        
        try:
            # Analyze with VideoLLaMA3
            print("Analyzing with VideoLLaMA3...")
            result = analyzer.analyze_video_frames(frames, fps=max(1, int(fps/10)), max_frames=16)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'=' * 80}")
            print("VideoLLaMA3 Response:")
            print("-" * 80)
            print(f"AI Score: {result['aiScore']}")
            print(f"Scene Type: {result['sceneType']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Explanation: {result['explanation']}")
            print("-" * 80)
            print(f"Analysis time: {duration:.2f}s")
            print(f"Expected: {expected_type.upper()}")
            
            # Determine if correct
            scene_type = result['sceneType'].lower()
            correct = None
            
            if expected_type == 'fight':
                # For fight videos, accept real_fight or high scores
                if scene_type == 'real_fight' or result['aiScore'] >= 60:
                    correct = True
                    print("✓ CORRECT - Fight detected")
                else:
                    correct = False
                    print("✗ INCORRECT - Fight not detected")
            else:  # normal
                # For normal videos, accept normal or low scores
                if scene_type == 'normal' or result['aiScore'] < 40:
                    correct = True
                    print("✓ CORRECT - Normal activity detected")
                else:
                    correct = False
                    print("✗ INCORRECT - False positive")
            
            return {
                'video': video_path.name,
                'expected': expected_type,
                'ai_score': result['aiScore'],
                'scene_type': result['sceneType'],
                'confidence': result['confidence'],
                'explanation': result['explanation'],
                'frames_analyzed': len(frames),
                'duration_seconds': duration,
                'correct': correct
            }
            
        except Exception as e:
            print(f"✗ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Find sample videos
    fight_dir = Path("data/sample_videos/fightvideos")
    normal_dir = Path("data/sample_videos/Normal_Videos_for_Event_Recognition")
    
    # Get 3 fight and 3 normal videos
    fight_videos = sorted(list(fight_dir.glob("*.mpeg")))[:3] if fight_dir.exists() else []
    normal_videos = sorted(list(normal_dir.glob("*.mp4")))[:3] if normal_dir.exists() else []
    
    print(f"\nFound {len(fight_videos)} fight videos and {len(normal_videos)} normal videos")
    
    if not fight_videos and not normal_videos:
        print("✗ No videos found!")
        sys.exit(1)
    
    # Run tests
    results = []
    
    print("\n" + "=" * 80)
    print("TESTING FIGHT VIDEOS")
    print("=" * 80)
    
    for video in fight_videos:
        result = analyze_video(video, "fight")
        if result:
            results.append(result)
    
    print("\n" + "=" * 80)
    print("TESTING NORMAL VIDEOS")
    print("=" * 80)
    
    for video in normal_videos:
        result = analyze_video(video, "normal")
        if result:
            results.append(result)
    
    # Calculate accuracy
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    correct = sum(1 for r in results if r.get('correct') == True)
    total = len([r for r in results if r.get('correct') is not None])
    
    if total > 0:
        accuracy = (correct / total) * 100
        print(f"\nOverall Accuracy: {accuracy:.1f}% ({correct}/{total})")
    
    # Fight detection accuracy
    fight_results = [r for r in results if r['expected'] == 'fight' and r.get('correct') is not None]
    if fight_results:
        fight_correct = sum(1 for r in fight_results if r['correct'])
        fight_accuracy = (fight_correct / len(fight_results)) * 100
        print(f"Fight Detection: {fight_accuracy:.1f}% ({fight_correct}/{len(fight_results)})")
        
        # Show fight scores
        print("\nFight Video Scores:")
        for r in fight_results:
            status = "✓" if r['correct'] else "✗"
            print(f"  {status} {r['video']}: Score={r['ai_score']}, Type={r['scene_type']}")
    
    # Normal detection accuracy
    normal_results = [r for r in results if r['expected'] == 'normal' and r.get('correct') is not None]
    if normal_results:
        normal_correct = sum(1 for r in normal_results if r['correct'])
        normal_accuracy = (normal_correct / len(normal_results)) * 100
        print(f"Normal Detection: {normal_accuracy:.1f}% ({normal_correct}/{len(normal_results)})")
        
        # Show normal scores
        print("\nNormal Video Scores:")
        for r in normal_results:
            status = "✓" if r['correct'] else "✗"
            print(f"  {status} {r['video']}: Score={r['ai_score']}, Type={r['scene_type']}")
    
    # Average analysis time
    avg_time = sum(r['duration_seconds'] for r in results) / len(results) if results else 0
    print(f"\nAverage Analysis Time: {avg_time:.2f}s per video")
    
    # Save results
    output_file = "videollama3_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': 'DAMO-NLP-SG/VideoLLaMA3-7B',
            'total_videos': len(results),
            'accuracy': accuracy if total > 0 else None,
            'fight_accuracy': fight_accuracy if fight_results else None,
            'normal_accuracy': normal_accuracy if normal_results else None,
            'avg_time_seconds': avg_time,
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print("=" * 80)
    
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
