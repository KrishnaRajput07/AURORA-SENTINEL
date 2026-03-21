
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Unit Tests for Two-Tier Scoring Service

Tests the TwoTierScoringService class and score aggregation logic.
"""

import pytest
import asyncio
import numpy as np
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scoring_service import TwoTierScoringService
from models.scoring.risk_engine import RiskScoringEngine


class TestTwoTierScoringService:
    """Test suite for TwoTierScoringService."""
    
    @pytest.fixture
    def risk_engine(self):
        """Create a risk engine instance for testing."""
        return RiskScoringEngine(fps=30, bypass_calibration=True)
    
    @pytest.fixture
    def mock_ai_client(self):
        """Create a mock AI client."""
        client = Mock()
        client.analyze_image = AsyncMock(return_value={
            'aiScore': 75.0,
            'explanation': 'Real fight detected',
            'sceneType': 'real_fight',
            'confidence': 0.9,
            'provider': 'gemini'
        })
        return client
    
    @pytest.fixture
    def scoring_service(self, risk_engine, mock_ai_client):
        """Create a scoring service instance."""
        return TwoTierScoringService(risk_engine, mock_ai_client)
    
    def test_initialization(self, scoring_service):
        """Test service initialization."""
        assert scoring_service.alert_threshold == 60.0
        assert scoring_service.risk_engine is not None
        assert scoring_service.ai_client is not None
    
    @pytest.mark.asyncio
    async def test_calculate_scores_ml_only(self, scoring_service):
        """Test score calculation with ML only (AI always runs)."""
        # Create mock detection data
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock risk engine to return low score
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(45.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions - AI always runs, so we get weighted score
        assert result['ml_score'] == 45.0
        assert result['ai_score'] == 75.0  # From mock AI client
        # Weighted: 0.3 * 45 + 0.7 * 75 = 13.5 + 52.5 = 66.0
        assert result['final_score'] == 66.0
        assert result['scoring_method'] == 'weighted'
        assert result['confidence'] == 0.8
        assert result['should_alert'] is True  # 66 > 60 threshold
    
    @pytest.mark.asyncio
    async def test_calculate_scores_ml_triggers_ai(self, scoring_service):
        """Test score calculation when ML triggers AI verification."""
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock risk engine to return high score
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(75.0, {'aggressive_posture': 0.8})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert result['ml_score'] == 75.0
        assert result['ai_score'] == 75.0  # From mock AI client
        assert result['final_score'] == 75.0
        assert result['detection_source'] == 'both'
        assert result['should_alert'] is True
    
    @pytest.mark.asyncio
    async def test_calculate_scores_ai_timeout(self, scoring_service):
        """Test score calculation when AI times out."""
        detection_data = {
            'poses': [],
            'objects': [],
            'weapons': []
        }
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock AI client to raise timeout
        scoring_service.ai_client.analyze_image = AsyncMock(side_effect=asyncio.TimeoutError())
        
        # Mock risk engine to return high score
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(75.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions - should fall back to ML only
        assert result['ml_score'] == 75.0
        assert result['ai_score'] == 0.0
        assert result['final_score'] == 75.0
        assert result['detection_source'] == 'ml'
        assert 'error' in result['ai_explanation'].lower() or 'timeout' in result['ai_explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_final_score_is_weighted(self, scoring_service):
        """Test that final score uses weighted calculation (0.3*ML + 0.7*AI)."""
        test_cases = [
            # (ml_score, ai_score, expected_final)
            (70.0, 50.0, 56.0),   # 0.3*70 + 0.7*50 = 21 + 35 = 56
            (50.0, 70.0, 64.0),   # 0.3*50 + 0.7*70 = 15 + 49 = 64
            (60.0, 60.0, 60.0),   # 0.3*60 + 0.7*60 = 18 + 42 = 60
            (30.0, 80.0, 65.0),   # 0.3*30 + 0.7*80 = 9 + 56 = 65
            (90.0, 20.0, 41.0),   # 0.3*90 + 0.7*20 = 27 + 14 = 41
        ]
        
        for ml_score, ai_score, expected_final in test_cases:
            # Mock both scores
            with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(ml_score, {})):
                scoring_service.ai_client.analyze_image = AsyncMock(return_value={
                    'aiScore': ai_score,
                    'explanation': 'Test',
                    'sceneType': 'normal',
                    'confidence': 0.5,
                    'provider': 'test'
                })
                
                result = await scoring_service.calculate_scores(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    {'poses': [], 'objects': [], 'weapons': []},
                    {'camera_id': 'test', 'timestamp': 0.0}
                )
                
                assert result['final_score'] == expected_final, \
                    f"Expected {expected_final}, got {result['final_score']} for ML={ml_score}, AI={ai_score}"
                assert result['scoring_method'] == 'weighted'
                assert result['confidence'] == 0.8
    
    @pytest.mark.asyncio
    async def test_detection_source_logic(self, scoring_service):
        """Test detection source determination."""
        test_cases = [
            (70.0, 70.0, 'both'),   # Both exceed threshold
            (70.0, 50.0, 'ml'),     # Only ML exceeds
            (50.0, 70.0, 'ai'),     # Only AI exceeds
            (50.0, 50.0, 'none'),   # Neither exceeds
        ]
        
        for ml_score, ai_score, expected_source in test_cases:
            with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(ml_score, {})):
                scoring_service.ai_client.analyze_image = AsyncMock(return_value={
                    'aiScore': ai_score,
                    'explanation': 'Test',
                    'sceneType': 'normal',
                    'confidence': 0.5,
                    'provider': 'test'
                })
                
                result = await scoring_service.calculate_scores(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    {'poses': [], 'objects': [], 'weapons': []},
                    {'camera_id': 'test', 'timestamp': 0.0}
                )
                
                assert result['detection_source'] == expected_source, \
                    f"Expected {expected_source}, got {result['detection_source']} for ML={ml_score}, AI={ai_score}"
    
    @pytest.mark.asyncio
    async def test_ai_unavailable_fallback(self, scoring_service):
        """Test fallback when AI is unavailable: Final = ML, confidence 0.3."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock AI client to return None for aiScore
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': None,
            'explanation': 'AI model unavailable',
            'sceneType': 'normal',
            'confidence': 0.0,
            'provider': 'none'
        })
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(75.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert result['ml_score'] == 75.0
        assert result['ai_score'] == 0.0  # Converted from None
        assert result['final_score'] == 75.0  # Final = ML
        assert result['scoring_method'] == 'ml_only'
        assert result['confidence'] == 0.3
        assert result['should_alert'] is True
    
    @pytest.mark.asyncio
    async def test_ml_unavailable_fallback(self, scoring_service):
        """Test fallback when ML is unavailable: Final = AI, confidence 0.6."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock risk engine to return None
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(None, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert result['ml_score'] == 0.0  # Converted from None
        assert result['ai_score'] == 75.0  # From mock AI client
        assert result['final_score'] == 75.0  # Final = AI
        assert result['scoring_method'] == 'ai_only'
        assert result['confidence'] == 0.6
        assert result['should_alert'] is True
    
    @pytest.mark.asyncio
    async def test_nemotron_verification_included(self, scoring_service):
        """Test that Nemotron verification details are included in response."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock AI client to return Nemotron verification
        nemotron_data = {
            'verification_score': 0.75,
            'verified': True,
            'agreement': True,
            'recommended_score': 80,
            'nemotron_scene_type': 'real_fight',
            'confidence': 0.9
        }
        
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': 80.0,
            'ai_score_raw': 85.0,
            'explanation': 'Real fight detected',
            'sceneType': 'real_fight',
            'confidence': 0.9,
            'provider': 'qwen2vl',
            'nemotron_verification': nemotron_data
        })
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(70.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert 'nemotron_verification' in result
        assert result['nemotron_verification'] == nemotron_data
        assert result['ai_score'] == 80.0  # Nemotron-adjusted
        assert result['scoring_method'] == 'weighted'
    
    @pytest.mark.asyncio
    async def test_no_hardcoded_multipliers(self, scoring_service):
        """Test that no hardcoded multipliers (like ml_score * 0.6) are used."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Test AI unavailable case - should NOT use ml_score * 0.6
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': None,
            'explanation': 'AI unavailable',
            'sceneType': 'normal',
            'confidence': 0.0,
            'provider': 'none'
        })
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(50.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Should be 50.0, NOT 30.0 (50 * 0.6)
        assert result['final_score'] == 50.0
        assert result['scoring_method'] == 'ml_only'
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, scoring_service, caplog):
        """Test that component scores are logged for audit."""
        import logging
        caplog.set_level(logging.INFO)
        
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(60.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Check that audit logs are present
        audit_logs = [record.message for record in caplog.records if '[AUDIT]' in record.message]
        assert len(audit_logs) > 0
        assert 'ML_Score' in audit_logs[0]
        assert 'AI_Score' in audit_logs[0]
        assert 'Final' in audit_logs[0]
    
    @pytest.mark.asyncio
    async def test_both_scores_unavailable(self, scoring_service):
        """Test fallback when both ML and AI are unavailable."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock both to return None
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': None,
            'explanation': 'AI unavailable',
            'sceneType': 'normal',
            'confidence': 0.0,
            'provider': 'none'
        })
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(None, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert result['ml_score'] == 0.0
        assert result['ai_score'] == 0.0
        assert result['final_score'] == 0.0
        assert result['scoring_method'] == 'none'
        assert result['confidence'] == 0.0
        assert result['should_alert'] is False
    
    @pytest.mark.asyncio
    async def test_weighted_with_nemotron_adjustment(self, scoring_service):
        """Test that Nemotron-adjusted AI score is used in weighted calculation."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Mock AI to return Nemotron-adjusted score
        # Raw Qwen score: 85, Nemotron adjusted: 80
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': 80.0,  # Nemotron-adjusted
            'ai_score_raw': 85.0,  # Original Qwen score
            'explanation': 'Real fight detected, verified by Nemotron',
            'sceneType': 'real_fight',
            'confidence': 0.9,
            'provider': 'qwen2vl',
            'nemotron_verification': {
                'verification_score': 0.75,
                'verified': True,
                'agreement': True,
                'recommended_score': 80,
                'nemotron_scene_type': 'real_fight',
                'confidence': 0.9
            }
        })
        
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(70.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
        
        # Assertions
        assert result['ml_score'] == 70.0
        assert result['ai_score'] == 80.0  # Nemotron-adjusted, not raw 85
        # Weighted: 0.3 * 70 + 0.7 * 80 = 21 + 56 = 77.0
        assert result['final_score'] == 77.0
        assert result['scoring_method'] == 'weighted'
        assert result['confidence'] == 0.8
        assert 'nemotron_verification' in result
        assert result['nemotron_verification']['verified'] is True
    
    @pytest.mark.asyncio
    async def test_scoring_method_metadata(self, scoring_service):
        """Test that scoring_method metadata is correctly set for all scenarios."""
        detection_data = {'poses': [], 'objects': [], 'weapons': []}
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        context = {'camera_id': 'test-cam', 'timestamp': 0.0}
        
        # Test weighted
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(60.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
            assert result['scoring_method'] == 'weighted'
        
        # Test ml_only
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': None,
            'explanation': 'AI unavailable',
            'sceneType': 'normal',
            'confidence': 0.0,
            'provider': 'none'
        })
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(60.0, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
            assert result['scoring_method'] == 'ml_only'
        
        # Test ai_only
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': 75.0,
            'explanation': 'Real fight',
            'sceneType': 'real_fight',
            'confidence': 0.9,
            'provider': 'qwen2vl'
        })
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(None, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
            assert result['scoring_method'] == 'ai_only'
        
        # Test none
        scoring_service.ai_client.analyze_image = AsyncMock(return_value={
            'aiScore': None,
            'explanation': 'AI unavailable',
            'sceneType': 'normal',
            'confidence': 0.0,
            'provider': 'none'
        })
        with patch.object(scoring_service.risk_engine, 'calculate_risk', return_value=(None, {})):
            result = await scoring_service.calculate_scores(frame, detection_data, context)
            assert result['scoring_method'] == 'none'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
