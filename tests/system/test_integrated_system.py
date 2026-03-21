"""
Test Integrated AI System
Tests: Qwen2-VL (GPU) + Ollama + Weighted Scoring
"""
import cv2
import numpy as np
import os
import sys

# Add AI layer to path


from aiRouter_enhanced import analyze_image
import base64
from io import BytesIO
from PIL import Image

def load_video_frame(video_path):
    """Load a single frame from video"""
    print(f"Loading frame from: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None
    
    # Get middle frame
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_frame = total_frames // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Error: Could not read frame")
        return None
    
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)

def image_to_base64(image):
    """Convert PIL Image to base64"""
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode()

def test_video(video_path, video_type, ml_score):
    """Test a single video"""
    print(f"\n{'='*60}")
    print(f"Testing {video_type}: {os.path.basename(video_path)}")
    print(f"ML Score: {ml_score}/100")
    print(f"{'='*60}")
    
    # Load frame
    image = load_video_frame(video_path)
    if not image:
        print("Failed to load frame")
        return None
    
    # Convert to base64
    image_data = f"data:image/jpeg;base64,{image_to_base64(image)}"
    
    # Analyze
    ml_factors = {}
    if ml_score > 70:
        ml_factors = {'aggression': 0.8, 'proximity': 0.7}
    elif ml_score > 40:
        ml_factors = {'movement': 0.6}
    
    result = analyze_image(
        image_data=image_data,
        ml_score=ml_score,
        ml_factors=ml_factors,
        camera_id='TEST-CAM'
    )
    
    print(f"\nResults:")
    print(f"  Provider: {result.get('provider', 'unknown')}")
    print(f"  AI Score: {result['aiScore']}/100")
    print(f"  Scene Type: {result['sceneType']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Weighted: {result.get('weighted', False)}")
    print(f"  Explanation: {result['explanation'][:150]}...")
    
    return result

def main():
    print("="*60)
    print("Integrated AI System Test")
    print("Testing: Qwen2-VL (GPU) + Ollama + Weighted Scoring")
    print("="*60)
    
    # Test videos with simulated ML scores
    test_cases = [
        # Fight videos (high ML scores)
        ("data/sample_videos/fightvideos/fight_0034.mpeg", "FIGHT", 85),
        ("data/sample_videos/fightvideos/fight_0081.mpeg", "FIGHT", 82),
        
        # Normal videos (low ML scores)
        ("data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_015_x264.mp4", "NORMAL", 15),
        ("data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_100_x264.mp4", "NORMAL", 12),
    ]
    
    results = []
    
    for video_path, video_type, ml_score in test_cases:
        if os.path.exists(video_path):
            result = test_video(video_path, video_type, ml_score)
            if result:
                results.append({
                    'type': video_type,
                    'ml_score': ml_score,
                    'ai_score': result['aiScore'],
                    'scene_type': result['sceneType'],
                    'provider': result.get('provider', 'unknown'),
                    'weighted': result.get('weighted', False)
                })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    fight_results = [r for r in results if r['type'] == 'FIGHT']
    normal_results = [r for r in results if r['type'] == 'NORMAL']
    
    if fight_results:
        print(f"\nFight Videos (tested {len(fight_results)}):")
        for r in fight_results:
            print(f"  ML: {r['ml_score']}, AI: {r['ai_score']}, Type: {r['scene_type']}, Provider: {r['provider']}, Weighted: {r['weighted']}")
        avg_ai = sum(r['ai_score'] for r in fight_results) / len(fight_results)
        print(f"  Average AI Score: {avg_ai:.1f}/100")
    
    if normal_results:
        print(f"\nNormal Videos (tested {len(normal_results)}):")
        for r in normal_results:
            print(f"  ML: {r['ml_score']}, AI: {r['ai_score']}, Type: {r['scene_type']}, Provider: {r['provider']}, Weighted: {r['weighted']}")
        avg_ai = sum(r['ai_score'] for r in normal_results) / len(normal_results)
        print(f"  Average AI Score: {avg_ai:.1f}/100")
    
    # Provider statistics
    providers = {}
    for r in results:
        provider = r['provider']
        providers[provider] = providers.get(provider, 0) + 1
    
    print(f"\nProvider Usage:")
    for provider, count in providers.items():
        print(f"  {provider}: {count} times")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()
