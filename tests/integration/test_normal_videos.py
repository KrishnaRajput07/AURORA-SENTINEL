
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Normal Video Testing - Validate Low Risk Scores for Normal Activities

Tests all 49 normal videos in data/sample_videos/Normal_Videos_for_Event_Recognition/
to ensure the two-tier system (ML + VLM) produces low risk scores for normal activities.

Expected Results:
- ML_Score < 30% for normal videos (no false positives)
- VLM_Score < 30% for normal videos
- Final_Score < 30% (no alerts generated)
- Pass rate > 80% (at least 40/49 videos should pass)
"""

import pytest
import asyncio
import numpy as np
import cv2
import sys
import json
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scoring_service import TwoTierScoringService
from models.scoring.risk_engine import RiskScoringEngine
from models.detection.detector import UnifiedDetector


class TestNormalVideos:
    """
    Test suite for normal video validation
    Ensures ML and VLM produce low risk scores for normal activities
    """
    
    NORMAL_VIDEO_DIR = Path('data/sample_videos/Normal_Videos_for_Event_Recognition')
    ML_THRESHOLD = 30.0  # ML scores should be below 30%
    VLM_THRESHOLD = 30.0  # VLM scores should be below 30%
    PASS_RATE_THRESHOLD = 0.80  # 80% of videos should pass
    
    @pytest.fixture(scope="class")
    def detector(self):
        """Initialize UnifiedDetector for video processing."""
        detector = UnifiedDetector()
        detector.warmup()
        return detector
    
    @pytest.fixture(scope="class")
    def risk_engine(self):
        """Initialize RiskScoringEngine."""
        return RiskScoringEngine(fps=30, bypass_calibration=True)
    
    @pytest.fixture
    def mock_ai_client(self):
        """Create a mock AI client that returns low scores for normal videos."""
        client = Mock()
        
        async def analyze_image_mock(imageData, mlScore, mlFactors, cameraId, timestamp, **kwargs):
            """Mock AI that returns low scores for normal activities."""
            # For normal videos, AI should return low scores
            return {
                'aiScore': 10.0,
                'explanation': 'Normal activity detected, no threats',
                'sceneType': 'normal',
                'confidence': 0.9,
                'provider': 'gemini'
            }
        
        client.analyze_image = AsyncMock(side_effect=analyze_image_mock)
        return client
    
    @pytest.fixture
    def scoring_service(self, risk_engine, mock_ai_client):
        """Initialize TwoTierScoringService."""
        return TwoTierScoringService(risk_engine, mock_ai_client)
    
    def get_normal_videos(self) -> List[Path]:
        """Get list of all normal video files."""
        if not self.NORMAL_VIDEO_DIR.exists():
            return []
        
        videos = sorted(self.NORMAL_VIDEO_DIR.glob('*.mp4'))
        return videos
    
    def process_video_sample(self, video_path: Path, detector: UnifiedDetector, 
                            max_frames: int = 30) -> List[Dict]:
        """
        Process a sample of frames from the video.
        
        Args:
            video_path: Path to video file
            detector: UnifiedDetector instance
            max_frames: Maximum number of frames to process
            
        Returns:
            List of detection data dicts
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Sample frames evenly throughout the video
        frame_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
        
        detections = []
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Process frame through detector
            detection_result = detector.process_frame(frame)
            
            # Store frame and detection data
            detections.append({
                'frame_number': frame_idx,
                'timestamp': frame_idx / fps if fps > 0 else frame_idx,
                'frame': frame,
                'detection_data': detection_result
            })
        
        cap.release()
        return detections
    
    @pytest.mark.asyncio
    async def test_all_normal_videos(self, detector, scoring_service):
        """
        Test all 49 normal videos to ensure low risk scores.
        
        Expected:
        - ML_Score < 30% for each video
        - VLM_Score < 30% for each video
        - Final_Score < 30% (no alerts)
        - Pass rate > 80%
        """
        print(f"\n{'='*80}")
        print(f"Testing Normal Videos for Low Risk Scores")
        print(f"{'='*80}")
        
        videos = self.get_normal_videos()
        
        if len(videos) == 0:
            pytest.skip(f"No normal videos found in {self.NORMAL_VIDEO_DIR}")
        
        print(f"\nFound {len(videos)} normal videos")
        print(f"Expected: ML_Score < {self.ML_THRESHOLD}%, VLM_Score < {self.VLM_THRESHOLD}%")
        print(f"Pass rate threshold: {self.PASS_RATE_THRESHOLD * 100}%\n")
        
        results = []
        passed_count = 0
        failed_videos = []
        
        for idx, video_path in enumerate(videos, 1):
            video_name = video_path.name
            print(f"[{idx}/{len(videos)}] Processing: {video_name}...", end=' ')
            
            try:
                # Process video sample
                detections = self.process_video_sample(video_path, detector, max_frames=30)
                
                if len(detections) == 0:
                    print("❌ SKIP (no frames)")
                    continue
                
                # Calculate scores for each frame
                ml_scores = []
                ai_scores = []
                final_scores = []
                
                for det in detections:
                    context = {
                        'camera_id': 'NORMAL-TEST',
                        'timestamp': det['timestamp'],
                        'frame_number': det['frame_number']
                    }
                    
                    scoring_result = await scoring_service.calculate_scores(
                        det['frame'],
                        det['detection_data'],
                        context
                    )
                    
                    ml_scores.append(scoring_result['ml_score'])
                    ai_scores.append(scoring_result['ai_score'])
                    final_scores.append(scoring_result['final_score'])
                
                # Calculate statistics
                max_ml = max(ml_scores)
                max_ai = max(ai_scores)
                max_final = max(final_scores)
                avg_ml = np.mean(ml_scores)
                avg_ai = np.mean(ai_scores)
                avg_final = np.mean(final_scores)
                
                # Determine pass/fail
                ml_pass = max_ml < self.ML_THRESHOLD
                ai_pass = max_ai < self.VLM_THRESHOLD
                final_pass = max_final < self.ML_THRESHOLD
                
                passed = ml_pass and ai_pass and final_pass
                
                if passed:
                    passed_count += 1
                    print(f"✅ PASS (ML: {max_ml:.1f}%, AI: {max_ai:.1f}%, Final: {max_final:.1f}%)")
                else:
                    print(f"❌ FAIL (ML: {max_ml:.1f}%, AI: {max_ai:.1f}%, Final: {max_final:.1f}%)")
                    failed_videos.append({
                        'name': video_name,
                        'max_ml': max_ml,
                        'max_ai': max_ai,
                        'max_final': max_final
                    })
                
                results.append({
                    'video': video_name,
                    'frames_processed': len(detections),
                    'max_ml_score': max_ml,
                    'max_ai_score': max_ai,
                    'max_final_score': max_final,
                    'avg_ml_score': avg_ml,
                    'avg_ai_score': avg_ai,
                    'avg_final_score': avg_final,
                    'passed': passed,
                    'ml_pass': ml_pass,
                    'ai_pass': ai_pass,
                    'final_pass': final_pass
                })
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.append({
                    'video': video_name,
                    'error': str(e),
                    'passed': False
                })
        
        # Calculate overall statistics
        total_tested = len(results)
        pass_rate = passed_count / total_tested if total_tested > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"Total videos tested: {total_tested}")
        print(f"Passed: {passed_count} ({pass_rate * 100:.1f}%)")
        print(f"Failed: {total_tested - passed_count}")
        print(f"Pass rate threshold: {self.PASS_RATE_THRESHOLD * 100}%")
        
        if failed_videos:
            print(f"\n❌ Failed Videos ({len(failed_videos)}):")
            for fv in failed_videos[:10]:  # Show first 10
                print(f"  - {fv['name']}: ML={fv['max_ml']:.1f}%, AI={fv['max_ai']:.1f}%, Final={fv['max_final']:.1f}%")
            if len(failed_videos) > 10:
                print(f"  ... and {len(failed_videos) - 10} more")
        
        # Calculate score statistics across all videos
        all_max_ml = [r['max_ml_score'] for r in results if 'max_ml_score' in r]
        all_max_ai = [r['max_ai_score'] for r in results if 'max_ai_score' in r]
        all_max_final = [r['max_final_score'] for r in results if 'max_final_score' in r]
        
        if all_max_ml:
            print(f"\nML Score Statistics:")
            print(f"  Mean: {np.mean(all_max_ml):.1f}%")
            print(f"  Max: {np.max(all_max_ml):.1f}%")
            print(f"  Min: {np.min(all_max_ml):.1f}%")
            print(f"  Std: {np.std(all_max_ml):.1f}%")
        
        if all_max_ai:
            print(f"\nAI Score Statistics:")
            print(f"  Mean: {np.mean(all_max_ai):.1f}%")
            print(f"  Max: {np.max(all_max_ai):.1f}%")
            print(f"  Min: {np.min(all_max_ai):.1f}%")
            print(f"  Std: {np.std(all_max_ai):.1f}%")
        
        if all_max_final:
            print(f"\nFinal Score Statistics:")
            print(f"  Mean: {np.mean(all_max_final):.1f}%")
            print(f"  Max: {np.max(all_max_final):.1f}%")
            print(f"  Min: {np.min(all_max_final):.1f}%")
            print(f"  Std: {np.std(all_max_final):.1f}%")
        
        # Save detailed report
        report_path = Path('tests/integration/normal_videos_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'test_date': datetime.utcnow().isoformat(),
            'total_videos': total_tested,
            'passed': passed_count,
            'failed': total_tested - passed_count,
            'pass_rate': pass_rate,
            'pass_rate_threshold': self.PASS_RATE_THRESHOLD,
            'ml_threshold': self.ML_THRESHOLD,
            'vlm_threshold': self.VLM_THRESHOLD,
            'statistics': {
                'ml_mean': float(np.mean(all_max_ml)) if all_max_ml else 0,
                'ml_max': float(np.max(all_max_ml)) if all_max_ml else 0,
                'ai_mean': float(np.mean(all_max_ai)) if all_max_ai else 0,
                'ai_max': float(np.max(all_max_ai)) if all_max_ai else 0,
                'final_mean': float(np.mean(all_max_final)) if all_max_final else 0,
                'final_max': float(np.max(all_max_final)) if all_max_final else 0,
            },
            'failed_videos': failed_videos,
            'detailed_results': results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Detailed report saved to: {report_path}")
        
        # Assert pass rate meets threshold
        assert pass_rate >= self.PASS_RATE_THRESHOLD, \
            f"Pass rate {pass_rate * 100:.1f}% is below threshold {self.PASS_RATE_THRESHOLD * 100}%"
        
        print(f"\n✅ TEST PASSED: {pass_rate * 100:.1f}% pass rate meets {self.PASS_RATE_THRESHOLD * 100}% threshold")
    
    @pytest.mark.asyncio
    async def test_sample_normal_videos_detailed(self, detector, scoring_service):
        """
        Test a sample of 5 normal videos with detailed frame-by-frame analysis.
        """
        print(f"\n{'='*80}")
        print(f"Detailed Analysis of Sample Normal Videos")
        print(f"{'='*80}")
        
        videos = self.get_normal_videos()
        
        if len(videos) == 0:
            pytest.skip(f"No normal videos found in {self.NORMAL_VIDEO_DIR}")
        
        # Select 5 videos evenly distributed
        sample_indices = np.linspace(0, len(videos) - 1, min(5, len(videos)), dtype=int)
        sample_videos = [videos[i] for i in sample_indices]
        
        for video_path in sample_videos:
            print(f"\n{'='*60}")
            print(f"Video: {video_path.name}")
            print(f"{'='*60}")
            
            # Process video
            detections = self.process_video_sample(video_path, detector, max_frames=20)
            
            print(f"Frames processed: {len(detections)}")
            print(f"\nFrame-by-frame scores:")
            print(f"{'Frame':<8} {'ML Score':<12} {'AI Score':<12} {'Final Score':<12} {'Status'}")
            print(f"{'-'*60}")
            
            for det in detections:
                context = {
                    'camera_id': 'NORMAL-TEST',
                    'timestamp': det['timestamp'],
                    'frame_number': det['frame_number']
                }
                
                scoring_result = await scoring_service.calculate_scores(
                    det['frame'],
                    det['detection_data'],
                    context
                )
                
                ml_score = scoring_result['ml_score']
                ai_score = scoring_result['ai_score']
                final_score = scoring_result['final_score']
                
                status = "✅ OK" if final_score < self.ML_THRESHOLD else "❌ HIGH"
                
                print(f"{det['frame_number']:<8} {ml_score:<12.1f} {ai_score:<12.1f} {final_score:<12.1f} {status}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
