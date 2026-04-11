# Backend Tests — Functionality

This directory contains test suites for backend services and routers, including property-based testing (PBT).

## Test Files

### `test_alert_integration_pbt.py`
- Property-based tests for alert generation and integration
- Verifies alert metadata consistency across random scoring inputs

### `test_clip_capture_pbt.py`
- Property-based tests for clip capture service
- Tests deduplication, enable/disable toggling, and threshold crossing behavior

### `test_clip_capture_service.py`
- Unit tests for `ClipCaptureService`
- Covers handle_threshold_crossing, dedup logic, and DB interaction

### `test_retention_scheduler.py`
- Unit tests for `RetentionScheduler`
- Verifies expired clip deletion and run_once behavior

### `test_retention_scheduler_pbt.py`
- Property-based tests for retention scheduler
- Tests edge cases with random expiration timestamps

### `test_settings_pbt.py`
- Property-based tests for system settings validation
- Verifies value range constraints and type safety

### `test_settings_router.py`
- Integration tests for the settings API router
- Tests CRUD operations, VLM interval guardrails, and maintenance mode toggling

### `test_smart_bin_router.py`
- Integration tests for the smart-bin API router
- Tests clip listing, single clip retrieval, and streaming endpoints

### `test_smart_bin_router_pbt.py`
- Property-based tests for smart-bin router
- Verifies response schema consistency across random clip data
