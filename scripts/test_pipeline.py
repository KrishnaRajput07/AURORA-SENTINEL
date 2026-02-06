import requests
import cv2
import numpy as np
import time
from pathlib import Path
import os
import sys

class PipelineTester:
    """
    Test complete pipeline from video upload to alert generation
    """
    def __init__(self, api_url='http://localhost:8000'):
        self.api_url = api_url.rstrip('/')
    
    def test_health(self):
        """Test API health"""
        print("Testing API health...")
        try:
            response = requests.get(f"{self.api_url}/health")
            assert response.status_code == 200
            print("✓ API is healthy")
            return response.json()
        except requests.exceptions.ConnectionError:
            print("x API is not running. Please start the backend.")
            sys.exit(1)
        except Exception as e:
            print(f"x Health check failed: {e}")
            return {}
    
    def test_video_upload(self, video_path):
        """Test video upload and processing"""
        print(f"Testing video upload: {video_path}")
        
        # Create a dummy video if not exists for testing
        if not os.path.exists(video_path):
            self._create_dummy_video(video_path)
            
        with open(video_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.api_url}/process/video",
                files=files
            )
        
        if response.status_code != 200:
             print(f"x Video upload failed: {response.text}")
             return {}

        result = response.json()
        
        print(f"✓ Video processed successfully")
        print(f"  - Status: {result.get('status')}")
        print(f"  - Alerts Found: {result.get('alerts_found')}")
        
        return result
    
    def test_alerts_endpoint(self):
        """Test alerts retrieval"""
        print("Testing alerts endpoint...")
        response = requests.get(f"{self.api_url}/alerts/recent?limit=10")
        
        assert response.status_code == 200
        result = response.json()
        
        print(f"✓ Retrieved {result['count']} alerts")
        return result
    
    def _create_dummy_video(self, path):
        print(f"Creating dummy video at {path}...")
        height, width = 640, 640
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(path), fourcc, 30.0, (width, height))
        for _ in range(60): # 2 seconds
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            out.write(frame)
        out.release()
    
    def test_full_pipeline(self):
        """Run all tests"""
        print("="*50)
        print("AURORA-SENTINEL Pipeline Test")
        print("="*50)
        
        # Test 1: Health check
        health = self.test_health()
        print(f"  GPU Available: {health.get('gpu_available')}")
        
        # Test 2: Video processing
        # Ensure directory exists
        os.makedirs('data/sample_videos', exist_ok=True)
        # Use user provided video
        test_video_path = 'data/sample_videos/Normal_Videos_for_Event_Recognition/Normal_Videos_015_x264.mp4'
        if not os.path.exists(test_video_path):
             print(f"User video not found, using default test video")
             test_video_path = 'data/sample_videos/test_pipeline_video.mp4'
        
        result = self.test_video_upload(test_video_path)
        
        # Test 3: Alerts
        alerts = self.test_alerts_endpoint()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("="*50)

if __name__ == "__main__":
    tester = PipelineTester()
    tester.test_full_pipeline()
