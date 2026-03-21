
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Property-Based Tests for Nemotron Verification

This module implements property-based tests for the Nemotron embedding verification layer.
Uses Hypothesis for property-based testing to validate universal correctness properties.

**Validates: Requirements 3.9**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.vlm_service import NemotronProvider


# ============================================================================
# Test Strategies
# ============================================================================

# Strategy for risk scores (0-100)
risk_scores = st.integers(min_value=0, max_value=100)

# Strategy for verification scores (0.0-1.0)
verification_scores = st.floats(min_value=0.0, max_value=1.0)

# Strategy for scene types
scene_types = st.sampled_from(['real_fight', 'organized_sport', 'normal', 'suspicious'])

# Strategy for category similarity scores (0.0-1.0)
category_scores = st.floats(min_value=0.0, max_value=1.0)


# ============================================================================
# PROPERTY 1: Conservative Disagreement Handling
# **Validates: Requirements 3.9**
# ============================================================================

@given(
    qwen_risk_score=risk_scores,
    nemotron_risk_score=risk_scores,
    verification_score=verification_scores,
    qwen_scene_type=scene_types,
    nemotron_scene_type=scene_types
)
@settings(max_examples=20, deadline=None)
def test_property_1_conservative_disagreement_handling(
    qwen_risk_score,
    nemotron_risk_score,
    verification_score,
    qwen_scene_type,
    nemotron_scene_type
):
    """
    Property 1: Conservative disagreement handling
    **Validates: Requirements 3.9**
    
    Universal Property: When models disagree (different scene types OR verification < 0.6),
    the system MUST use the higher risk score (conservative approach).
    
    This ensures that in public safety contexts, we err on the side of caution
    and never downgrade a threat when there's uncertainty.
    """
    # Create mock NemotronProvider
    provider = NemotronProvider()
    
    # Mock the model to avoid loading actual model in tests
    provider.available = True
    provider.model = Mock()
    provider.processor = Mock()
    
    # Mock the embedding computation methods
    mock_image_embedding = np.array([[0.1] * 768])
    mock_summary_embedding = np.array([[0.2] * 768])
    
    # Create mock category scores based on nemotron_scene_type
    category_map = {
        'real_fight': 0,
        'organized_sport': 1,
        'normal': 2,
        'suspicious': 3
    }
    category_scores_array = np.array([0.3, 0.3, 0.3, 0.3])
    # Set the nemotron scene type to have highest score
    nemotron_idx = category_map[nemotron_scene_type]
    category_scores_array[nemotron_idx] = 0.8
    
    # Mock forward_images to return image embedding
    provider.forward_images = Mock(return_value=mock_image_embedding)
    
    # Mock forward_queries to return appropriate embeddings
    def mock_forward_queries(queries):
        if len(queries) == 1:
            # Summary embedding
            return mock_summary_embedding
        else:
            # Category embeddings
            return np.array([[0.1] * 768] * 4)
    
    provider.forward_queries = Mock(side_effect=mock_forward_queries)
    
    # Mock get_scores to return controlled similarity scores
    def mock_get_scores(image_emb, query_emb):
        if query_emb.shape[0] == 1:
            # Verification score (image ↔ summary)
            return np.array([[verification_score]])
        else:
            # Category scores (image ↔ threat categories)
            return np.array([category_scores_array])
    
    provider.get_scores = Mock(side_effect=mock_get_scores)
    
    # Mock the risk score mapping
    risk_map = {
        'real_fight': (80, 95),
        'organized_sport': (20, 35),
        'normal': (10, 25),
        'suspicious': (60, 75)
    }
    
    # Calculate expected nemotron risk score
    if category_scores_array[nemotron_idx] > 0.7:
        risk_range = risk_map[nemotron_scene_type]
        expected_nemotron_risk = int(np.mean(risk_range))
    else:
        expected_nemotron_risk = 50
    
    # Create mock image
    mock_image = Mock()
    
    # Call verify_analysis
    result = provider.verify_analysis(
        image=mock_image,
        qwen_summary="Test summary",
        qwen_scene_type=qwen_scene_type,
        qwen_risk_score=qwen_risk_score,
        timeout=3.0
    )
    
    # Determine if models agree
    verified = verification_score > 0.6
    agreement = qwen_scene_type == nemotron_scene_type
    
    # CRITICAL PROPERTY: Conservative disagreement handling
    if not verified or not agreement:
        # When there's disagreement or mismatch, MUST use higher risk score
        expected_recommended_score = max(qwen_risk_score, result['nemotron_risk_score'])
        
        assert result['recommended_score'] == expected_recommended_score, (
            f"Conservative handling violated! "
            f"Qwen: {qwen_risk_score}, Nemotron: {result['nemotron_risk_score']}, "
            f"Recommended: {result['recommended_score']}, Expected: {expected_recommended_score}. "
            f"Verified: {verified}, Agreement: {agreement}"
        )
        
        # Confidence should be lower (0.5) when there's disagreement
        assert result['confidence'] == 0.5, (
            f"Confidence should be 0.5 for disagreement, got {result['confidence']}"
        )
        
        # Verify that we're using the HIGHER risk score (conservative)
        assert result['recommended_score'] >= qwen_risk_score, (
            f"Recommended score {result['recommended_score']} is less than Qwen score {qwen_risk_score}"
        )
        assert result['recommended_score'] >= result['nemotron_risk_score'], (
            f"Recommended score {result['recommended_score']} is less than Nemotron score {result['nemotron_risk_score']}"
        )
    
    elif verified and agreement:
        # When both agree and verified, use average
        expected_recommended_score = int((qwen_risk_score + result['nemotron_risk_score']) / 2)
        
        assert result['recommended_score'] == expected_recommended_score, (
            f"Agreement handling violated! "
            f"Qwen: {qwen_risk_score}, Nemotron: {result['nemotron_risk_score']}, "
            f"Recommended: {result['recommended_score']}, Expected: {expected_recommended_score}"
        )
        
        # Confidence should be high (0.9) when there's agreement
        assert result['confidence'] == 0.9, (
            f"Confidence should be 0.9 for agreement, got {result['confidence']}"
        )
    
    # Verify verification score is correctly set
    assert result['verified'] == verified, (
        f"Verified flag mismatch: expected {verified}, got {result['verified']}"
    )
    
    # Verify agreement flag is correctly set
    assert result['agreement'] == agreement, (
        f"Agreement flag mismatch: expected {agreement}, got {result['agreement']}"
    )


# ============================================================================
# PROPERTY 2: Verification Score Threshold
# **Validates: Requirements 3.5, 3.6**
# ============================================================================

@given(
    verification_score=verification_scores
)
@settings(max_examples=20, deadline=None)
def test_property_2_verification_score_threshold(verification_score):
    """
    Property 2: Verification score threshold
    **Validates: Requirements 3.5, 3.6**
    
    Universal Property: Verification score > 0.6 marks analysis as "verified",
    score < 0.6 marks as "mismatch" and triggers conservative handling.
    
    The 0.6 threshold is critical for determining when Qwen's description
    accurately matches the actual image content.
    """
    # Create mock NemotronProvider
    provider = NemotronProvider()
    provider.available = True
    provider.model = Mock()
    provider.processor = Mock()
    
    # Mock embeddings
    mock_image_embedding = np.array([[0.1] * 768])
    mock_summary_embedding = np.array([[0.2] * 768])
    
    # Mock category scores (all equal, so 'real_fight' will be first)
    category_scores_array = np.array([0.8, 0.3, 0.3, 0.3])
    
    provider.forward_images = Mock(return_value=mock_image_embedding)
    
    def mock_forward_queries(queries):
        if len(queries) == 1:
            return mock_summary_embedding
        else:
            return np.array([[0.1] * 768] * 4)
    
    provider.forward_queries = Mock(side_effect=mock_forward_queries)
    
    def mock_get_scores(image_emb, query_emb):
        if query_emb.shape[0] == 1:
            return np.array([[verification_score]])
        else:
            return np.array([category_scores_array])
    
    provider.get_scores = Mock(side_effect=mock_get_scores)
    
    # Call verify_analysis
    result = provider.verify_analysis(
        image=Mock(),
        qwen_summary="Test summary",
        qwen_scene_type='real_fight',
        qwen_risk_score=80,
        timeout=3.0
    )
    
    # CRITICAL PROPERTY: Verification threshold at 0.6
    if verification_score > 0.6:
        assert result['verified'] is True, (
            f"Verification score {verification_score} > 0.6 should be verified"
        )
    else:
        assert result['verified'] is False, (
            f"Verification score {verification_score} <= 0.6 should NOT be verified"
        )
    
    # Verify the verification score is correctly stored
    assert abs(result['verification_score'] - verification_score) < 0.01, (
        f"Verification score mismatch: expected {verification_score}, got {result['verification_score']}"
    )


# ============================================================================
# PROPERTY 3: Risk Score Bounds
# **Validates: Requirements 3.10**
# ============================================================================

@given(
    qwen_risk_score=risk_scores,
    category_similarity=category_scores,
    scene_type=scene_types
)
@settings(max_examples=20, deadline=None)
def test_property_3_risk_score_bounds(qwen_risk_score, category_similarity, scene_type):
    """
    Property 3: Risk score bounds
    **Validates: Requirements 3.10**
    
    Universal Property: Risk scores must always be within valid ranges:
    - real_fight: 80-95
    - organized_sport: 20-35
    - normal: 10-25
    - suspicious: 60-75
    - uncertain (similarity <= 0.7): 50
    
    All recommended scores must be in range [0, 100].
    """
    # Create mock NemotronProvider
    provider = NemotronProvider()
    provider.available = True
    provider.model = Mock()
    provider.processor = Mock()
    
    # Mock embeddings
    mock_image_embedding = np.array([[0.1] * 768])
    mock_summary_embedding = np.array([[0.2] * 768])
    
    # Create category scores with the specified scene type having the highest score
    category_map = {
        'real_fight': 0,
        'organized_sport': 1,
        'normal': 2,
        'suspicious': 3
    }
    category_scores_array = np.array([0.3, 0.3, 0.3, 0.3])
    scene_idx = category_map[scene_type]
    category_scores_array[scene_idx] = category_similarity
    
    provider.forward_images = Mock(return_value=mock_image_embedding)
    
    def mock_forward_queries(queries):
        if len(queries) == 1:
            return mock_summary_embedding
        else:
            return np.array([[0.1] * 768] * 4)
    
    provider.forward_queries = Mock(side_effect=mock_forward_queries)
    
    def mock_get_scores(image_emb, query_emb):
        if query_emb.shape[0] == 1:
            return np.array([[0.8]])  # High verification score
        else:
            return np.array([category_scores_array])
    
    provider.get_scores = Mock(side_effect=mock_get_scores)
    
    # Call verify_analysis
    result = provider.verify_analysis(
        image=Mock(),
        qwen_summary="Test summary",
        qwen_scene_type=scene_type,
        qwen_risk_score=qwen_risk_score,
        timeout=3.0
    )
    
    # CRITICAL PROPERTY: Risk scores must be within valid bounds
    risk_map = {
        'real_fight': (80, 95),
        'organized_sport': (20, 35),
        'normal': (10, 25),
        'suspicious': (60, 75)
    }
    
    nemotron_risk = result['nemotron_risk_score']
    
    if category_similarity > 0.7:
        # Should be within the mapped range for the scene type
        min_risk, max_risk = risk_map[scene_type]
        assert min_risk <= nemotron_risk <= max_risk, (
            f"Nemotron risk score {nemotron_risk} out of bounds for {scene_type}: "
            f"expected [{min_risk}, {max_risk}]"
        )
    else:
        # Uncertain - should be 50
        assert nemotron_risk == 50, (
            f"Uncertain score should be 50, got {nemotron_risk}"
        )
    
    # Recommended score must always be in [0, 100]
    assert 0 <= result['recommended_score'] <= 100, (
        f"Recommended score {result['recommended_score']} out of bounds [0, 100]"
    )
    
    # All category scores must be in [0, 1]
    for category, score in result['category_scores'].items():
        assert 0.0 <= score <= 1.0, (
            f"Category score for {category} out of bounds: {score}"
        )


# ============================================================================
# PROPERTY 4: Confidence Levels
# **Validates: Requirements 3.8, 3.9**
# ============================================================================

@given(
    verification_score=verification_scores,
    agreement=st.booleans()
)
@settings(max_examples=20, deadline=None)
def test_property_4_confidence_levels(verification_score, agreement):
    """
    Property 4: Confidence levels
    **Validates: Requirements 3.8, 3.9**
    
    Universal Property: Confidence levels must follow these rules:
    - Verified AND agreement: confidence = 0.9 (high confidence)
    - Mismatch OR disagreement: confidence = 0.5 (low confidence)
    - Other cases: confidence = 0.7 (medium confidence)
    """
    # Create mock NemotronProvider
    provider = NemotronProvider()
    provider.available = True
    provider.model = Mock()
    provider.processor = Mock()
    
    # Mock embeddings
    mock_image_embedding = np.array([[0.1] * 768])
    mock_summary_embedding = np.array([[0.2] * 768])
    
    # Set up category scores to control agreement
    if agreement:
        # Same scene type
        qwen_scene = 'real_fight'
        category_scores_array = np.array([0.8, 0.3, 0.3, 0.3])  # real_fight highest
    else:
        # Different scene types
        qwen_scene = 'real_fight'
        category_scores_array = np.array([0.3, 0.8, 0.3, 0.3])  # organized_sport highest
    
    provider.forward_images = Mock(return_value=mock_image_embedding)
    
    def mock_forward_queries(queries):
        if len(queries) == 1:
            return mock_summary_embedding
        else:
            return np.array([[0.1] * 768] * 4)
    
    provider.forward_queries = Mock(side_effect=mock_forward_queries)
    
    def mock_get_scores(image_emb, query_emb):
        if query_emb.shape[0] == 1:
            return np.array([[verification_score]])
        else:
            return np.array([category_scores_array])
    
    provider.get_scores = Mock(side_effect=mock_get_scores)
    
    # Call verify_analysis
    result = provider.verify_analysis(
        image=Mock(),
        qwen_summary="Test summary",
        qwen_scene_type=qwen_scene,
        qwen_risk_score=80,
        timeout=3.0
    )
    
    # CRITICAL PROPERTY: Confidence levels based on verification and agreement
    verified = verification_score > 0.6
    actual_agreement = result['agreement']
    
    if verified and actual_agreement:
        expected_confidence = 0.9
    elif not verified or not actual_agreement:
        expected_confidence = 0.5
    else:
        expected_confidence = 0.7
    
    assert result['confidence'] == expected_confidence, (
        f"Confidence mismatch: expected {expected_confidence}, got {result['confidence']}. "
        f"Verified: {verified}, Agreement: {actual_agreement}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
