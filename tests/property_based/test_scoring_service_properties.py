
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Property-Based Tests for Scoring Service

This module implements property-based tests for the weighted scoring logic.
Uses Hypothesis for property-based testing to validate universal correctness properties.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.scoring_service import TwoTierScoringService
from models.scoring.risk_engine import RiskScoringEngine


# ============================================================================
# Test Strategies
# ============================================================================

# Strategy for risk scores (0-100)
risk_scores = st.integers(min_value=0, max_value=100)

# Strategy for optional risk scores (None or 0-100)
optional_risk_scores = st.one_of(st.none(), risk_scores)

# Strategy for scene types
scene_types = st.sampled_from(['real_fight', 'organized_sport', 'normal', 'suspicious'])

# Strategy for confidence values (0.0-1.0)
confidence_values = st.floats(min_value=0.0, max_value=1.0)


# ============================================================================
# PROPERTY 2: Score Consistency
# **Validates: Requirements 4.1, 4.2, 4.3**
# ============================================================================

@given(
    ml_score=optional_risk_scores,
    ai_score=optional_risk_scores
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_2_score_consistency(ml_score, ai_score):
    """
    Property 2: Score consistency
    **Validates: Requirements 4.1, 4.2, 4.3**
    
    Universal Property: The final score calculation must follow these rules:
    1. When both ML and AI scores are available: Final = 0.3 * ML + 0.7 * AI
    2. When AI is unavailable: Final = ML (confidence 0.3)
    3. When ML is unavailable: Final = AI (confidence 0.6)
    4. When both unavailable: Final = 0 (confidence 0.0)
    
    This ensures consistent, predictable scoring behavior across all input combinations.
    """
    # Skip cases where both scores are None (edge case handled separately)
    if ml_score is None and ai_score is None:
        assume(False)
    
    # Create mock risk engine
    risk_engine = Mock(spec=RiskScoringEngine)
    risk_engine.calculate_risk = Mock(return_value=(ml_score, {}))
    
    # Create mock AI client
    ai_client = Mock()
    ai_client.analyze_image = AsyncMock(return_value={
        'aiScore': ai_score,
        'explanation': 'Test explanation',
        'sceneType': 'normal',
        'confidence': 0.8,
        'provider': 'test'
    })
    
    # Create scoring service
    scoring_service = TwoTierScoringService(risk_engine, ai_client)
    
    # Create test frame and detection data
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection_data = {'poses': [], 'objects': [], 'weapons': []}
    context = {'camera_id': 'test-cam', 'timestamp': 0.0}
    
    # Calculate scores
    result = await scoring_service.calculate_scores(frame, detection_data, context)
    
    # CRITICAL PROPERTY: Score consistency based on availability
    if ml_score is not None and ai_score is not None:
        if ml_score < 20:
            expected_final = ml_score
            expected_method = 'ml_only'
            expected_confidence = 0.3
        else:
            # Both available: weighted calculation
            expected_final = (0.3 * ml_score) + (0.7 * ai_score)
            expected_method = 'weighted'
            expected_confidence = 0.8
        
        assert abs(result['final_score'] - expected_final) < 0.01, (
            f"Weighted scoring violated! "
            f"ML={ml_score}, AI={ai_score}, "
            f"Expected Final={expected_final:.2f}, Got={result['final_score']:.2f}"
        )
        
        assert result['scoring_method'] == expected_method, (
            f"Scoring method should be '{expected_method}', got '{result['scoring_method']}'"
        )
        
        assert result['confidence'] == expected_confidence, (
            f"Confidence should be {expected_confidence}, got {result['confidence']}"
        )
        
        # Verify component scores are preserved
        assert result['ml_score'] == ml_score, (
            f"ML score not preserved: expected {ml_score}, got {result['ml_score']}"
        )
        expected_ai_score = 0.0 if ml_score < 20 else ai_score
        assert result['ai_score'] == expected_ai_score, (
            f"AI score not preserved: expected {expected_ai_score}, got {result['ai_score']}"
        )
    
    elif ml_score is not None and ai_score is None:
        # AI unavailable: Final = ML
        expected_final = ml_score
        expected_method = 'ml_only'
        expected_confidence = 0.3
        
        assert result['final_score'] == expected_final, (
            f"ML-only fallback violated! "
            f"ML={ml_score}, AI=None, "
            f"Expected Final={expected_final}, Got={result['final_score']}"
        )
        
        assert result['scoring_method'] == expected_method, (
            f"Scoring method should be '{expected_method}', got '{result['scoring_method']}'"
        )
        
        assert result['confidence'] == expected_confidence, (
            f"Confidence should be {expected_confidence}, got {result['confidence']}"
        )
        
        # Verify ML score is preserved
        assert result['ml_score'] == ml_score, (
            f"ML score not preserved: expected {ml_score}, got {result['ml_score']}"
        )
    
    elif ml_score is None and ai_score is not None:
        # ML unavailable: Final = AI
        expected_final = ai_score
        expected_method = 'ai_only'
        expected_confidence = 0.6
        
        assert result['final_score'] == expected_final, (
            f"AI-only fallback violated! "
            f"ML=None, AI={ai_score}, "
            f"Expected Final={expected_final}, Got={result['final_score']}"
        )
        
        assert result['scoring_method'] == expected_method, (
            f"Scoring method should be '{expected_method}', got '{result['scoring_method']}'"
        )
        
        assert result['confidence'] == expected_confidence, (
            f"Confidence should be {expected_confidence}, got {result['confidence']}"
        )
        
        # Verify AI score is preserved
        assert result['ai_score'] == ai_score, (
            f"AI score not preserved: expected {ai_score}, got {result['ai_score']}"
        )
    
    # Verify final score is always in valid range [0, 100]
    assert 0 <= result['final_score'] <= 100, (
        f"Final score {result['final_score']} out of bounds [0, 100]"
    )


# ============================================================================
# PROPERTY 3: No Arbitrary Multipliers
# **Validates: Requirements 4.4**
# ============================================================================

@given(
    ml_score=risk_scores
)
@settings(max_examples=30, deadline=None)
@pytest.mark.asyncio
async def test_property_3_no_arbitrary_multipliers(ml_score):
    """
    Property 3: No arbitrary multipliers
    **Validates: Requirements 4.4**
    
    Universal Property: When AI is unavailable, the system must NOT apply
    arbitrary multipliers like ml_score * 0.6. The final score must equal
    the ML score exactly.
    
    This prevents the old bug where hardcoded multipliers distorted scores.
    """
    # Create mock risk engine
    risk_engine = Mock(spec=RiskScoringEngine)
    risk_engine.calculate_risk = Mock(return_value=(ml_score, {}))
    
    # Create mock AI client that returns None (unavailable)
    ai_client = Mock()
    ai_client.analyze_image = AsyncMock(return_value={
        'aiScore': None,
        'explanation': 'AI unavailable',
        'sceneType': 'normal',
        'confidence': 0.0,
        'provider': 'none'
    })
    
    # Create scoring service
    scoring_service = TwoTierScoringService(risk_engine, ai_client)
    
    # Create test frame and detection data
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection_data = {'poses': [], 'objects': [], 'weapons': []}
    context = {'camera_id': 'test-cam', 'timestamp': 0.0}
    
    # Calculate scores
    result = await scoring_service.calculate_scores(frame, detection_data, context)
    
    # CRITICAL PROPERTY: No arbitrary multipliers
    # Final score must equal ML score exactly (not ml_score * 0.6 or any other multiplier)
    assert result['final_score'] == ml_score, (
        f"Arbitrary multiplier detected! "
        f"ML={ml_score}, Final={result['final_score']}. "
        f"Expected Final=ML (no multiplier), but got different value."
    )
    
    # Verify it's not using the old 0.6 multiplier
    old_buggy_score = ml_score * 0.6
    if ml_score != 0:  # Avoid false positive when ml_score is 0
        assert result['final_score'] != old_buggy_score or ml_score == 0, (
            f"Old buggy multiplier (0.6) detected! "
            f"ML={ml_score}, Final={result['final_score']}, "
            f"Old buggy value would be {old_buggy_score}"
        )
    
    # Verify scoring method is ml_only
    assert result['scoring_method'] == 'ml_only', (
        f"Scoring method should be 'ml_only', got '{result['scoring_method']}'"
    )


# ============================================================================
# PROPERTY 4: Weighted Calculation Correctness
# **Validates: Requirements 4.1**
# ============================================================================

@given(
    ml_score=risk_scores,
    ai_score=risk_scores
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_4_weighted_calculation_correctness(ml_score, ai_score):
    """
    Property 4: Weighted calculation correctness
    **Validates: Requirements 4.1**
    
    Universal Property: When both scores are available, the weighted formula
    must be exactly: Final = 0.3 * ML + 0.7 * AI
    
    This validates the correct weighting (30% ML, 70% AI) is applied.
    """
    # Create mock risk engine
    risk_engine = Mock(spec=RiskScoringEngine)
    risk_engine.calculate_risk = Mock(return_value=(ml_score, {}))
    
    # Create mock AI client
    ai_client = Mock()
    ai_client.analyze_image = AsyncMock(return_value={
        'aiScore': ai_score,
        'explanation': 'Test explanation',
        'sceneType': 'normal',
        'confidence': 0.8,
        'provider': 'test'
    })
    
    # Create scoring service
    scoring_service = TwoTierScoringService(risk_engine, ai_client)
    
    # Create test frame and detection data
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection_data = {'poses': [], 'objects': [], 'weapons': []}
    context = {'camera_id': 'test-cam', 'timestamp': 0.0}
    
    # Calculate scores
    result = await scoring_service.calculate_scores(frame, detection_data, context)
    
    # CRITICAL PROPERTY: Weighted calculation must be exact
    if ml_score < 20:
        expected_final = ml_score
    else:
        expected_final = (0.3 * ml_score) + (0.7 * ai_score)
    
    assert abs(result['final_score'] - expected_final) < 0.01, (
        f"Weighted calculation incorrect! "
        f"ML={ml_score}, AI={ai_score}, "
        f"Expected: {expected_final:.2f}, "
        f"Got: {result['final_score']:.2f}"
    )
    
    # Verify the weights are correct (not 50/50 or any other split)
    if ml_score >= 20:
        ml_contribution = 0.3 * ml_score
        ai_contribution = 0.7 * ai_score
        
        # The final score should be the sum of these contributions
        assert abs(result['final_score'] - (ml_contribution + ai_contribution)) < 0.01, (
            f"Weight distribution incorrect! "
            f"ML contribution (30%): {ml_contribution:.2f}, "
            f"AI contribution (70%): {ai_contribution:.2f}, "
            f"Sum: {ml_contribution + ai_contribution:.2f}, "
            f"Got: {result['final_score']:.2f}"
        )


# ============================================================================
# PROPERTY 5: Nemotron Adjustment Integration
# **Validates: Requirements 4.6**
# ============================================================================

@given(
    ml_score=risk_scores,
    ai_score_raw=risk_scores,
    nemotron_adjusted_score=risk_scores
)
@settings(max_examples=30, deadline=None)
@pytest.mark.asyncio
async def test_property_5_nemotron_adjustment_integration(
    ml_score,
    ai_score_raw,
    nemotron_adjusted_score
):
    """
    Property 5: Nemotron adjustment integration
    **Validates: Requirements 4.6**
    
    Universal Property: When Nemotron provides an adjusted AI score,
    the weighted calculation must use the Nemotron-adjusted score,
    not the raw Qwen2-VL score.
    
    This ensures Nemotron's verification layer properly influences the final score.
    """
    # Create mock risk engine
    risk_engine = Mock(spec=RiskScoringEngine)
    risk_engine.calculate_risk = Mock(return_value=(ml_score, {}))
    
    # Create mock AI client with Nemotron verification
    nemotron_verification = {
        'verification_score': 0.75,
        'verified': True,
        'agreement': True,
        'recommended_score': nemotron_adjusted_score,
        'nemotron_scene_type': 'real_fight',
        'confidence': 0.9
    }
    
    ai_client = Mock()
    ai_client.analyze_image = AsyncMock(return_value={
        'aiScore': nemotron_adjusted_score,  # Nemotron-adjusted score
        'ai_score_raw': ai_score_raw,  # Original Qwen score
        'explanation': 'Test explanation',
        'sceneType': 'real_fight',
        'confidence': 0.9,
        'provider': 'qwen2vl',
        'nemotron_verification': nemotron_verification
    })
    
    # Create scoring service
    scoring_service = TwoTierScoringService(risk_engine, ai_client)
    
    # Create test frame and detection data
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection_data = {'poses': [], 'objects': [], 'weapons': []}
    context = {'camera_id': 'test-cam', 'timestamp': 0.0}
    
    # Calculate scores
    result = await scoring_service.calculate_scores(frame, detection_data, context)
    
    # CRITICAL PROPERTY: Must use Nemotron-adjusted score in weighted calculation
    if ml_score < 20:
        expected_final = ml_score
        assert abs(result['final_score'] - expected_final) < 0.01, (
            f"Expected ml_only fallback! "
            f"ML={ml_score}, Expected: {expected_final:.2f}, Got: {result['final_score']:.2f}"
        )
    else:
        expected_final = (0.3 * ml_score) + (0.7 * nemotron_adjusted_score)
        
        assert abs(result['final_score'] - expected_final) < 0.01, (
            f"Nemotron adjustment not used in weighted calculation! "
            f"ML={ml_score}, AI_raw={ai_score_raw}, AI_adjusted={nemotron_adjusted_score}, "
            f"Expected: 0.3*{ml_score} + 0.7*{nemotron_adjusted_score} = {expected_final:.2f}, "
            f"Got: {result['final_score']:.2f}"
        )
        
        # Verify Nemotron verification details are included
        assert 'nemotron_verification' in result, (
            "Nemotron verification details missing from result"
        )
        
        assert result['nemotron_verification'] == nemotron_verification, (
            "Nemotron verification details not correctly passed through"
        )
    
    # Verify the AI score in result is the adjusted one
    if ml_score >= 20:
        assert result['ai_score'] == nemotron_adjusted_score, (
            f"AI score should be Nemotron-adjusted ({nemotron_adjusted_score}), "
            f"got {result['ai_score']}"
        )


# ============================================================================
# PROPERTY 6: Metadata Consistency
# **Validates: Requirements 4.5, 4.7**
# ============================================================================

@given(
    ml_score=optional_risk_scores,
    ai_score=optional_risk_scores
)
@settings(max_examples=30, deadline=None)
@pytest.mark.asyncio
async def test_property_6_metadata_consistency(ml_score, ai_score):
    """
    Property 6: Metadata consistency
    **Validates: Requirements 4.5, 4.7**
    
    Universal Property: The response must always include:
    1. scoring_method indicating which scores were used
    2. Component scores (ml_score, ai_score) for audit
    3. Confidence level appropriate to the scoring method
    
    This ensures transparency and auditability of scoring decisions.
    """
    # Skip cases where both scores are None or ml_score < 20 (which forces ml_only)
    if (ml_score is None and ai_score is None) or (ml_score is not None and ml_score < 20):
        assume(False)
    
    # Create mock risk engine
    risk_engine = Mock(spec=RiskScoringEngine)
    risk_engine.calculate_risk = Mock(return_value=(ml_score, {}))
    
    # Create mock AI client
    ai_client = Mock()
    ai_client.analyze_image = AsyncMock(return_value={
        'aiScore': ai_score,
        'explanation': 'Test explanation',
        'sceneType': 'normal',
        'confidence': 0.8,
        'provider': 'test'
    })
    
    # Create scoring service
    scoring_service = TwoTierScoringService(risk_engine, ai_client)
    
    # Create test frame and detection data
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detection_data = {'poses': [], 'objects': [], 'weapons': []}
    context = {'camera_id': 'test-cam', 'timestamp': 0.0}
    
    # Calculate scores
    result = await scoring_service.calculate_scores(frame, detection_data, context)
    
    # CRITICAL PROPERTY: Metadata must be present and consistent
    
    # 1. scoring_method must be present and valid
    assert 'scoring_method' in result, "scoring_method missing from result"
    valid_methods = ['weighted', 'ml_only', 'ai_only', 'none']
    assert result['scoring_method'] in valid_methods, (
        f"Invalid scoring_method: {result['scoring_method']}"
    )
    
    # 2. Component scores must be present
    assert 'ml_score' in result, "ml_score missing from result"
    assert 'ai_score' in result, "ai_score missing from result"
    
    # 3. Confidence must be present and valid
    assert 'confidence' in result, "confidence missing from result"
    assert 0.0 <= result['confidence'] <= 1.0, (
        f"Confidence {result['confidence']} out of bounds [0.0, 1.0]"
    )
    
    # 4. scoring_method must match actual score availability
    if ml_score is not None and ai_score is not None:
        if ml_score < 20:
            assert result['scoring_method'] == 'ml_only', (
                f"ml_score < 20 triggers skip optimization, expected 'ml_only', got '{result['scoring_method']}'"
            )
        else:
            assert result['scoring_method'] == 'weighted', (
                f"Both scores available, expected 'weighted', got '{result['scoring_method']}'"
            )
    elif ml_score is not None and ai_score is None:
        assert result['scoring_method'] == 'ml_only', (
            f"Only ML available, expected 'ml_only', got '{result['scoring_method']}'"
        )
    elif ml_score is None and ai_score is not None:
        assert result['scoring_method'] == 'ai_only', (
            f"Only AI available, expected 'ai_only', got '{result['scoring_method']}'"
        )
    
    # 5. Final score must be present and valid
    assert 'final_score' in result, "final_score missing from result"
    assert 0 <= result['final_score'] <= 100, (
        f"Final score {result['final_score']} out of bounds [0, 100]"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
