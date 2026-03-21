
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Unit Tests for Alert Service

Tests the AlertService class and alert generation logic.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.alert_service import AlertService


class TestAlertService:
    """Test suite for AlertService."""
    
    @pytest.fixture
    def alert_service(self):
        """Create an alert service instance."""
        return AlertService()
    
    def test_initialization(self, alert_service):
        """Test service initialization."""
        assert alert_service is not None
    
    def test_generate_alert_critical_level(self, alert_service):
        """Test alert generation for critical level (>70%)."""
        scoring_result = {
            'ml_score': 75.0,
            'ai_score': 80.0,
            'final_score': 80.0,
            'ml_factors': {'aggressive_posture': 0.8, 'proximity_violation': 0.7},
            'ai_explanation': 'Real fight detected',
            'ai_scene_type': 'real_fight',
            'ai_confidence': 0.9,
            'detection_source': 'both',
            'should_alert': True
        }
        
        context = {
            'timestamp': datetime.utcnow(),
            'camera_id': 'CAM-01',
            'location': 'Main Hall'
        }
        
        alert = alert_service.generate_alert(scoring_result, context)
        
        # Assertions
        assert alert['level'] == 'critical'
        assert alert['color'] == 'red'
        assert alert['ml_score'] == 75.0
        assert alert['ai_score'] == 80.0
        assert alert['final_score'] == 80.0
        assert alert['detection_source'] == 'both'
        assert 'Both ML and AI detected threat' in alert['message']
    
    def test_generate_alert_high_level(self, alert_service):
        """Test alert generation for high level (50-70%)."""
        scoring_result = {
            'ml_score': 65.0,
            'ai_score': 55.0,
            'final_score': 65.0,
            'ml_factors': {'aggressive_posture': 0.6},
            'ai_explanation': 'Elevated activity',
            'ai_scene_type': 'normal',
            'ai_confidence': 0.7,
            'detection_source': 'ml',
            'should_alert': True
        }
        
        context = {
            'timestamp': datetime.utcnow(),
            'camera_id': 'CAM-02',
            'location': 'Parking Lot'
        }
        
        alert = alert_service.generate_alert(scoring_result, context)
        
        assert alert['level'] == 'high'
        assert alert['color'] == 'orange'
        assert alert['final_score'] == 65.0
    
    def test_generate_alert_medium_level(self, alert_service):
        """Test alert generation for medium level (30-50%)."""
        scoring_result = {
            'ml_score': 40.0,
            'ai_score': 35.0,
            'final_score': 40.0,
            'ml_factors': {'crowd_density': 0.5},
            'ai_explanation': 'Normal activity',
            'ai_scene_type': 'normal',
            'ai_confidence': 0.8,
            'detection_source': 'none',
            'should_alert': False
        }
        
        context = {
            'timestamp': datetime.utcnow(),
            'camera_id': 'CAM-03',
            'location': 'Entrance'
        }
        
        alert = alert_service.generate_alert(scoring_result, context)
        
        assert alert['level'] == 'medium'
        assert alert['color'] == 'yellow'
    
    def test_context_message_both_sources(self, alert_service):
        """Test context message when both ML and AI detect threat."""
        scoring_result = {
            'ml_score': 75.0,
            'ai_score': 70.0,
            'final_score': 75.0,
            'ml_factors': {},
            'ai_explanation': 'Fight detected',
            'ai_scene_type': 'real_fight',
            'ai_confidence': 0.9,
            'detection_source': 'both',
            'should_alert': True
        }
        
        message = alert_service._generate_context_message(scoring_result)
        
        assert 'Both ML and AI detected threat' in message
    
    def test_context_message_ml_only_boxing(self, alert_service):
        """Test context message when ML detects but AI identifies boxing."""
        scoring_result = {
            'ml_score': 70.0,
            'ai_score': 25.0,
            'final_score': 70.0,
            'ml_factors': {},
            'ai_explanation': 'Controlled sparring',
            'ai_scene_type': 'boxing',
            'ai_confidence': 0.85,
            'detection_source': 'ml',
            'should_alert': True
        }
        
        message = alert_service._generate_context_message(scoring_result)
        
        assert 'boxing' in message.lower() or 'sparring' in message.lower()
    
    def test_context_message_ml_only_drama(self, alert_service):
        """Test context message when ML detects but AI identifies drama."""
        scoring_result = {
            'ml_score': 65.0,
            'ai_score': 20.0,
            'final_score': 65.0,
            'ml_factors': {},
            'ai_explanation': 'Staged performance',
            'ai_scene_type': 'drama',
            'ai_confidence': 0.8,
            'detection_source': 'ml',
            'should_alert': True
        }
        
        message = alert_service._generate_context_message(scoring_result)
        
        assert 'drama' in message.lower() or 'performance' in message.lower() or 'staged' in message.lower()
    
    def test_context_message_ai_only(self, alert_service):
        """Test context message when only AI detects threat."""
        scoring_result = {
            'ml_score': 50.0,
            'ai_score': 75.0,
            'final_score': 75.0,
            'ml_factors': {},
            'ai_explanation': 'Contextual threat',
            'ai_scene_type': 'real_fight',
            'ai_confidence': 0.9,
            'detection_source': 'ai',
            'should_alert': True
        }
        
        message = alert_service._generate_context_message(scoring_result)
        
        assert 'AI Detection' in message
    
    def test_get_top_factors(self, alert_service):
        """Test extraction of top risk factors."""
        ml_factors = {
            'aggressive_posture': 0.8,
            'proximity_violation': 0.7,
            'weapon_detection': 0.0,
            'crowd_density': 0.3,
            'loitering': 0.1
        }
        
        top_factors = alert_service._get_top_factors(ml_factors, top_n=3)
        
        # Should return top 3 factors with score > 0.1
        assert len(top_factors) <= 3
        assert any('Aggressive Posture' in f for f in top_factors)
        assert any('Proximity Violation' in f for f in top_factors)
        assert any('Crowd Density' in f for f in top_factors)
    
    def test_get_alert_color(self, alert_service):
        """Test color assignment based on final score."""
        test_cases = [
            (85.0, 'red'),
            (70.0, 'red'),
            (65.0, 'orange'),
            (50.0, 'orange'),
            (45.0, 'yellow'),
            (30.0, 'yellow'),
            (25.0, 'green'),
            (10.0, 'green')
        ]
        
        for score, expected_color in test_cases:
            color = alert_service.get_alert_color(score)
            assert color == expected_color, f"Expected {expected_color} for score {score}, got {color}"
    
    def test_alert_metadata_completeness(self, alert_service):
        """Test that generated alerts contain all required metadata."""
        scoring_result = {
            'ml_score': 75.0,
            'ai_score': 70.0,
            'final_score': 75.0,
            'ml_factors': {'aggressive_posture': 0.8},
            'ai_explanation': 'Test explanation',
            'ai_scene_type': 'real_fight',
            'ai_confidence': 0.9,
            'detection_source': 'both',
            'should_alert': True
        }
        
        context = {
            'timestamp': datetime.utcnow(),
            'camera_id': 'CAM-01',
            'location': 'Test Location',
            'video_clip_path': '/path/to/clip.mp4'
        }
        
        alert = alert_service.generate_alert(scoring_result, context)
        
        # Check all required fields
        required_fields = [
            'timestamp', 'level', 'color', 'ml_score', 'ai_score', 'final_score',
            'risk_score', 'detection_source', 'ai_explanation', 'ai_scene_type',
            'ai_confidence', 'camera_id', 'location', 'message', 'risk_factors',
            'top_factors', 'video_clip_path', 'status'
        ]
        
        for field in required_fields:
            assert field in alert, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
