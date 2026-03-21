"""
Test Ollama Integration with Video Files
Supports: MP4, MPEG, AVI, MOV, MKV, and other common formats
"""
import cv2
import base64
import requests
import json
import sys
import os
from pathlib import Path

def extract_frame_from_video(video_path, frame_number=0):
    """
    Extract a specific frame from video file
    Supports: MP4, MPEG, AVI, MOV, MKV, etc.
    """
    print(f"[TEST] Opening video: {video_path}")
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"[ERROR] Video file not found: {video_path}")
        return None
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {video_path}")
        return None
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"[TEST] Video info:")
    print(f"  - Total frames: {total_frames}")
    print(f"  - FPS: {fps:.2f}")
    print(f"  - Duration: {duration:.2f} seconds")
    
    # If frame_number is negative, extract from middle
    if frame_number < 0:
        frame_number = total_frames // 2
        print(f"[TEST] Extracting middle frame: {frame_number}")
    
    # Set frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    # Read frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"[ERROR] Could not read frame {frame_number}")
        return None
    
    print(f"[TEST] Successfully extracted frame {frame_number}")
    print(f"  - Frame shape: {frame.shape}")
    
    return frame

def frame_to_base64(frame):
    """Convert frame to base64 encoded JPEG"""
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    
    # Convert to base64
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    
    # Create data URL
    data_url = f"data:image/jpeg;base64,{jpg_as_text}"
    
    return data_url

def test_ollama_with_frame(frame, ml_score=50, camera_id="TEST"):
    """
    Test Ollama AI service with a video frame
    """
    print(f"\n[TEST] Testing Ollama AI service...")
    
    # Convert frame to base64
    image_data = frame_to_base64(frame)
    
    # Prepare request
    payload = {
        "imageData": image_data,
        "mlScore": ml_score,
        "mlFactors": {
            "aggressive_posture": 0.5,
            "proximity_violation": 0.3,
            "weapon_detection": 0.0
        },
        "cameraId": camera_id
    }
    
    # Send request to AI service
    try:
        print(f"[TEST] Sending request to AI service...")
        response = requests.post(
            "http://localhost:3001/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[TEST] ✅ AI Analysis Result:")
            print(f"  - Provider: {result.get('provider', 'unknown')}")
            print(f"  - AI Score: {result.get('aiScore', 0)}%")
            print(f"  - Scene Type: {result.get('sceneType', 'unknown')}")
            print(f"  - Confidence: {result.get('confidence', 0):.2f}")
            print(f"  - Explanation: {result.get('explanation', 'N/A')}")
            
            return result
        else:
            print(f"[ERROR] AI service returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Could not connect to AI service at http://localhost:3001")
        print(f"  Make sure the AI service is running:")
        print(f"  cd ai-intelligence-layer && npm start")
        return None
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None

def test_multiple_frames(video_path, num_frames=5, ml_score=50):
    """
    Test with multiple frames from the video
    """
    print(f"\n[TEST] Testing with {num_frames} frames from video...")
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    # Calculate frame indices to sample
    frame_indices = [int(i * total_frames / (num_frames + 1)) for i in range(1, num_frames + 1)]
    
    results = []
    for i, frame_idx in enumerate(frame_indices):
        print(f"\n[TEST] === Frame {i+1}/{num_frames} (index: {frame_idx}) ===")
        
        frame = extract_frame_from_video(video_path, frame_idx)
        if frame is not None:
            result = test_ollama_with_frame(frame, ml_score, f"TEST-frame{i+1}")
            if result:
                results.append(result)
    
    # Summary
    if results:
        print(f"\n[TEST] === Summary of {len(results)} frames ===")
        avg_score = sum(r.get('aiScore', 0) for r in results) / len(results)
        print(f"  - Average AI Score: {avg_score:.1f}%")
        
        scene_types = [r.get('sceneType', 'unknown') for r in results]
        most_common = max(set(scene_types), key=scene_types.count)
        print(f"  - Most common scene type: {most_common}")
        
        providers = [r.get('provider', 'unknown') for r in results]
        print(f"  - Providers used: {', '.join(set(providers))}")
    
    return results

def check_ai_service():
    """Check if AI service is running"""
    try:
        response = requests.get("http://localhost:3001/health", timeout=5)
        if response.status_code == 200:
            print("[TEST] ✅ AI service is running")
            return True
    except:
        pass
    
    print("[TEST] ❌ AI service is not running")
    print("[TEST] Start it with: cd ai-intelligence-layer && npm start")
    return False

def check_ollama():
    """Check if Ollama is running and has llava model"""
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            print(f"[TEST] ✅ Ollama is running")
            print(f"[TEST] Available models: {', '.join(model_names) if model_names else 'None'}")
            
            if any('llava' in name for name in model_names):
                print(f"[TEST] ✅ llava model is installed")
                return True
            else:
                print(f"[TEST] ⚠️ llava model not found")
                print(f"[TEST] Install with: ollama pull llava")
                return False
    except:
        print(f"[TEST] ❌ Ollama is not running")
        print(f"[TEST] Start it with: ollama serve")
        return False

def main():
    print("=" * 60)
    print("Ollama Video Testing Tool")
    print("Supports: MP4, MPEG, AVI, MOV, MKV, and more")
    print("=" * 60)
    
    # Check if video path provided
    if len(sys.argv) < 2:
        print("\nUsage: python test_ollama_with_video.py <video_path> [ml_score] [num_frames]")
        print("\nExamples:")
        print("  python test_ollama_with_video.py video.mpeg")
        print("  python test_ollama_with_video.py video.mp4 75")
        print("  python test_ollama_with_video.py video.avi 60 10")
        print("\nSearching for video files in current directory...")
        
        # Search for video files
        video_extensions = ['.mp4', '.mpeg', '.mpg', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(Path('.').glob(f'*{ext}'))
            video_files.extend(Path('.').glob(f'*{ext.upper()}'))
        
        if video_files:
            print(f"\nFound {len(video_files)} video file(s):")
            for i, vf in enumerate(video_files[:10], 1):
                print(f"  {i}. {vf}")
            
            if len(video_files) > 10:
                print(f"  ... and {len(video_files) - 10} more")
            
            print(f"\nUsage: python test_ollama_with_video.py {video_files[0]}")
        else:
            print("\nNo video files found in current directory")
        
        return
    
    video_path = sys.argv[1]
    ml_score = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    num_frames = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    # Check prerequisites
    print("\n[TEST] Checking prerequisites...")
    ai_service_ok = check_ai_service()
    ollama_ok = check_ollama()
    
    if not ai_service_ok:
        print("\n[TEST] ⚠️ AI service is not running. Please start it first.")
        return
    
    if not ollama_ok:
        print("\n[TEST] ⚠️ Ollama or llava model not available.")
        print("[TEST] The test will use fallback provider (HuggingFace or rule-based)")
    
    # Test with video
    if num_frames == 1:
        # Single frame test (middle of video)
        print(f"\n[TEST] Testing with single frame from: {video_path}")
        frame = extract_frame_from_video(video_path, frame_number=-1)
        
        if frame is not None:
            result = test_ollama_with_frame(frame, ml_score, "TEST")
            
            if result:
                print(f"\n[TEST] ✅ Test completed successfully!")
            else:
                print(f"\n[TEST] ❌ Test failed")
        else:
            print(f"\n[TEST] ❌ Could not extract frame from video")
    else:
        # Multiple frames test
        results = test_multiple_frames(video_path, num_frames, ml_score)
        
        if results:
            print(f"\n[TEST] ✅ Test completed successfully!")
        else:
            print(f"\n[TEST] ❌ Test failed")

if __name__ == "__main__":
    main()
