# Tests — Functionality

Comprehensive test suite for AURORA Sentinel covering unit, integration, property-based, and system tests.

## Test Categories

| Directory | Type | Purpose |
|-----------|------|---------|
| `environment_utils/` | Utils | Environment setup and compatibility fixes |
| `fight_detection/` | Integration | Fight detection algorithm validation |
| `integration/` | Integration | End-to-end component integration |
| `ollama/` | Integration | Ollama VLM provider tests |
| `property_based/` | PBT | Hypothesis-generated random input tests |
| `setup_scripts/` | Utils | Windows PowerShell setup scripts |
| `synthetic_data/` | Utils | Synthetic video generation for testing |
| `system/` | System | Full system integration tests |
| `unit/` | Unit | Individual component tests |
| `video_utils/` | Unit | Video codec and utility tests |

## Key Test Files (Root)

### `test_agent_smoke.py`
- Smoke tests for the agent service
- Quick validation that agent can initialize and make tool calls

### `test_api_search.py`
- API endpoint tests for search functionality
- Tests query parsing, result formatting, error handling

### `test_api_video_upload.py`
- Tests the video upload API (`/process/upload`)
- Validates file handling, processing pipeline, result storage

### `test_fallback_scenarios.py`
- Tests graceful degradation when AI models are unavailable
- Validates ML-only operation mode
- Tests fallback chain: Primary → Backup → ML-only

### `test_fire_detection.py`
- Tests fire detection capabilities
- Validates fire/flame recognition in video frames

### `test_fire_system_integration.py`
- Integration tests for fire detection with the alerting system
- Tests fire alerts trigger correct workflows

### `test_ml_smoke.py`
- Smoke tests for ML service initialization
- Validates YOLO detector and risk engine load correctly

### `test_nemotron_verification.py`
- Tests Nemotron as a verification layer
- Validates confidence adjustments and explanation quality

### `test_performance.py`
- Performance benchmarking tests
- Measures latency: ML detection (<100ms), AI analysis (2–5s)
- GPU vs CPU performance comparison

### `test_real_video_samples.py`
- Tests with real-world video samples
- Validates system performance on actual surveillance footage
- Generates detailed reports on accuracy metrics

### `test_vlm_service.py`
- Unit tests for the VLM service orchestrator
- Tests provider selection, fallback behavior, timeout handling

## Configuration

### `conftest.py`
- Pytest configuration and shared fixtures
- Database setup/teardown, mock services, test client

### `__init__.py`
- Test package initialization

## Running Tests
```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/property_based/

# Run with coverage
pytest --cov=backend --cov=models --cov=ai-intelligence-layer

# PowerShell (Windows)
./tests/run_tests.ps1
```
