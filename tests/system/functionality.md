# System Tests — Functionality

End-to-end system integration tests and orchestrators.

## Test Files

### `run_all_tests.py`
- Test suite orchestrator
- Runs all system tests and generates comprehensive report
- Coordinates between unit, integration, and property-based tests

### `test_all_videos_simple.py`
- Simple batch test runner for video files
- Processes multiple videos and aggregates results

### `test_integrated_system.py`
- Full system integration test
- Verifies all components work together: API, ML, AI, database, storage

### `tmp_test_search.py`
- Temporary search functionality test
- Quick validation of search endpoint behavior
