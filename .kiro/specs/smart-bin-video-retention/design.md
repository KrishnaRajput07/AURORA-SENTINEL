# Design Document: Smart Bin Video Retention

## Overview

The Smart Bin Video Retention feature automatically captures, stores, and manages video clips when a threat escalates beyond the configured alert threshold in the AURORA violence detection system. When the `TwoTierScoringService` produces a `final_score` that crosses the `alert_threshold`, a new `ClipCaptureService` trims the live video stream into a configurable-length clip, persists it to disk, and records metadata in a new `ClipRecord` database table. Clips are surfaced in the existing Archives page and alert queue. A background `RetentionScheduler` enforces configurable retention periods by deleting expired clips and their database records.

The design extends the existing FastAPI/SQLAlchemy backend and React/MUI frontend with minimal changes to existing services, preferring composition over modification.

---

## Architecture

```mermaid
flowchart TD
    SS[TwoTierScoringService] -->|final_score > threshold| CCS[ClipCaptureService]
    CCS -->|get_segment(camera_id, ts, duration)| VSS[VideoStorageService]
    VSS -->|video bytes| CCS
    CCS -->|write file + insert ClipRecord| DB[(SQLite / PostgreSQL)]
    CCS -->|associate clip_path| AS[AlertService]
    AS -->|broadcast alert_event| WS[WebSocketManager]
    WS -->|alert_event JSON| FE[React Frontend]
    FE --> AQ[AlertQueue component]
    FE --> MV[MapView component]
    FE --> AG[ArchiveGallery component]

    RS[RetentionScheduler] -->|query expired ClipRecords| DB
    RS -->|delete file + delete record| FS[File System]

    SP[Settings API /settings/smart-bin] --> DB
    FE -->|GET/POST settings| SP
```

Key design decisions:

- `ClipCaptureService` is a new service that orchestrates capture; it does not modify `VideoStorageService` or `AlertService` directly — it calls them.
- `RetentionScheduler` runs as an `asyncio` background task started at FastAPI startup, replacing the existing file-mtime-based cleanup in `VideoStorageService`.
- Settings are stored as `SystemSetting` key-value rows (existing model), using three new keys: `smart_bin_enabled`, `clip_duration_seconds`, `clip_retention_days`.
- The `ClipRecord` table is a new SQLAlchemy model added to `backend/db/models.py`.

---

## Components and Interfaces

### Backend

#### `ClipRecord` (new DB model — `backend/db/models.py`)

New SQLAlchemy model (see Data Models section).

#### `ClipCaptureService` (new — `backend/services/clip_capture_service.py`)

```python
class ClipCaptureService:
    async def handle_threshold_crossing(
        self,
        camera_id: str,
        timestamp: datetime,
        final_score: float,
        alert_id: int,
    ) -> Optional[ClipRecord]: ...

    def _is_enabled(self, db: Session) -> bool: ...
    def _get_clip_duration(self, db: Session) -> int: ...
    def _get_retention_days(self, db: Session) -> int: ...
    def _dedup_key(self, camera_id: str, alert_id: int) -> str: ...
```

- Called by the scoring pipeline (e.g., `stream_vlm.py` router) after `should_alert` is `True`.
- Reads `smart_bin_enabled`, `clip_duration_seconds`, `clip_retention_days` from `SystemSetting`.
- Delegates video retrieval to `VideoStorageService.get_segment()` (new method, see below).
- Writes the clip file to `storage/bin/<camera_id>_<timestamp>.mp4`.
- Inserts a `ClipRecord` row.
- Calls `AlertService` to attach `video_clip_path` to the alert.
- Uses an in-memory set of `(camera_id, alert_id)` pairs to prevent duplicate captures.

#### `VideoStorageService` — new method `get_segment()`

```python
def get_segment(
    self,
    camera_id: str,
    end_time: datetime,
    duration_seconds: int,
) -> bytes:
    """
    Retrieve `duration_seconds` of video ending at `end_time` for `camera_id`.
    Returns raw MP4 bytes. Raises VideoSegmentNotFoundError on failure.
    """
```

Implemented by reading the most recent rolling recording file for the camera and using FFmpeg (`subprocess`) to trim the segment.

#### `RetentionScheduler` (new — `backend/services/retention_scheduler.py`)

```python
class RetentionScheduler:
    async def start(self) -> None: ...          # called at FastAPI startup
    async def _run_loop(self) -> None: ...      # sleeps 24 h between runs
    async def run_once(self, db: Session) -> int: ...  # returns deleted count
    async def _delete_clip(self, record: ClipRecord, db: Session) -> None: ...
```

- Registered via `app.on_event("startup")` in `main.py`.
- `run_once` queries `ClipRecord` where `expires_at < utcnow()`, deletes files, then deletes DB rows.
- Missing files are logged as warnings; the DB row is still deleted.
- File I/O errors are logged; the DB row is NOT deleted (retried next run).

#### Settings API (extend `backend/api/routers/settings.py`)

New generic endpoints:

```
GET  /settings/{key}          → {"key": str, "value": str}
POST /settings/{key}          → body: {"value": str}
```

Validation for Smart Bin keys is enforced in the router:

| Key | Type | Valid range |
|-----|------|-------------|
| `smart_bin_enabled` | bool string (`"true"`/`"false"`) | — |
| `clip_duration_seconds` | int string | 5–300 |
| `clip_retention_days` | int string | 1–365 |

#### Smart Bin API (new — `backend/api/routers/smart_bin.py`)

```
GET  /smart-bin/clips          → list of ClipRecord (non-expired, desc timestamp)
GET  /smart-bin/clips/{id}     → single ClipRecord or 404
GET  /smart-bin/clips/{id}/stream → FileResponse (video/mp4) or 404
```

#### Alert Router / WebSocket event

When `ClipCaptureService` successfully creates a `ClipRecord`, it calls `ws_manager.broadcast()` with:

```json
{
  "type": "alert",
  "alert_id": 123,
  "camera_id": "cam_01",
  "timestamp": "2025-01-01T12:00:00Z",
  "clip_id": 42,
  "clip_url": "/smart-bin/clips/42/stream",
  "level": "critical"
}
```

### Frontend

#### `SmartBinSettings` component (new — `frontend/src/components/SmartBinSettings.jsx`)

Rendered inside the existing `GeneralTab` in `System.jsx`. Contains:
- Toggle: "Smart Bin Video Retention" (`smart_bin_enabled`)
- Number input: "Clip Duration (seconds)" — validates 5–300
- Number input: "Clip Retention Period (days)" — validates 1–365

Each control reads its initial value from `GET /settings/{key}` and persists changes via `POST /settings/{key}`.

#### `ArchiveGallery` component (extend existing — `frontend/src/components/ArchiveGallery.jsx`)

Replace file-listing logic with `GET /smart-bin/clips`. Each card shows:
- Camera ID, capture timestamp, clip duration, expiry date
- Inline `<video>` player using `/smart-bin/clips/{id}/stream`
- "Unavailable" error state when the API returns 404

#### Alert Queue / Map View (extend existing)

Handle the new `"type": "alert"` WebSocket event shape to display `clip_url` link and map marker.

---

## Data Models

### `ClipRecord` (new SQLAlchemy model)

```python
class ClipRecord(Base):
    __tablename__ = "clip_records"

    id           = Column(Integer, primary_key=True, index=True)
    camera_id    = Column(String, nullable=False, index=True)
    alert_id     = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    file_path    = Column(String, nullable=False)
    duration_sec = Column(Integer, nullable=False)
    captured_at  = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at   = Column(DateTime, nullable=False, index=True)
```

`expires_at = captured_at + timedelta(days=retention_days)`

### `SystemSetting` keys (existing model, new rows)

| key | default value | description |
|-----|---------------|-------------|
| `smart_bin_enabled` | `"false"` | Feature toggle |
| `clip_duration_seconds` | `"10"` | Clip length in seconds |
| `clip_retention_days` | `"10"` | Retention period in days |

### `Alert` model (existing, no schema change)

`video_clip_path` column already exists and will be populated by `ClipCaptureService`.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Feature toggle gates clip creation

*For any* risk score value (including values above the alert threshold) and any camera ID, if `smart_bin_enabled` is `"false"` in `SystemSetting`, then calling `ClipCaptureService.handle_threshold_crossing()` should return `None` and no `ClipRecord` should be inserted into the database.

**Validates: Requirements 1.3, 1.4**

### Property 2: Input validation rejects out-of-range clip duration

*For any* integer value submitted as `clip_duration_seconds`, the settings API should accept it if and only if the value is in the closed interval [5, 300]; values outside this range should be rejected with a 422 response and the `SystemSetting` row should remain unchanged.

**Validates: Requirements 2.2, 2.3**

### Property 3: Captured clip duration matches configuration

*For any* configured `clip_duration_seconds` value `d` in [5, 300] and any threshold-crossing event, the `ClipRecord` created by `ClipCaptureService` should have `duration_sec == d`.

**Validates: Requirements 2.5**

### Property 4: Clip capture is triggered with correct parameters

*For any* camera ID and threshold-crossing timestamp, when `smart_bin_enabled` is `"true"`, `ClipCaptureService` should call `VideoStorageService.get_segment()` with exactly that camera ID, that timestamp, and the currently configured `clip_duration_seconds`.

**Validates: Requirements 3.1, 3.2**

### Property 5: Successful capture produces a complete ClipRecord

*For any* camera ID, alert ID, and successful response from `VideoStorageService.get_segment()`, the resulting `ClipRecord` should have non-null values for `camera_id`, `captured_at`, `file_path`, `duration_sec`, and `expires_at`.

**Validates: Requirements 3.3**

### Property 6: Storage error prevents partial ClipRecord creation

*For any* camera ID and timestamp, if `VideoStorageService.get_segment()` raises an exception, then no `ClipRecord` should be present in the database for that camera ID and timestamp after the call returns.

**Validates: Requirements 3.4**

### Property 7: Duplicate capture prevention (idempotency)

*For any* camera ID and alert ID, calling `ClipCaptureService.handle_threshold_crossing()` multiple times with the same `(camera_id, alert_id)` pair should result in exactly one `ClipRecord` in the database.

**Validates: Requirements 3.6**

### Property 8: Alert record references ClipRecord

*For any* successfully created `ClipRecord`, the `Alert` row with the matching `alert_id` should have its `video_clip_path` set to the `ClipRecord`'s `file_path`.

**Validates: Requirements 4.1**

### Property 9: WebSocket broadcast on ClipRecord creation

*For any* successfully created `ClipRecord`, `WebSocketManager.broadcast()` should be called exactly once with a message containing `type == "alert"`, the correct `camera_id`, and the correct `clip_id`.

**Validates: Requirements 4.2**

### Property 10: Alert queue event contains required fields

*For any* alert WebSocket event received by the frontend, the rendered alert queue entry should contain the `camera_id`, `timestamp`, and a `clip_url` link.

**Validates: Requirements 4.3**

### Property 11: Smart Bin API returns clips ordered by timestamp descending

*For any* set of `ClipRecord` rows in the database, `GET /smart-bin/clips` should return them sorted by `captured_at` descending.

**Validates: Requirements 5.1**

### Property 12: Smart Bin API excludes expired clips and includes required fields

*For any* set of `ClipRecord` rows with mixed `expires_at` values, `GET /smart-bin/clips` should return only those where `expires_at >= utcnow()`, and each returned record should include `camera_id`, `captured_at`, `duration_sec`, and `expires_at`.

**Validates: Requirements 5.2, 5.5**

### Property 13: Input validation rejects out-of-range retention period

*For any* integer value submitted as `clip_retention_days`, the settings API should accept it if and only if the value is in the closed interval [1, 365]; values outside this range should be rejected with a 422 response and the `SystemSetting` row should remain unchanged.

**Validates: Requirements 6.2, 6.3**

### Property 14: Expiry date equals capture timestamp plus retention period

*For any* capture timestamp `t` and retention period `r` days, the `ClipRecord` created by `ClipCaptureService` should have `expires_at == t + timedelta(days=r)`.

**Validates: Requirements 6.5**

### Property 15: Retention scheduler identifies exactly the expired records

*For any* set of `ClipRecord` rows with mixed `expires_at` values and a given "current time" `now`, `RetentionScheduler.run_once()` should attempt deletion of exactly those records where `expires_at < now` and leave all others untouched.

**Validates: Requirements 7.2**

### Property 16: Expired records and files are fully removed; file errors preserve the record

*For any* expired `ClipRecord`, after `RetentionScheduler.run_once()` completes successfully, both the file at `file_path` and the database row should be absent. If the file deletion raises an OS error, the database row should remain present (to be retried on the next run).

**Validates: Requirements 7.3, 7.4, 7.5, 7.6**

---

## Error Handling

| Scenario | Component | Behaviour |
|----------|-----------|-----------|
| `smart_bin_enabled` key missing | `ClipCaptureService._is_enabled()` | Returns `False`, logs `WARNING` |
| `clip_duration_seconds` key missing | `ClipCaptureService._get_clip_duration()` | Returns default `10`, logs `WARNING` |
| `clip_retention_days` key missing | `ClipCaptureService._get_retention_days()` | Returns default `10`, logs `WARNING` |
| `VideoStorageService.get_segment()` raises | `ClipCaptureService` | Logs `ERROR` with camera_id + timestamp; no `ClipRecord` created |
| File write fails | `ClipCaptureService` | Logs `ERROR`; no `ClipRecord` created |
| `ClipRecord` file missing at playback | `smart_bin.py` router | Returns HTTP 404 |
| Expired file missing at deletion | `RetentionScheduler` | Logs `WARNING`; DB row deleted |
| Expired file deletion OS error | `RetentionScheduler` | Logs `ERROR` with record ID + path; DB row retained |
| Camera ID has no coordinates | Map View (frontend) | Renders marker at default "unknown location" with label |
| Settings value out of range | Settings router | Returns HTTP 422; `SystemSetting` unchanged |

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are required. Unit tests cover specific examples, integration points, and error conditions. Property-based tests verify universal correctness across randomised inputs.

### Unit Tests

- `test_clip_capture_service.py`: specific examples for enabled/disabled toggle, default fallback values, error paths (storage failure, file write failure), duplicate prevention.
- `test_retention_scheduler.py`: specific examples for empty DB, all-expired, none-expired, mixed, missing file, file deletion error.
- `test_smart_bin_router.py`: HTTP 200 list, HTTP 404 on missing file, ordering, field presence.
- `test_settings_router.py`: boundary values (5, 300, 1, 365), out-of-range rejection, missing key defaults.
- `test_smart_bin_settings.jsx` (React Testing Library): toggle renders, number inputs render with correct values, validation error messages appear for out-of-range inputs.

### Property-Based Tests

Library: **Hypothesis** (Python) for backend; **fast-check** (TypeScript) for frontend.

Each property test runs a minimum of **100 iterations**.

Each test is tagged with a comment in the format:
`# Feature: smart-bin-video-retention, Property N: <property_text>`

| Property | Test file | Strategy |
|----------|-----------|----------|
| P1: Feature toggle gates clip creation | `test_clip_capture_pbt.py` | `st.booleans()` for enabled flag, `st.floats(0,100)` for score |
| P2: Clip duration validation | `test_settings_pbt.py` | `st.integers()` covering in-range and out-of-range |
| P3: Captured clip duration matches config | `test_clip_capture_pbt.py` | `st.integers(5,300)` for duration |
| P4: Correct parameters passed to VideoStorageService | `test_clip_capture_pbt.py` | `st.text()` for camera_id, `st.datetimes()` for timestamp |
| P5: Complete ClipRecord fields | `test_clip_capture_pbt.py` | `st.text()`, `st.datetimes()`, `st.integers(5,300)` |
| P6: Storage error prevents partial record | `test_clip_capture_pbt.py` | Inject random exceptions from VideoStorageService mock |
| P7: Duplicate prevention idempotency | `test_clip_capture_pbt.py` | `st.integers(1,10)` for call count |
| P8: Alert references ClipRecord | `test_alert_integration_pbt.py` | `st.builds(ClipRecord, ...)` |
| P9: WebSocket broadcast on creation | `test_alert_integration_pbt.py` | `st.builds(ClipRecord, ...)` |
| P10: Alert queue event fields (frontend) | `smart_bin_settings.pbt.test.ts` | `fc.record({camera_id, timestamp, clip_id})` |
| P11: Clips ordered by timestamp desc | `test_smart_bin_router_pbt.py` | `st.lists(st.builds(ClipRecord, ...))` |
| P12: Expired clips excluded, fields present | `test_smart_bin_router_pbt.py` | `st.lists(...)` with mixed `expires_at` |
| P13: Retention period validation | `test_settings_pbt.py` | `st.integers()` covering in-range and out-of-range |
| P14: Expiry date calculation | `test_clip_capture_pbt.py` | `st.datetimes()` × `st.integers(1,365)` |
| P15: Scheduler identifies expired records | `test_retention_scheduler_pbt.py` | `st.lists(...)` with mixed `expires_at`, `st.datetimes()` for "now" |
| P16: Full deletion / file error preserves record | `test_retention_scheduler_pbt.py` | Inject OS errors on file deletion |
