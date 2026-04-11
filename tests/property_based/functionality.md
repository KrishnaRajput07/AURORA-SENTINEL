# Property-Based Tests — Functionality

Property-based testing using Hypothesis — generates random inputs to find edge cases.

## Test Files

### `test_nemotron_verification_properties.py`
- Property-based tests for Nemotron verification
- Tests behavior across random confidence scores, scene types, and explanations

### `test_risk_engine_properties.py`
- Property-based tests for the RiskScoringEngine
- Validates risk score calculations with random detection inputs
- Tests temporal validation, proximity, and aggression scoring

### `test_scoring_service_properties.py`
- Property-based tests for the TwoTierScoringService
- Tests weighted score calculations and threshold logic
- Validates should_alert determinations across random inputs
