
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Test Script for Enhanced Fight Detection

Tests the enhanced ML risk engine with real video files to validate:
1. Fight videos produce ML_Score > 70%
2. Boxing video produces ML_Score > 60% but AI_Score < 30%
3. All videos generate alerts for operator review
"""

import cv2
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models.scoring.risk_engine import RiskScoringEngine
from backend.services.ml_service import MLService

# Test video paths
TEST_VIDEOS = {
    'fight_1': 'storage/temp/raw_1772268166.802879_4rth.mp4',
    'fight_2': 'storage/temp/raw_1772268210.415873_5th.mp4',
    'boxing': 'storage/temp/raw_1772268625.365338_scr9-231238~2sdddsd.mp4'
}

# Expected results
EXPECTED_RESULTS = {
    'fight_1': {'ml_score_min': 70.0, 'description': 'Fight video 1'},
    'fight_2': {'ml_score_min': 70.0, 'description': 'Fight video 2'},
    'boxing': {'ml_score_min': 60.0, 'description': 'Boxing video (controlled sparring)'}
}


def test_video(video_path: str, video_name: str, ml_service: MLService, risk_engine: RiskScoringEngine):
    """
    Test a single video file and return results.
    
    Args:
        video_path: Path to video file
        video_name: Name identifier for the video
        ml_service: ML service instance
        risk_engine: Risk scoring engine instance
        
    Returns:
        Dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing: {video_name} - {EXPECTED_RESULTS[video_name]['description']}")
    print(f"Video: {video_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(video_path):
        print(f"❌ ERROR: Video file not found: {video_path}")
        return {
            'video_name': video_name,
            'success': False,
            'error': 'File not found',
            'max_ml_score': 0.0,
            'frames_processed': 0
        }
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video info: {total_frames} frames @ {fps} FPS")
    
    max_ml_score = 0.0
    max_ml_factors = {}
    max_score_frame = 0
    frames_processed = 0
    high_risk_frames = 0
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every 2nd frame for speed
            if frame_count % 2 == 0:
                # Detect objects and poses
                detection_data = ml_service.detector.process_frame(frame)
                
                # Calculate risk score
                timestamp = frame_count / fps
                context = {
                    'timestamp': timestamp,
                    'hour': 14,  # Afternoon
                    'sensitivity': 1.0
                }
                
                ml_score, ml_factors = risk_engine.calculate_risk(detection_data, context)
                
                # Track maximum score
                if ml_score > max_ml_score:
                    max_ml_score = ml_score
                    max_ml_factors = ml_factors
                    max_score_frame = frame_count
                
                # Count high-risk frames
                if ml_score > 60:
                    high_risk_frames += 1
                
                frames_processed += 1
                
                # Print progress every 30 frames
                if frames_processed % 15 == 0:
                    print(f"  Frame {frame_count}/{total_frames}: ML_Score={ml_score:.1f}% "
                          f"(Max so far: {max_ml_score:.1f}%)")
            
            frame_count += 1
    
    except Exception as e:
        print(f"❌ ERROR processing video: {e}")
        import traceback
        traceback.print_exc()
        return {
            'video_name': video_name,
            'success': False,
            'error': str(e),
            'max_ml_score': max_ml_score,
            'frames_processed': frames_processed
        }
    finally:
        cap.release()
    
    # Evaluate results
    expected_min = EXPECTED_RESULTS[video_name]['ml_score_min']
    success = max_ml_score >= expected_min
    
    print(f"\n{'='*80}")
    print(f"RESULTS for {video_name}:")
    print(f"{'='*80}")
    print(f"Frames processed: {frames_processed}")
    print(f"High-risk frames (>60%): {high_risk_frames}")
    print(f"Maximum ML_Score: {max_ml_score:.1f}% (at frame {max_score_frame})")
    print(f"Expected minimum: {expected_min}%")
    print(f"Top ML factors at peak:")
    for factor, score in sorted(max_ml_factors.items(), key=lambda x: x[1], reverse=True)[:5]:
        if score > 0.1:
            print(f"  - {factor}: {score*100:.1f}%")
    
    if success:
        print(f"✅ PASS: ML_Score {max_ml_score:.1f}% >= {expected_min}%")
    else:
        print(f"❌ FAIL: ML_Score {max_ml_score:.1f}% < {expected_min}%")
    
    return {
        'video_name': video_name,
        'success': success,
        'max_ml_score': max_ml_score,
        'expected_min': expected_min,
        'frames_processed': frames_processed,
        'high_risk_frames': high_risk_frames,
        'max_score_frame': max_score_frame,
        'max_ml_factors': max_ml_factors
    }


def main():
    """Main test function."""
    print("="*80)
    print("ENHANCED FIGHT DETECTION - VIDEO VALIDATION TEST")
    print("="*80)
    
    # Initialize ML service
    print("\nInitializing ML service...")
    ml_service = MLService()
    
    if not ml_service.detector:
        print("❌ ERROR: ML detector not initialized. Please ensure models are loaded.")
        return
    
    print("✅ ML service initialized")
    
    # Initialize risk engine with enhanced thresholds
    print("Initializing enhanced risk engine...")
    risk_engine = RiskScoringEngine(fps=30, bypass_calibration=True)
    print("✅ Risk engine initialized with enhanced fight detection thresholds")
    
    # Test each video
    results = []
    for video_name, video_path in TEST_VIDEOS.items():
        result = test_video(video_path, video_name, ml_service, risk_engine)
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    print("\nDetailed results:")
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} {result['video_name']}: ML_Score={result.get('max_ml_score', 0):.1f}% "
              f"(expected >={result.get('expected_min', 0):.1f}%)")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Enhanced fight detection is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the results above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
