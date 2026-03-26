"""
Two-Tier Scoring Service for Enhanced Fight Detection

This service implements the dual-scoring architecture:
- ML_Score: Aggressive detection of physical combat patterns (no discrimination)
- AI_Score: Context-aware verification using vision-language models
- Final_Score: Weighted combination (0.3×ML + 0.7×AI) for operator alerts

If the final weighted score exceeds the alert threshold (60%), the operator is notified for manual review.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Load config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    import config
except ImportError:
    config = None


class TwoTierScoringService:
    """
    Two-tier scoring service that combines ML risk engine with AI intelligence verification.
    """
    
    def __init__(self, risk_engine, ai_client=None):
        """
        Initialize the two-tier scoring service.
        
        Args:
            risk_engine: RiskScoringEngine instance for ML-based detection
            ai_client: AI intelligence client for context verification (optional)
        """
        self.risk_engine = risk_engine
        self.ai_client = ai_client
        self.alert_threshold = getattr(config, 'ALERT_THRESHOLD', 60.0) if config else 60.0
        
    async def calculate_scores(self, frame, detection_data, context=None):
        """
        Calculate both ML and AI scores, return aggregated result.
        
        Args:
            frame: Video frame (numpy array or bytes)
            detection_data: Dict with 'poses', 'objects', 'weapons', etc.
            context: Optional context dict with 'camera_id', 'timestamp', 'sensitivity'
            
        Returns:
            Dict with:
                - ml_score: float (0-100)
                - ai_score: float (0-100) - Nemotron-adjusted if available
                - final_score: float (weighted: 0.3*ML + 0.7*AI, or fallback)
                - ml_factors: Dict of detection factors
                - ai_explanation: str (reasoning from AI)
                - ai_scene_type: str ("real_fight" | "organized_sport" | "suspicious" | "normal")
                - ai_confidence: float (0-1)
                - nemotron_verification: Dict (Nemotron verification details if available)
                - scoring_method: str ("weighted" | "ml_only" | "ai_only")
                - confidence: float (overall confidence in final score)
                - detection_source: str ("ml" | "ai" | "both" | "none")
                - should_alert: bool
        """
        context = context or {}
        
        # 1. Calculate ML score using risk engine (synchronous)
        ml_score, ml_factors = self.risk_engine.calculate_risk(detection_data, context)
        
        # 2. Check ML threshold optimization (skip AI if ML score < threshold)
        ml_skip_threshold = getattr(config, 'ML_SKIP_AI_THRESHOLD', 20) if config else 20
        skip_ai_analysis = False
        if ml_score is not None and ml_score < ml_skip_threshold:
            skip_ai_analysis = True
            logger.info(f"ML score ({ml_score:.1f}) below threshold (20), skipping AI analysis to conserve resources")
        
        # 3. AI verification (conditional on ML threshold)
        ai_score = None
        ai_score_raw = None
        ai_explanation = ""
        ai_scene_type = "normal"
        ai_confidence = 0.0
        ai_provider = "none"
        nemotron_verification = None
        
        # AI verification runs only if not skipped by ML threshold
        if not skip_ai_analysis and self.ai_client:
            try:
                # Handle None ml_score for logging
                ml_score_for_log = ml_score if ml_score is not None else 0.0
                logger.info(f"Triggering AI verification (ML_Score: {ml_score_for_log:.1f}%)...")
                
                ai_result = await self._call_ai_verification(
                    frame=frame,
                    ml_score=ml_score if ml_score is not None else 0.0,
                    ml_factors=ml_factors,
                    camera_id=context.get('camera_id', 'unknown'),
                    timestamp=context.get('timestamp', 0)
                )
                
                # Extract AI score (may be Nemotron-adjusted)
                ai_score = ai_result.get('aiScore', None)
                ai_score_raw = ai_result.get('ai_score_raw', ai_score)
                ai_explanation = ai_result.get('explanation', '')
                ai_scene_type = ai_result.get('sceneType', 'normal')
                ai_confidence = ai_result.get('confidence', 0.0)
                ai_provider = ai_result.get('provider', 'unknown')
                nemotron_verification = ai_result.get('nemotron_verification', None)
                
                # Ensure ai_confidence is a valid number
                if ai_confidence is None:
                    ai_confidence = 0.0
                
                # Log AI score (handle None for logging)
                ai_score_log = ai_score if ai_score is not None else "unavailable"
                logger.info(f"AI verification complete: AI_Score={ai_score_log}, Scene={ai_scene_type}")
                
            except Exception as e:
                logger.error(f"AI verification failed: {e}")
                ai_explanation = f"AI verification error: {str(e)}"
                ai_score = None  # Mark as unavailable
        
        # 4. Calculate final score with proper fallback logic
        # NO hardcoded multipliers (no ml_score * 0.6)
        scoring_method = ""
        overall_confidence = 0.0
        
        if ai_score is not None and ml_score is not None:
            # Both available: weighted calculation
            ml_w = getattr(config, 'ML_SCORE_WEIGHT', 0.3) if config else 0.3
            ai_w = getattr(config, 'AI_SCORE_WEIGHT', 0.7) if config else 0.7
            final_score = (ml_w * ml_score) + (ai_w * ai_score)
            scoring_method = "weighted"
            overall_confidence = getattr(config, 'CONFIDENCE_BOTH_AVAILABLE', 0.8) if config else 0.8
            logger.info(f"Weighted scoring: {ml_w}×{ml_score:.1f} + {ai_w}×{ai_score:.1f} = {final_score:.1f}")
            
            # Log component scores for audit
            ai_score_raw_str = f"{ai_score_raw:.1f}" if ai_score_raw is not None else "N/A"
            logger.info(f"[AUDIT] ML_Score={ml_score:.1f}, AI_Score_Raw={ai_score_raw_str}, AI_Score_Adjusted={ai_score:.1f}, Final={final_score:.1f}")
            if nemotron_verification:
                logger.info(f"[AUDIT] Nemotron: verified={nemotron_verification.get('verified')}, agreement={nemotron_verification.get('agreement')}, recommended={nemotron_verification.get('recommended_score')}")
        
        elif ai_score is None and ml_score is not None:
            # AI unavailable: Final = ML
            final_score = ml_score
            scoring_method = "ml_only"
            overall_confidence = getattr(config, 'CONFIDENCE_ML_ONLY', 0.3) if config else 0.3
            logger.info(f"AI unavailable, using ML score only: Final={final_score:.1f} (confidence=0.3)")
            logger.info(f"[AUDIT] ML_Score={ml_score:.1f}, AI_Score=unavailable, Final={final_score:.1f}")
        
        elif ai_score is not None and ml_score is None:
            # ML unavailable: Final = AI
            final_score = ai_score
            scoring_method = "ai_only"
            overall_confidence = getattr(config, 'CONFIDENCE_AI_ONLY', 0.6) if config else 0.6
            logger.info(f"ML unavailable, using AI score only: Final={final_score:.1f} (confidence=0.6)")
            logger.info(f"[AUDIT] ML_Score=unavailable, AI_Score={ai_score:.1f}, Final={final_score:.1f}")
        
        else:
            # Both unavailable: fallback to 0
            final_score = 0.0
            scoring_method = "none"
            overall_confidence = getattr(config, 'CONFIDENCE_NONE', 0.0) if config else 0.0
            logger.warning("Both ML and AI unavailable, final score = 0")
            logger.info(f"[AUDIT] ML_Score=unavailable, AI_Score=unavailable, Final=0.0")
        
        # 5. Determine detection source (for backward compatibility)
        if ml_score and ml_score > self.alert_threshold and ai_score and ai_score > self.alert_threshold:
            source = "both"
        elif ml_score and ml_score > self.alert_threshold:
            source = "ml"
        elif ai_score and ai_score > self.alert_threshold:
            source = "ai"
        else:
            source = "none"
        
        # 6. Determine if alert should be generated
        should_alert = final_score > self.alert_threshold
        
        result = {
            'ml_score': ml_score if ml_score is not None else 0.0,
            'ai_score': ai_score if ai_score is not None else 0.0,
            'final_score': final_score,
            'ml_factors': ml_factors,
            'ai_explanation': ai_explanation,
            'ai_scene_type': ai_scene_type,
            'ai_confidence': ai_confidence,
            'ai_provider': ai_provider,
            'scoring_method': scoring_method,
            'confidence': overall_confidence,
            'detection_source': source,
            'should_alert': should_alert
        }
        
        # Include Nemotron verification details if available
        if nemotron_verification:
            result['nemotron_verification'] = nemotron_verification
        
        return result
    
    async def _call_ai_verification(self, frame, ml_score, ml_factors, camera_id, timestamp):
        """
        Call AI intelligence layer for context verification.
        
        Args:
            frame: Video frame
            ml_score: ML risk score (0-100)
            ml_factors: Dict of ML detection factors
            camera_id: Camera identifier
            timestamp: Frame timestamp
            
        Returns:
            Dict with aiScore, explanation, sceneType, confidence, provider
        """
        if not self.ai_client:
            return {
                'aiScore': 0.0,
                'explanation': 'AI client not available',
                'sceneType': 'normal',
                'confidence': 0.0,
                'provider': 'none'
            }
        
        try:
            # Convert frame to base64 if needed
            import base64
            import cv2
            
            if isinstance(frame, np.ndarray):
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
            elif isinstance(frame, bytes):
                frame_base64 = base64.b64encode(frame).decode('utf-8')
            else:
                frame_base64 = frame  # Assume already base64
            
            # Call AI intelligence layer
            result = await self.ai_client.analyze_image(
                imageData=frame_base64,
                mlScore=ml_score,
                mlFactors=ml_factors,
                cameraId=camera_id,
                timestamp=timestamp
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI verification call failed: {e}")
            raise
