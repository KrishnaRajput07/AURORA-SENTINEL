# Integration Tests — Functionality

End-to-end integration tests that verify the complete system works together.

## Test Files

### `test_health_check_with_model_status.py`
- Tests the `/health` endpoint
- Verifies model status reporting in health checks

### `test_nemotron_integration.py`
- Integration tests for Nemotron VLM provider
- Tests Nemotron as verification layer

### `test_normal_videos.py`
- Tests system behavior with normal/non-threatening videos
- Validates low false positive rate
- Generates `normal_videos_report.json`

### `test_real_ai_comprehensive.py`
- Comprehensive AI validation tests with real VLM calls
- Tests full pipeline with actual AI analysis
- Generates `real_ai_comprehensive_report.json`

### `test_real_ai_validation.py`
- Focused validation of AI tier behavior
- Tests scene classification accuracy

### `test_two_tier_integration.py`
- Primary integration test for the two-tier scoring system
- Large test suite (500+ lines) covering ML+AI integration
- Tests scoring weights, thresholds, and alert generation

### `test_video_pipeline.py`
- End-to-end video processing pipeline test
- Validates upload → processing → results flow

### `test_vlm_intelligence.py`
- Tests VLM integration with the intelligence layer
- (Currently empty placeholder)

## Report Files

- `INTEGRATION_TEST_REPORT.md` — Summary of integration test results
- `NORMAL_VIDEOS_TEST_REPORT.md` — Results from normal video testing
- `correlation_report.json` — Correlation analysis between ML and AI scores
- `normal_videos_report.json` — Detailed normal video test results
- `real_ai_comprehensive_report.json` — Comprehensive AI validation results
