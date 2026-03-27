# Implementation Plan: Smart Bin Video Retention

## Overview

Implement the Smart Bin Video Retention feature for AURORA: automatic clip capture on threat escalation, configurable retention, a background deletion scheduler, REST API, and frontend settings/gallery integration. All backend code uses Python/FastAPI/SQLAlchemy; frontend uses React/MUI.

## Tasks

- [x] 1. Add `ClipRecord` database model
  - Add `ClipRecord` SQLAlchemy model to `backend/db/models.py` with columns: `id`, `camera_id`, `alert_id` (FK → alerts.id, nullable), `file_path`, `duration_sec`, `captured_at`, `expires_at`
  - Add index on `expires_at` and `camera_id`
  - Run Alembic migration (or `Base.metadata.create_all`) to create the `clip_records` table
  - _Requirements: 3.3, 6.5_

- [x] 2. Extend settings API with Smart Bin keys
  - [x] 2.1 Add generic `GET /settings/{key}` and `POST /settings/{key}` endpoints to `backend/api/routers/settings.py`
    - Validate `clip_duration_seconds` ∈ [5, 300] and `clip_retention_days` ∈ [1, 365]; return HTTP 422 on violation without mutating the DB row
    - Accept `smart_bin_enabled` as `"true"`/`"false"` string
    - _Requirements: 1.1, 1.2, 2.2, 2.3, 2.4, 6.2, 6.3, 6.4_

  - [x] 2.2 Write property test for clip duration validation (P2)
    - **Property 2: Input validation rejects out-of-range clip duration**
    - File: `backend/tests/test_settings_pbt.py` — use `st.integers()` spanning in-range and out-of-range values
    - **Validates: Requirements 2.2, 2.3**

  - [x] 2.3 Write property test for retention period validation (P13)
    - **Property 13: Input validation rejects out-of-range retention period**
    - File: `backend/tests/test_settings_pbt.py` — use `st.integers()` spanning in-range and out-of-range values
    - **Validates: Requirements 6.2, 6.3**

  - [x] 2.4 Write unit tests for settings router boundary values
    - File: `backend/tests/test_settings_router.py` — test boundary values 5, 300, 1, 365 and out-of-range rejection
    - _Requirements: 2.2, 2.3, 6.2, 6.3_

- [x] 3. Add `get_segment()` to `VideoStorageService`
  - Add `get_segment(camera_id: str, end_time: datetime, duration_seconds: int) -> bytes` to `backend/services/video_storage_service.py`
  - Use FFmpeg via `subprocess` to trim the most recent rolling recording file for the camera
  - Raise `VideoSegmentNotFoundError` on failure
  - _Requirements: 3.2_

- [x] 4. Implement `ClipCaptureService`
  - [x] 4.1 Create `backend/services/clip_capture_service.py` with `ClipCaptureService` class
    - Implement `handle_threshold_crossing(camera_id, timestamp, final_score, alert_id)` → `Optional[ClipRecord]`
    - Implement `_is_enabled()`, `_get_clip_duration()`, `_get_retention_days()` reading from `SystemSetting` with defaults (`False`, `10`, `10`) and `WARNING` log on missing key
    - Implement `_dedup_key()` and in-memory set to prevent duplicate captures per `(camera_id, alert_id)`
    - Write clip to `storage/bin/<camera_id>_<timestamp>.mp4`; insert `ClipRecord`; call `AlertService` to set `video_clip_path`; broadcast WebSocket event
    - Return `None` and skip all side-effects when `smart_bin_enabled` is `"false"`
    - Log `ERROR` and return `None` (no partial `ClipRecord`) on `VideoStorageService` or file-write failure
    - _Requirements: 1.3, 1.4, 1.5, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 6.5, 6.6_

  - [x] 4.2 Write property test: feature toggle gates clip creation (P1)
    - **Property 1: Feature toggle gates clip creation**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.booleans()` for enabled flag, `st.floats(0, 100)` for score
    - **Validates: Requirements 1.3, 1.4**

  - [x] 4.3 Write property test: captured clip duration matches config (P3)
    - **Property 3: Captured clip duration matches configuration**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.integers(5, 300)` for duration
    - **Validates: Requirements 2.5**

  - [x] 4.4 Write property test: correct parameters passed to VideoStorageService (P4)
    - **Property 4: Clip capture is triggered with correct parameters**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.text()` for camera_id, `st.datetimes()` for timestamp
    - **Validates: Requirements 3.1, 3.2**

  - [x] 4.5 Write property test: successful capture produces complete ClipRecord (P5)
    - **Property 5: Successful capture produces a complete ClipRecord**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.text()`, `st.datetimes()`, `st.integers(5, 300)`
    - **Validates: Requirements 3.3**

  - [x] 4.6 Write property test: storage error prevents partial ClipRecord (P6)
    - **Property 6: Storage error prevents partial ClipRecord creation**
    - File: `backend/tests/test_clip_capture_pbt.py` — inject random exceptions from `VideoStorageService` mock
    - **Validates: Requirements 3.4**

  - [x] 4.7 Write property test: duplicate capture prevention (P7)
    - **Property 7: Duplicate capture prevention (idempotency)**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.integers(1, 10)` for call count
    - **Validates: Requirements 3.6**

  - [x] 4.8 Write property test: expiry date equals capture timestamp plus retention period (P14)
    - **Property 14: Expiry date equals capture timestamp plus retention period**
    - File: `backend/tests/test_clip_capture_pbt.py` — `st.datetimes()` × `st.integers(1, 365)`
    - **Validates: Requirements 6.5**

  - [x] 4.9 Write unit tests for ClipCaptureService
    - File: `backend/tests/test_clip_capture_service.py` — cover enabled/disabled toggle, default fallback values, storage failure, file-write failure, duplicate prevention
    - _Requirements: 1.3, 1.5, 2.6, 3.4, 3.6, 6.6_

- [x] 5. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement alert integration and WebSocket broadcast
  - [x] 6.1 Wire `ClipCaptureService` into the scoring pipeline
    - In `backend/api/routers/stream_vlm.py` (or equivalent), call `ClipCaptureService.handle_threshold_crossing()` after `should_alert` is `True`
    - _Requirements: 3.1, 3.5, 4.1_

  - [x] 6.2 Write property test: alert record references ClipRecord (P8)
    - **Property 8: Alert record references ClipRecord**
    - File: `backend/tests/test_alert_integration_pbt.py` — `st.builds(ClipRecord, ...)`
    - **Validates: Requirements 4.1**

  - [x] 6.3 Write property test: WebSocket broadcast on ClipRecord creation (P9)
    - **Property 9: WebSocket broadcast on ClipRecord creation**
    - File: `backend/tests/test_alert_integration_pbt.py` — `st.builds(ClipRecord, ...)`
    - **Validates: Requirements 4.2**

- [x] 7. Implement `RetentionScheduler`
  - [x] 7.1 Create `backend/services/retention_scheduler.py` with `RetentionScheduler` class
    - Implement `start()`, `_run_loop()` (24 h sleep), `run_once(db) -> int`, `_delete_clip(record, db)`
    - `run_once` queries `ClipRecord` where `expires_at < utcnow()`, deletes files then DB rows
    - Missing file → log `WARNING`, still delete DB row
    - File deletion OS error → log `ERROR` with record ID + path, retain DB row for retry
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 7.2 Write property test: scheduler identifies exactly the expired records (P15)
    - **Property 15: Retention scheduler identifies exactly the expired records**
    - File: `backend/tests/test_retention_scheduler_pbt.py` — `st.lists(...)` with mixed `expires_at`, `st.datetimes()` for "now"
    - **Validates: Requirements 7.2**

  - [x] 7.3 Write property test: full deletion / file error preserves record (P16)
    - **Property 16: Expired records and files are fully removed; file errors preserve the record**
    - File: `backend/tests/test_retention_scheduler_pbt.py` — inject OS errors on file deletion
    - **Validates: Requirements 7.3, 7.4, 7.5, 7.6**

  - [x] 7.4 Write unit tests for RetentionScheduler
    - File: `backend/tests/test_retention_scheduler.py` — cover empty DB, all-expired, none-expired, mixed, missing file, file deletion error
    - _Requirements: 7.1–7.6_

- [x] 8. Implement Smart Bin REST API
  - [x] 8.1 Create `backend/api/routers/smart_bin.py` with three endpoints
    - `GET /smart-bin/clips` — return non-expired `ClipRecord` rows ordered by `captured_at` desc
    - `GET /smart-bin/clips/{id}` — return single record or HTTP 404
    - `GET /smart-bin/clips/{id}/stream` — return `FileResponse` (video/mp4) or HTTP 404 if file missing
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 8.2 Write property test: clips ordered by timestamp descending (P11)
    - **Property 11: Smart Bin API returns clips ordered by timestamp descending**
    - File: `backend/tests/test_smart_bin_router_pbt.py` — `st.lists(st.builds(ClipRecord, ...))`
    - **Validates: Requirements 5.1**

  - [x] 8.3 Write property test: expired clips excluded and required fields present (P12)
    - **Property 12: Smart Bin API excludes expired clips and includes required fields**
    - File: `backend/tests/test_smart_bin_router_pbt.py` — `st.lists(...)` with mixed `expires_at`
    - **Validates: Requirements 5.2, 5.5**

  - [x] 8.4 Write unit tests for Smart Bin router
    - File: `backend/tests/test_smart_bin_router.py` — HTTP 200 list, HTTP 404 on missing file, ordering, field presence
    - _Requirements: 5.1–5.5_

- [x] 9. Register router and startup hook in `main.py`
  - Import and register `smart_bin` router under prefix `/smart-bin` in `backend/api/main.py`
  - Register `RetentionScheduler.start()` via `app.on_event("startup")`
  - _Requirements: 7.1_

- [x] 10. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement `SmartBinSettings` frontend component
  - [x] 11.1 Create `frontend/src/components/SmartBinSettings.jsx`
    - Toggle labelled "Smart Bin Video Retention" bound to `smart_bin_enabled` via `GET/POST /settings/smart_bin_enabled`
    - Number input "Clip Duration (seconds)" — client-side validation 5–300, error message on violation, persists via `POST /settings/clip_duration_seconds`
    - Number input "Clip Retention Period (days)" — client-side validation 1–365, error message on violation, persists via `POST /settings/clip_retention_days`
    - Each control reads initial value on mount; persists on change within 2 s
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.3, 6.4_

  - [x] 11.2 Render `SmartBinSettings` inside `GeneralTab` in `frontend/src/pages/System.jsx`
    - Import and place `<SmartBinSettings />` within the existing tab layout
    - _Requirements: 1.1, 2.1, 6.1_

  - [x] 11.3 Write unit tests for SmartBinSettings component
    - File: `frontend/src/components/__tests__/SmartBinSettings.test.jsx` (React Testing Library)
    - Test: toggle renders with correct initial state, number inputs render with correct values, validation error messages appear for out-of-range inputs
    - _Requirements: 1.1, 2.2, 2.3, 6.2, 6.3_

  - [x] 11.4 Write property test: alert queue event contains required fields (P10)
    - **Property 10: Alert queue event contains required fields**
    - File: `frontend/src/components/__tests__/SmartBinSettings.pbt.test.ts` (fast-check)
    - Use `fc.record({ camera_id: fc.string(), timestamp: fc.date(), clip_id: fc.integer() })`
    - **Validates: Requirements 4.3**

- [x] 12. Extend `ArchiveGallery` component
  - Replace file-listing logic in `frontend/src/components/ArchiveGallery.jsx` with `GET /smart-bin/clips`
  - Each card: camera ID, capture timestamp, clip duration, expiry date, inline `<video>` using `/smart-bin/clips/{id}/stream`
  - Show "Unavailable" error state when API returns 404 for a clip
  - Handle unknown camera coordinates: display marker at default "unknown location" with label
  - _Requirements: 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 13. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (backend) and fast-check (frontend), minimum 100 iterations each
- Each property test must include the comment: `# Feature: smart-bin-video-retention, Property N: <property_text>`
