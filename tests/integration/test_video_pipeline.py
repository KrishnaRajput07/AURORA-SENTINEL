
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Integration Tests for Video Processing Pipeline

Tests the end-to-end flow: detection → ML scoring → AI verification → alert generation.
"""

import pytest
import asyncio
import numpy as np
import cv2
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scoring_service import TwoTierScoringService
from backend.services.alert_service import AlertService
from models.scoring.risk_engine import RiskScoringEngine


class TestVideoPipelineIntegration:
    """Integration tests for the complete video processing pipeline."""
    
    @pytest.fixture
    def risk_engine(self):
        """Create a risk engine instance."""
        return RiskScoringEngine(fps=30, bypass_calibration=True)
    
    @pytest.fixture
    def mock_ai_client(self):
        """Create a mock AI client."""
        client = Mock()
        client.analyze_image = AsyncMock(return_value={
            'aiScore': 75.0,
            'explanation': 'Real fight detected with high confidence',
            'sceneType': 'real_fight',
            'confidence': 0.9,
            'provider': 'gemini'
        })
        return client
    
    @pytest.fixture
    def scoring_service(self, risk_engine, mock_ai_client):
        """Create a scoring service instance."""
        return TwoTierScoringService(risk_engine, mock_ai_client)
    
    @pytest.fixture
    def alert_service(self):
        """Create an alert service instance."""
        return AlertService()
    
    @pytest.mark.asyncio
    async def test_end_to_end_fight_detection(self, scoring_service, alert_service):
        """Test complete pipeline for fight detection."""
        # Create synthetic fight scene
        detection_data = {
            'poses': [
                {
                    'keypoints': np.array([
                        [100, 50], [95, 55], [105, 55], [90, 60], [110, 60],  # head
                        [80, 100], [120, 100],  # shoulders
                        [70, 120], [130, 120],  # elbows
                        [60, 80], [140, 80],  # wrists (raised)
                        [85, 200], [115, 200],  # hips
                        [80, 300], [120, 300],  # knees
                        [50, 400], [150, 400]  # ankles (wide stance)
                    ]),
                    'confidence': np.array([0.9] * 17),
                    'bbox': [50, 50, 150, 400],
                    'track_id': 1
                },
                {
                    'keypoints': np.array([
                        [200, 50], [195, 55], [205, 55], [190, 60], [210, 60],
                        [180, 100], [220, 100],
                        [170, 120], [230, 120],
                        [160, 80], [240, 80],
                        [185, 200], [215, 200],
                        [180, 300], [220, 300],
                        [150, 400], [250, 400]
                    ]),
                    'confidence': np.array([0.9] * 17),
                    'bbox': [150, 50, 250, 400],
                    'track_id': 2
                }
            ],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {
            'camera_id': 'CAM-01',
            'timestamp': 0.0,
            'location': 'Test Location'
        }
        
        # Step 1: Calculate scores
        scoring_result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Verify scoring
        assert scoring_result['ml_score'] > 0
        assert scoring_result['final_score'] > 0
        
        # Step 2: Generate alert if needed
        if scoring_result['should_alert']:
            alert = alert_service.generate_alert(scoring_result, context)
            
            # Verify alert
            assert alert['level'] in ['critical', 'high', 'medium', 'low']
            assert alert['ml_score'] == scoring_result['ml_score']
            assert alert['ai_score'] == scoring_result['ai_score']
            assert alert['final_score'] == scoring_result['final_score']
            assert alert['detection_source'] == scoring_result['detection_source']
    
    @pytest.mark.asyncio
    async def test_boxing_discrimination(self, scoring_service, alert_service):
        """Test that boxing is correctly identified by AI layer."""
        # Mock AI to identify boxing
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': 25.0,
            'explanation': 'Controlled sparring activity in boxing ring',
            'sceneType': 'boxing',
            'confidence': 0.85,
            'provider': 'gemini'
        })
        
        # Create detection data with fighting poses
        detection_data = {
            'poses': [
                {
                    'keypoints': np.random.rand(17, 2) * 100,
                    'confidence': np.array([0.9] * 17),
                    'bbox': [50, 50, 150, 400],
                    'track_id': 1
                }
            ],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'CAM-01', 'timestamp': 0.0, 'location': 'Gym'}
        
        # Calculate scores
        scoring_result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # ML should detect combat (>60%), AI should identify as boxing (<30%)
        # This tests the two-tier discrimination
        if scoring_result['ml_score'] > 60:
            assert scoring_result['ai_scene_type'] == 'boxing'
            assert scoring_result['ai_score'] < 30
    
    @pytest.mark.asyncio
    async def test_alert_metadata_persistence(self, scoring_service, alert_service):
        """Test that alert metadata is correctly populated for database storage."""
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {
            'camera_id': 'CAM-01',
            'timestamp': datetime.utcnow(),
            'location': 'Test Location',
            'video_clip_path': '/path/to/clip.mp4'
        }
        
        # Mock high ML score
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(75.0, {'aggressive_posture': 0.8})):
            scoring_result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Generate alert
        alert = alert_service.generate_alert(scoring_result, context)
        
        # Verify all database fields are present
        assert 'ml_score' in alert
        assert 'ai_score' in alert
        assert 'final_score' in alert
        assert 'detection_source' in alert
        assert 'ai_explanation' in alert
        assert 'ai_scene_type' in alert
        assert 'ai_confidence' in alert
        assert 'timestamp' in alert
        assert 'camera_id' in alert
        assert 'location' in alert
        assert 'risk_factors' in alert
        assert 'status' in alert
    
    @pytest.mark.asyncio
    async def test_error_handling_ai_failure(self, scoring_service, alert_service):
        """Test graceful degradation when AI fails."""
        # Mock AI to fail
        scoring_service.ai_client.analyze_image = AsyncMock(side_effect=Exception("AI service unavailable"))
        
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'CAM-01', 'timestamp': 0.0}
        
        # Mock high ML score to trigger AI
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(75.0, {})):
            scoring_result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Should fall back to ML only
        assert scoring_result['ml_score'] == 75.0
        assert scoring_result['ai_score'] == 0.0
        assert scoring_result['final_score'] == 75.0
        assert scoring_result['detection_source'] == 'ml'
        assert 'error' in scoring_result['ai_explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_frame_processing(self, scoring_service):
        """Test that multiple frames can be processed concurrently."""
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
        contexts = [{'camera_id': f'CAM-{i}', 'timestamp': i * 0.033} for i in range(5)]
        
        # Process frames concurrently
        tasks = [
            scoring_service.calculate_scores(frame, detection_data, context)
            for frame, context in zip(frames, contexts)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all frames processed
        assert len(results) == 5
        for result in results:
            assert 'ml_score' in result
            assert 'final_score' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
