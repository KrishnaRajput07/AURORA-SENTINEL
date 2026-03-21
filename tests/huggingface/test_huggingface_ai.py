
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""Test HuggingFace AI integration"""
import sys
import asyncio
import cv2
import numpy as np
import base64
import aiohttp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.detection.detector import UnifiedDetector
from models.scoring.risk_engine import RiskScoringEngine
from backend.services.scoring_service import TwoTierScoringService


class HuggingFaceAIClient:
    """Test client for HuggingFace AI service."""
    
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
        """Call the AI service."""
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


async def test_huggingface():
    """Test HuggingFace AI with different video types."""
    
    print("="*80)
    print("HUGGINGFACE AI INTEGRATION TEST")
    print("="*80)
    
    # Initialize components
    print("\nInitializing detector and risk engine...")
    detector = UnifiedDetector()
    detector.warmup()
    risk_engine = RiskScoringEngine(fps=30, bypass_calibration=True)
    
    # Test videos
    test_videos = {
        'fight': 'storage/temp/raw_1772268166.802879_4rth.mp4',
        'boxing': 'storage/temp/raw_1772268625.365338_scr9-231238~2sdddsd.mp4',
        'normal': 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_877_x264.mp4',
    }
    
    async with HuggingFaceAIClient() as ai_client:
        # Test connection
        print("\nTesting AI service connection...")
        try:
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            result = await ai_client.analyze_image(
                imageData=test_frame,
                mlScore=10.0,
                mlFactors={},
                cameraId='TEST',
                timestamp=0
            )
            print(f"✅ AI service connected: {result['provider']}")
        except Exception as e:
            print(f"❌ AI service connection failed: {e}")
            return
        
        # Create scoring service
        scoring_service = TwoTierScoringService(risk_engine, ai_client)
        
        # Test each video type
        for video_type, video_path in test_videos.items():
            if not Path(video_path).exists():
                print(f"\n⚠️  Skipping {video_type}: file not found")
                continue
            
            print(f"\n{'='*70}")
            print(f"Testing: {video_type.upper()}")
            print(f"Path: {video_path}")
            print(f"{'='*70}")
            
            # Load first frame
            vidcap = cv2.VideoCapture(video_path)
            success, frame = vidcap.read()
            vidcap.release()
            
            if not success:
                print(f"❌ Failed to load video")
                continue
            
            print(f"Frame loaded: {frame.shape}")
            
            # Process frame
            detection_result = detector.process_frame(frame)
            print(f"Detected: {len(detection_result['poses'])} poses")
            
            # Calculate scores
            context = {
                'camera_id': f'TEST-{video_type}',
                'timestamp': 0,
                'frame_number': 0
            }
            
            try:
                scoring_result = await scoring_service.calculate_scores(
                    frame,
                    detection_result,
                    context
                )
                
                print(f"\n📊 RESULTS:")
                print(f"  ML Score:       {scoring_result['ml_score']:.1f}%")
                print(f"  AI Score:       {scoring_result['ai_score']:.1f}%")
                print(f"  Final Score:    {scoring_result['final_score']:.1f}%")
                print(f"  Scene Type:     {scoring_result['ai_scene_type']}")
                print(f"  AI Confidence:  {scoring_result['ai_confidence']:.2f}")
                print(f"  AI Provider:    {scoring_result['ai_provider']}")
                print(f"  AI Explanation: {scoring_result['ai_explanation']}")
                print(f"  Should Alert:   {'🚨 YES' if scoring_result['should_alert'] else '✅ NO'}")
                
                # Validate results
                if video_type == 'fight':
                    if scoring_result['ai_score'] > 50:
                        print(f"\n✅ PASS: AI detected fight (score > 50%)")
                    else:
                        print(f"\n⚠️  WARNING: AI score low for fight video")
                
                elif video_type == 'boxing':
                    if scoring_result['ai_score'] < 50:
                        print(f"\n✅ PASS: AI discriminated boxing (score < 50%)")
                    else:
                        print(f"\n⚠️  WARNING: AI score high for boxing video")
                
                elif video_type == 'normal':
                    if scoring_result['final_score'] < 40:
                        print(f"\n✅ PASS: Low final score for normal video")
                    else:
                        print(f"\n⚠️  WARNING: Final score high for normal video")
                
            except Exception as e:
                print(f"\n❌ Error processing frame: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_huggingface())
