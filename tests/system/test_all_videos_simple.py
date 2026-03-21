"""
Simple test script for all videos with Ollama
"""
import cv2
import base64
import requests
import json
import os
from pathlib import Path
import time

# Directories
FIGHT_DIR = "data/sample_videos/fightvideos"
NORMAL_DIR = "data/sample_videos/Normal_Videos_for_Event_Recognition"
AI_URL = "http://localhost:3001/analyze"

def frame_to_base64(frame):
    """Convert frame to base64"""
    _, buffer = cv2.imencode('.jpg', frame)
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

def extract_middle_frame(video_path):
    """Extract middle frame from video"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle = total_frames // 2
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle)
    ret, frame = cap.read()
    cap.release()
    
    return frame if ret else None

def analyze_frame(frame, video_name, ml_score=50):
    """Send frame to AI service"""
    try:
        payload = {
            "imageData": frame_to_base64(frame),
            "mlScore": ml_score,
            "mlFactors": {"aggressive_posture": 0.5},
            "cameraId": video_name
        }
        
        response = requests.post(AI_URL, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

def test_videos(video_dir, video_type, max_videos=5):
    """Test videos from directory"""
    print(f"\n{'='*70}")
    print(f"Testing {video_type.upper()} Videos")
    print(f"{'='*70}")
    
    # Get video files
    if video_type == "fight":
        videos = list(Path(video_dir).glob("*.mpeg"))[:max_videos]
        expected_high_score = True
    else:
        videos = list(Path(video_dir).glob("*.mp4"))[:max_videos]
        expected_high_score = False
    
    print(f"Found {len(videos)} videos to test\n")
    
    results = []
    for i, video_path in enumerate(videos, 1):
        video_name = video_path.name
        print(f"[{i}/{len(videos)}] Testing: {video_name[:50]}")
        
        # Extract frame
        frame = extract_middle_frame(str(video_path))
        if frame is None:
            print(f"  ❌ Could not extract frame")
            continue
        
        # Analyze
        ml_score = 70 if expected_high_score else 30
        result = analyze_frame(frame, video_name, ml_score)
        
        if result:
            ai_score = result.get('aiScore', 0)
            scene_type = result.get('sceneType', 'unknown')
            provider = result.get('provider', 'unknown')
            
            # Determine if correct
            if expected_high_score:
                correct = ai_score > 60  # Fight should have high score
            else:
                correct = ai_score < 60  # Normal should have low score
            
            status = "✅" if correct else "❌"
            print(f"  {status} AI Score: {ai_score}% | Scene: {scene_type} | Provider: {provider}")
            
            results.append({
                'video': video_name,
                'type': video_type,
                'ml_score': ml_score,
                'ai_score': ai_score,
                'scene_type': scene_type,
                'provider': provider,
                'correct': correct
            })
        else:
            print(f"  ❌ Analysis failed")
        
        time.sleep(0.5)  # Brief pause
    
    return results

def main():
    print("="*70)
    print("OLLAMA VIDEO TESTING - ALL VIDEOS")
    print("="*70)
    
    # Check AI service
    try:
        response = requests.get("http://localhost:3001/health", timeout=5)
        if response.status_code == 200:
            print("✅ AI service is running\n")
        else:
            print("❌ AI service not responding")
            return
    except:
        print("❌ AI service not running")
        print("Start with: cd ai-intelligence-layer && npm start")
        return
    
    # Test fight videos
    fight_results = test_videos(FIGHT_DIR, "fight", max_videos=17)
    
    # Test normal videos
    normal_results = test_videos(NORMAL_DIR, "normal", max_videos=10)
    
    # Summary
    all_results = fight_results + normal_results
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    total = len(all_results)
    correct = sum(1 for r in all_results if r['correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\nTotal videos: {total}")
    print(f"Correct: {correct}/{total}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Fight videos
    fight_correct = sum(1 for r in fight_results if r['correct'])
    fight_accuracy = (fight_correct / len(fight_results) * 100) if fight_results else 0
    print(f"\nFight videos: {fight_correct}/{len(fight_results)} ({fight_accuracy:.1f}%)")
    
    # Normal videos
    normal_correct = sum(1 for r in normal_results if r['correct'])
    normal_accuracy = (normal_correct / len(normal_results) * 100) if normal_results else 0
    false_positives = len(normal_results) - normal_correct
    print(f"Normal videos: {normal_correct}/{len(normal_results)} ({normal_accuracy:.1f}%)")
    print(f"False positives: {false_positives}/{len(normal_results)}")
    
    # Provider stats
    ollama_count = sum(1 for r in all_results if r.get('provider') == 'ollama')
    print(f"\nOllama used: {ollama_count}/{total} times")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to: test_results.json")

if __name__ == "__main__":
    main()
