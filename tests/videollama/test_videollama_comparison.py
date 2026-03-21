"""
VideoLLaMA3 vs Ollama Comparison Test
Uses both models to analyze the same videos and compare results
"""
import cv2
import base64
import requests
import json
import os
from pathlib import Path
import time
import numpy as np

# Directories
FIGHT_DIR = "data/sample_videos/fightvideos"
NORMAL_DIR = "data/sample_videos/Normal_Videos_for_Event_Recognition"
AI_URL = "http://localhost:3001/analyze"

def extract_video_frames(video_path, max_frames=10, fps_sample=1):
    """Extract multiple frames from video for temporal analysis"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None, None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / video_fps if video_fps > 0 else 0
    
    # Sample frames evenly
    frame_interval = max(1, total_frames // max_frames)
    frame_indices = list(range(0, total_frames, frame_interval))[:max_frames]
    
    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    
    cap.release()
    
    info = {
        'total_frames': total_frames,
        'fps': video_fps,
        'duration': duration,
        'sampled_frames': len(frames)
    }
    
    return frames, info

def frame_to_base64(frame):
    """Convert frame to base64"""
    _, buffer = cv2.imencode('.jpg', frame)
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

def analyze_with_ollama_single_frame(frame, video_name, ml_score=50):
    """Analyze single frame with Ollama (current approach)"""
    try:
        payload = {
            "imageData": frame_to_base64(frame),
            "mlScore": ml_score,
            "mlFactors": {"aggressive_posture": 0.5},
            "cameraId": video_name
        }
        
        response = requests.post(AI_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            result['method'] = 'ollama_single_frame'
            return result
    except Exception as e:
        print(f"  Ollama error: {e}")
    return None

def analyze_with_ollama_multi_frame(frames, video_name, ml_score=50):
    """Analyze multiple frames with Ollama and take MAX score"""
    scores = []
    scene_types = []
    
    print(f"  Analyzing {len(frames)} frames with Ollama...")
    
    for i, frame in enumerate(frames):
        try:
            payload = {
                "imageData": frame_to_base64(frame),
                "mlScore": ml_score,
                "mlFactors": {"aggressive_posture": 0.5},
                "cameraId": f"{video_name}_frame{i}"
            }
            
            response = requests.post(AI_URL, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                scores.append(result.get('aiScore', 0))
                scene_types.append(result.get('sceneType', 'unknown'))
        except Exception as e:
            print(f"    Frame {i} error: {e}")
            continue
    
    if scores:
        max_score = max(scores)
        # Most common scene type
        most_common_scene = max(set(scene_types), key=scene_types.count) if scene_types else 'unknown'
        
        return {
            'aiScore': max_score,
            'sceneType': most_common_scene,
            'provider': 'ollama',
            'method': 'ollama_multi_frame',
            'frames_analyzed': len(scores),
            'all_scores': scores,
            'all_scenes': scene_types
        }
    
    return None

def analyze_with_videollama_simulation(frames, video_name):
    """
    Simulate VideoLLaMA3 temporal analysis
    In production, this would call the actual VideoLLaMA3 model
    For now, we simulate by analyzing motion and temporal patterns
    """
    print(f"  Simulating VideoLLaMA3 temporal analysis...")
    
    # Calculate motion between frames
    motion_scores = []
    for i in range(len(frames) - 1):
        # Convert to grayscale
        gray1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frames[i+1], cv2.COLOR_BGR2GRAY)
        
        # Calculate frame difference
        diff = cv2.absdiff(gray1, gray2)
        motion = np.mean(diff)
        motion_scores.append(motion)
    
    avg_motion = np.mean(motion_scores) if motion_scores else 0
    max_motion = max(motion_scores) if motion_scores else 0
    
    # Simulate VideoLLaMA3 scoring based on motion
    # High motion + sustained = likely fight
    # Low motion = likely normal
    
    if avg_motion > 30 and max_motion > 50:
        # High sustained motion - likely fight
        ai_score = 75
        scene_type = 'real_fight'
        confidence = 0.8
    elif avg_motion > 20:
        # Moderate motion - could be boxing or fight
        ai_score = 50
        scene_type = 'boxing'
        confidence = 0.6
    else:
        # Low motion - likely normal
        ai_score = 25
        scene_type = 'normal'
        confidence = 0.7
    
    return {
        'aiScore': ai_score,
        'sceneType': scene_type,
        'provider': 'videollama_simulated',
        'method': 'temporal_analysis',
        'confidence': confidence,
        'avg_motion': float(avg_motion),
        'max_motion': float(max_motion),
        'frames_analyzed': len(frames)
    }

def test_video_comparison(video_path, video_type, ml_score):
    """Test single video with all three methods"""
    video_name = os.path.basename(video_path)
    print(f"\nTesting: {video_name}")
    
    # Extract frames
    frames, info = extract_video_frames(video_path, max_frames=10)
    
    if not frames or len(frames) == 0:
        print(f"  ❌ Could not extract frames")
        return None
    
    print(f"  Video: {info['duration']:.1f}s, {len(frames)} frames sampled")
    
    results = {
        'video': video_name,
        'type': video_type,
        'video_info': info,
        'ml_score': ml_score
    }
    
    # Method 1: Ollama Single Frame (current)
    print(f"  [1/3] Ollama Single Frame...")
    middle_frame = frames[len(frames) // 2]
    ollama_single = analyze_with_ollama_single_frame(middle_frame, video_name, ml_score)
    if ollama_single:
        results['ollama_single'] = ollama_single
        print(f"    Score: {ollama_single.get('aiScore')}%, Scene: {ollama_single.get('sceneType')}")
    
    # Method 2: Ollama Multi-Frame (improved)
    print(f"  [2/3] Ollama Multi-Frame...")
    ollama_multi = analyze_with_ollama_multi_frame(frames, video_name, ml_score)
    if ollama_multi:
        results['ollama_multi'] = ollama_multi
        print(f"    Max Score: {ollama_multi.get('aiScore')}%, Scene: {ollama_multi.get('sceneType')}")
    
    # Method 3: VideoLLaMA3 Temporal (simulated)
    print(f"  [3/3] VideoLLaMA3 Temporal...")
    videollama = analyze_with_videollama_simulation(frames, video_name)
    if videollama:
        results['videollama'] = videollama
        print(f"    Score: {videollama.get('aiScore')}%, Scene: {videollama.get('sceneType')}")
        print(f"    Motion: avg={videollama.get('avg_motion'):.1f}, max={videollama.get('max_motion'):.1f}")
    
    # Evaluate each method
    expected_high = (video_type == 'fight')
    
    for method in ['ollama_single', 'ollama_multi', 'videollama']:
        if method in results:
            score = results[method].get('aiScore', 0)
            results[method]['correct'] = (score > 60) == expected_high
    
    return results

def main():
    print("="*70)
    print("OLLAMA vs VIDEOLLAMA3 COMPARISON TEST")
    print("="*70)
    
    # Check AI service
    try:
        response = requests.get("http://localhost:3001/health", timeout=5)
        if response.status_code != 200:
            print("❌ AI service not responding")
            return
    except:
        print("❌ AI service not running")
        return
    
    print("✅ AI service is running\n")
    
    # Test subset of videos
    fight_videos = list(Path(FIGHT_DIR).glob("*.mpeg"))[:5]
    normal_videos = list(Path(NORMAL_DIR).glob("*.mp4"))[:5]
    
    print(f"Testing {len(fight_videos)} fight + {len(normal_videos)} normal videos\n")
    
    all_results = []
    
    # Test fight videos
    print("="*70)
    print("FIGHT VIDEOS")
    print("="*70)
    for video in fight_videos:
        result = test_video_comparison(str(video), 'fight', ml_score=70)
        if result:
            all_results.append(result)
        time.sleep(1)
    
    # Test normal videos
    print("\n" + "="*70)
    print("NORMAL VIDEOS")
    print("="*70)
    for video in normal_videos:
        result = test_video_comparison(str(video), 'normal', ml_score=30)
        if result:
            all_results.append(result)
        time.sleep(1)
    
    # Generate comparison report
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    methods = ['ollama_single', 'ollama_multi', 'videollama']
    method_names = {
        'ollama_single': 'Ollama Single Frame',
        'ollama_multi': 'Ollama Multi-Frame',
        'videollama': 'VideoLLaMA3 Temporal'
    }
    
    for method in methods:
        results_with_method = [r for r in all_results if method in r]
        if not results_with_method:
            continue
        
        correct = sum(1 for r in results_with_method if r[method].get('correct', False))
        total = len(results_with_method)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Fight detection
        fight_results = [r for r in results_with_method if r['type'] == 'fight']
        fight_correct = sum(1 for r in fight_results if r[method].get('correct', False))
        fight_accuracy = (fight_correct / len(fight_results) * 100) if fight_results else 0
        
        # Normal detection
        normal_results = [r for r in results_with_method if r['type'] == 'normal']
        normal_correct = sum(1 for r in normal_results if r[method].get('correct', False))
        normal_accuracy = (normal_correct / len(normal_results) * 100) if normal_results else 0
        
        print(f"\n{method_names[method]}:")
        print(f"  Overall: {correct}/{total} ({accuracy:.1f}%)")
        print(f"  Fight Detection: {fight_correct}/{len(fight_results)} ({fight_accuracy:.1f}%)")
        print(f"  Normal Detection: {normal_correct}/{len(normal_results)} ({normal_accuracy:.1f}%)")
    
    # Save results
    with open('comparison_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nDetailed results saved to: comparison_results.json")
    
    # Recommendation
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    best_method = max(methods, 
                     key=lambda m: sum(1 for r in all_results if m in r and r[m].get('correct', False)))
    
    print(f"\nBest performing method: {method_names[best_method]}")
    print("\nNext steps:")
    print("1. Review comparison_results.json for detailed analysis")
    print("2. If multi-frame improves results, use that approach")
    print("3. If temporal analysis needed, install full VideoLLaMA3")

if __name__ == "__main__":
    main()
