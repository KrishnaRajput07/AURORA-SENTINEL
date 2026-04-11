# Unit Tests — Functionality

Focused unit tests for individual services and functions.

## Test Files

### `test_alert_service.py`
- Unit tests for AlertService
- Tests alert generation with two-tier scoring metadata

### `test_error_handling.py`
- Tests error handling across the backend
- Validates exception catching and response formatting

### `test_intelligence_helpers.py`
- Tests helper functions in the intelligence layer
- Validates search query building, result formatting

### `test_keyword_fallback.py`
- Tests keyword-based classification fallback
- Validates threat keyword detection and negation handling

### `test_model_availability.py`
- Unit tests for ModelAvailabilityTracker
- Tests circuit breaker pattern implementation

### `test_nemotron_verification.py`
- Tests Nemotron verification service
- Validates confidence scoring and explanation parsing

### `test_scoring_service.py`
- Comprehensive tests for TwoTierScoringService
- Tests weighted calculations, thresholds, and edge cases

### `test_strict_classification.py`
- Tests strict scene classification logic
- Validates real fight vs boxing vs drama discrimination
