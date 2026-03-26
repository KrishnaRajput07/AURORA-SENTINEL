"""
Alert Service for Enhanced Fight Detection

Generates operator alerts with two-tier score metadata.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Load config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    import config
except ImportError:
    config = None


class AlertService:
    """
    Service for generating and managing alerts with two-tier scoring metadata.
    """
    
    def __init__(self):
        """Initialize the alert service."""
        pass
    
    def generate_alert(self, scoring_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate operator alert with two-tier score metadata.
        
        Args:
            scoring_result: Dict from TwoTierScoringService.calculate_scores()
                - ml_score: float (0-100)
                - ai_score: float (0-100)
                - final_score: float (MAX of ml_score and ai_score)
                - ml_factors: Dict of detection factors
                - ai_explanation: str
                - ai_scene_type: str
                - ai_confidence: float (0-1)
                - detection_source: str ("ml" | "ai" | "both" | "none")
                - should_alert: bool
            context: Dict with camera_id, timestamp, location, etc.
            
        Returns:
            Dict with alert metadata ready for database insertion
        """
        final_score = scoring_result['final_score']
        ml_score = scoring_result['ml_score']
        ai_score = scoring_result['ai_score']
        detection_source = scoring_result['detection_source']
        
        # Determine alert level and color based on Final_Score
        critical_th = getattr(config, 'ALERT_LEVEL_CRITICAL', 70) if config else 70
        high_th = getattr(config, 'ALERT_LEVEL_HIGH', 50) if config else 50
        medium_th = getattr(config, 'ALERT_LEVEL_MEDIUM', 30) if config else 30

        if final_score > critical_th:
            level = 'critical'
            color = 'red'
        elif final_score > high_th:
            level = 'high'
            color = 'orange'
        elif final_score > medium_th:
            level = 'medium'
            color = 'yellow'
        else:
            level = 'low'
            color = 'green'
        
        # Generate context-aware message
        message = self._generate_context_message(scoring_result)
        
        # Get top risk factors
        ml_factors = scoring_result.get('ml_factors', {})
        top_factors = self._get_top_factors(ml_factors)
        
        # Build alert object
        alert = {
            'timestamp': context.get('timestamp', datetime.utcnow()),
            'level': level,
            'color': color,
            
            # Two-tier scores
            'ml_score': ml_score,
            'ai_score': ai_score,
            'final_score': final_score,
            'risk_score': final_score,  # Legacy field for backward compatibility
            
            # Detection metadata
            'detection_source': detection_source,
            'ai_explanation': scoring_result.get('ai_explanation', ''),
            'ai_scene_type': scoring_result.get('ai_scene_type', 'normal'),
            'ai_confidence': scoring_result.get('ai_confidence', 0.0),
            
            # Context
            'camera_id': context.get('camera_id', 'unknown'),
            'location': context.get('location', 'unknown'),
            'message': message,
            'risk_factors': ml_factors,
            'top_factors': top_factors,
            
            # Video clip
            'video_clip_path': context.get('video_clip_path'),
            
            # Status
            'status': 'pending'
        }
        
        logger.info(f"Alert generated: Level={level}, Final_Score={final_score:.1f}%, "
                   f"ML={ml_score:.1f}%, AI={ai_score:.1f}%, Source={detection_source}")
        
        return alert
    
    def _generate_context_message(self, scoring_result: Dict[str, Any]) -> str:
        """
        Generate context-aware alert message based on detection source.
        
        Args:
            scoring_result: Scoring result dict
            
        Returns:
            Context-aware message string
        """
        source = scoring_result['detection_source']
        ml_score = scoring_result['ml_score']
        ai_score = scoring_result['ai_score']
        ai_scene_type = scoring_result.get('ai_scene_type', 'normal')
        
        if source == 'both':
            return "Both ML and AI detected threat - Manual review required"
        elif source == 'ml' and ai_score < 30:
            # ML detected combat but AI identified it as controlled
            if ai_scene_type == 'boxing':
                return f"ML Detection - AI Verification: Controlled sparring/boxing activity"
            elif ai_scene_type == 'drama':
                return f"ML Detection - AI Verification: Staged/performance activity"
            else:
                return f"ML Detection - AI Verification: {ai_scene_type}"
        elif source == 'ai':
            return "AI Detection - Review ML Factors"
        else:
            return "Elevated risk detected - Manual review recommended"
    
    def _get_top_factors(self, ml_factors: Dict[str, float], top_n: int = 3) -> list:
        """
        Get top N contributing risk factors.
        
        Args:
            ml_factors: Dict of factor names to scores
            top_n: Number of top factors to return
            
        Returns:
            List of formatted factor strings
        """
        # Sort factors by score
        sorted_factors = sorted(ml_factors.items(), key=lambda x: x[1], reverse=True)
        
        # Format top factors
        top_factors = []
        for factor_name, score in sorted_factors[:top_n]:
            if score > 0.1:  # Only include significant factors
                formatted_name = factor_name.replace('_', ' ').title()
                top_factors.append(f"{formatted_name}: {int(score * 100)}%")
        
        return top_factors
    
    def get_alert_color(self, final_score: float) -> str:
        """
        Get color code for alert based on final score.
        
        Args:
            final_score: Final risk score (0-100)
            
        Returns:
            Color string: "red" | "orange" | "yellow" | "green"
        """
        critical_th = getattr(config, 'ALERT_LEVEL_CRITICAL', 70) if config else 70
        high_th = getattr(config, 'ALERT_LEVEL_HIGH', 50) if config else 50
        medium_th = getattr(config, 'ALERT_LEVEL_MEDIUM', 30) if config else 30

        if final_score > critical_th:
            return 'red'
        elif final_score > high_th:
            return 'orange'
        elif final_score > medium_th:
            return 'yellow'
        else:
            return 'green'
