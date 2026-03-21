
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Comprehensive Real AI Test with Real Videos

Tests the complete two-tier system with REAL AI service:
1. Loads real videos using efficient sampling
2. Processes through ML detection
3. Calls REAL AI service for verification
4. Uses weighted confidence aggregation
5. Validates results

Requirements: AI service must be running on http://localhost:3000
"""

import pytest
import asyncio
import numpy as np
import cv2
import sys
import json
import base64
import aiohttp
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scoring_service import TwoTierScoringService
from models.scoring.risk_engine import RiskScoringEngine
from models.detection.detector import UnifiedDetector


def load_video_frames(video_path: str, max_frames: int = 20, interval_ms: int = 250) -> List[np.ndarray]:
    """
    Load video frames efficiently using time-based sampling.
    
    Args:
        video_path: Path to video file
        max_frames: Maximum number of frames to extract
        interval_ms: Interval between frames in milliseconds (default: 250ms = 4 FPS)
        
    Returns:
        List of frames as numpy arrays (BGR format for OpenCV)
    """
    vidcap = cv2.VideoCapture(video_path)
    if not vidcap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    count = 0
    frames = []
    success = True
    
    while success and count < max_frames:
        # Set position to specific timestamp
        vidcap.set(cv2.CAP_PROP_POS_MSEC, (count * interval_ms))
        success, frame = vidcap.read()
        
        if success and frame is not None:
            # Keep original size for detection (don't resize to 224x224)
            # Our detector works better with original resolution
            frames.append(frame)
        
        count += 1
    
    vidcap.release()
    return frames


class RealAIClient:
    """Real AI client that calls the actual AI service."""
    
    def __init__(self, base_url='http://localhost:3001'):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_image(self, imageData, mlScore, mlFactors, cameraId, timestamp, **kwargs):
        """Call the real AI service."""
        # Convert numpy array to base64 if needed
        if isinstance(imageData, np.ndarray):
            _, buffer = cv2.imencode('.jpg', imageData)
            imageData = base64.b64encode(buffer).decode('utf-8')
        
        payload = {
            'imageData': imageData,
            'mlScore': mlScore,
            'mlFactors': mlFactors,
            'cameraId': cameraId,
            'timestamp': timestamp
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                f'{self.base_url}/analyze',
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"AI service error: {response.status} - {error_text}")
        except aiohttp.ClientConnectorError:
            raise Exception(f"Cannot connect to AI service at {self.base_url}. Is it running?")


class TestRealAIComprehensive:
    """Comprehensive test suite for real AI with real videos."""
    
    TEST_VIDEOS = {
        'fight_1': 'storage/temp/raw_1772268166.802879_4rth.mp4',
        'fight_2': 'storage/temp/raw_1772268210.415873_5th.mp4',
        'boxing': 'storage/temp/raw_1772268625.365338_scr9-231238~2sdddsd.mp4',
        'normal_1': 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_050_x264.mp4',
        'normal_2': 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_606_x264.mp4',
        'normal_3': 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_877_x264.mp4',
    }
    
    @pytest.fixture(scope="class")
    def detector(self):
        """Initialize UnifiedDetector."""
        detector = UnifiedDetector()
        detector.warmup()
        return detector
    
    @pytest.fixture(scope="class")
    def risk_engine(self):
        """Initialize RiskScoringEngine."""
        return RiskScoringEngine(fps=30, bypass_calibration=True)
    
    @pytest.mark.asyncio
    async def test_comprehensive_real_ai_validation(self, detector, risk_engine):
        """
        Comprehensive test with real AI on all video types.
        
        Tests:
        1. Fight videos → High ML + High AI = High Final (ALERT)
        2. Boxing videos → High ML + Low AI = Medium Final (NO ALERT with weighted)
        3. Normal videos → Low ML + Low AI = Low Final (NO ALERT)
        """
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE REAL AI VALIDATION TEST")
        print(f"{'='*80}")
        
        # Check if AI service is available
        async with RealAIClient() as ai_client:
            try:
                # Test connection
                test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                await ai_client.analyze_image(
                    imageData=test_frame,
                    mlScore=10.0,
                    mlFactors={},
                    cameraId='TEST',
                    timestamp=0
                )
                print("✅ AI service is running and accessible\n")
            except Exception as e:
                pytest.skip(f"AI service not available: {e}")
            
            # Create scoring service with real AI
            scoring_service = TwoTierScoringService(risk_engine, ai_client)
            
            results = {}
            
            for video_name, video_path in self.TEST_VIDEOS.items():
                if not Path(video_path).exists():
                    print(f"⚠️  Skipping {video_name}: file not found")
                    continue
                
                print(f"\n{'='*70}")
                print(f"Testing: {video_name}")
                print(f"Path: {video_path}")
                print(f"{'='*70}")
                
                # Load video frames
                try:
                    frames = load_video_frames(video_path, max_frames=10, interval_ms=500)
                    print(f"Loaded {len(frames)} frames")
                except Exception as e:
                    print(f"❌ Error loading video: {e}")
                    continue
                
                # Process frames
                ml_scores = []
                ai_scores = []
                final_scores = []
                scene_types = []
                confidences = []
                
                for idx, frame in enumerate(frames):
                    print(f"\n  Frame {idx + 1}/{len(frames)}:")
                    
                    # Run detection
                    detection_result = detector.process_frame(frame)
                    
                    # Calculate scores with real AI
                    context = {
                        'camera_id': f'TEST-{video_name}',
                        'timestamp': idx * 0.5,  # 500ms intervals
                        'frame_number': idx
                    }
                    
                    try:
                        scoring_result = await scoring_service.calculate_scores(
                            frame,
                            detection_result,
                            context
                        )
                        
                        ml_score = scoring_result['ml_score']
                        ai_score = scoring_result['ai_score']
                        final_score = scoring_result['final_score']
                        scene_type = scoring_result['ai_scene_type']
                        confidence = scoring_result['ai_confidence']
                        
                        ml_scores.append(ml_score)
                        ai_scores.append(ai_score)
                        final_scores.append(final_score)
                        scene_types.append(scene_type)
                        confidences.append(confidence)
                        
                        print(f"    ML Score: {ml_score:.1f}%")
                        print(f"    AI Score: {ai_score:.1f}%")
                        print(f"    Final Score: {final_score:.1f}%")
                        print(f"    Scene Type: {scene_type}")
                        print(f"    AI Confidence: {confidence:.2f}")
                        
                        if scoring_result['should_alert']:
                            print(f"    🚨 ALERT TRIGGERED!")
                        
                    except Exception as e:
                        print(f"    ❌ Error processing frame: {e}")
                        continue
                
                # Calculate statistics
                if ml_scores:
                    max_ml = max(ml_scores)
                    max_ai = max(ai_scores)
                    max_final = max(final_scores)
                    avg_ml = np.mean(ml_scores)
                    avg_ai = np.mean(ai_scores)
                    avg_final = np.mean(final_scores)
                    avg_confidence = np.mean(confidences)
                    
                    results[video_name] = {
                        'max_ml': max_ml,
                        'max_ai': max_ai,
                        'max_final': max_final,
                        'avg_ml': avg_ml,
                        'avg_ai': avg_ai,
                        'avg_final': avg_final,
                        'avg_confidence': avg_confidence,
                        'scene_types': list(set(scene_types)),
                        'frames_processed': len(ml_scores)
                    }
                    
                    print(f"\n  {'='*60}")
                    print(f"  SUMMARY for {video_name}:")
                    print(f"  {'='*60}")
                    print(f"  Frames processed: {len(ml_scores)}")
                    print(f"  ML Score:    Max={max_ml:.1f}%, Avg={avg_ml:.1f}%")
                    print(f"  AI Score:    Max={max_ai:.1f}%, Avg={avg_ai:.1f}%")
                    print(f"  Final Score: Max={max_final:.1f}%, Avg={avg_final:.1f}%")
                    print(f"  AI Confidence: Avg={avg_confidence:.2f}")
                    print(f"  Scene Types: {set(scene_types)}")
                    
                    # Validate based on video type
                    if 'fight' in video_name:
                        print(f"\n  ✅ Expected: High ML + High AI = High Final")
                        if max_ai > 50:
                            print(f"  ✅ PASS: AI detected fight (AI={max_ai:.1f}%)")
                        else:
                            print(f"  ⚠️  WARNING: AI score low (AI={max_ai:.1f}%)")
                    
                    elif 'boxing' in video_name:
                        print(f"\n  ✅ Expected: High ML + Low AI = Medium Final")
                        if max_ai < 50:
                            print(f"  ✅ PASS: AI discriminated boxing (AI={max_ai:.1f}%)")
                        else:
                            print(f"  ⚠️  WARNING: AI score high (AI={max_ai:.1f}%)")
                    
                    elif 'normal' in video_name:
                        print(f"\n  ✅ Expected: Low ML + Low AI = Low Final")
                        if max_final < 40:
                            print(f"  ✅ PASS: Low final score (Final={max_final:.1f}%)")
                        else:
                            print(f"  ⚠️  WARNING: Final score high (Final={max_final:.1f}%)")
            
            # Generate comprehensive report
            print(f"\n{'='*80}")
            print(f"COMPREHENSIVE TEST RESULTS")
            print(f"{'='*80}")
            
            for video_name, stats in results.items():
                print(f"\n{video_name}:")
                print(f"  Max Scores: ML={stats['max_ml']:.1f}%, AI={stats['max_ai']:.1f}%, Final={stats['max_final']:.1f}%")
                print(f"  Avg Scores: ML={stats['avg_ml']:.1f}%, AI={stats['avg_ai']:.1f}%, Final={stats['avg_final']:.1f}%")
                print(f"  AI Confidence: {stats['avg_confidence']:.2f}")
                print(f"  Scene Types: {stats['scene_types']}")
            
            # Save report
            report_path = Path('tests/integration/real_ai_comprehensive_report.json')
            report = {
                'test_date': datetime.utcnow().isoformat(),
                'ai_service': 'http://localhost:3000',
                'weighted_confidence': True,
                'results': results
            }
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📊 Detailed report saved to: {report_path}")
            
            # Validate key expectations
            print(f"\n{'='*80}")
            print(f"VALIDATION")
            print(f"{'='*80}")
            
            # Check if we have fight video results
            fight_results = [v for k, v in results.items() if 'fight' in k]
            if fight_results:
                max_fight_ai = max(r['max_ai'] for r in fight_results)
                print(f"✅ Fight videos: Max AI score = {max_fight_ai:.1f}%")
                if max_fight_ai > 50:
                    print(f"   ✅ PASS: AI can detect fights!")
                else:
                    print(f"   ⚠️  WARNING: AI scores low on fights")
            
            # Check if we have normal video results
            normal_results = [v for k, v in results.items() if 'normal' in k]
            if normal_results:
                max_normal_final = max(r['max_final'] for r in normal_results)
                print(f"✅ Normal videos: Max Final score = {max_normal_final:.1f}%")
                if max_normal_final < 40:
                    print(f"   ✅ PASS: Weighted confidence reduces false positives!")
                else:
                    print(f"   ⚠️  WARNING: Final scores still high on normal videos")
            
            print(f"\n{'='*80}")
            print(f"TEST COMPLETE")
            print(f"{'='*80}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
