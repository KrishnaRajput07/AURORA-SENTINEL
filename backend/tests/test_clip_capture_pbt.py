# Feature: smart-bin-video-retention, Property 1: Feature toggle gates clip creation
"""
Property-based tests for ClipCaptureService.

P1:  Feature toggle gates clip creation
P3:  Captured clip duration matches configuration
P4:  Clip capture is triggered with correct parameters
P5:  Successful capture produces a complete ClipRecord
P6:  Storage error prevents partial ClipRecord creation
P7:  Duplicate capture prevention (idempotency)
P14: Expiry date equals capture timestamp plus retention period
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import all models so Base.metadata knows about every table
from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401
from backend.db.database import Base
from backend.services.clip_capture_service import ClipCaptureService
from backend.services.video_storage_service import VideoSegmentNotFoundError


# ---------------------------------------------------------------------------
# Shared test infrastructure
# ---------------------------------------------------------------------------

def make_test_db():
    """
    Return (engine, TestSession) backed by a uniquely-named shared in-memory
    SQLite database.  The named URI with cache=shared ensures all connections
    within the same process see the same data.
    """
    db_name = f"test_{uuid.uuid4().hex}"
    db_url = f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    return engine, TestSession


def seed_settings(session: Session, enabled: bool, duration: int = 10, retention: int = 10):
    """Insert the three Smart Bin SystemSetting rows."""
    session.add(SystemSetting(key="smart_bin_enabled", value="true" if enabled else "false"))
    session.add(SystemSetting(key="clip_duration_seconds", value=str(duration)))
    session.add(SystemSetting(key="clip_retention_days", value=str(retention)))
    session.commit()


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Property 1: Feature toggle gates clip creation
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    enabled=st.booleans(),
    score=st.floats(min_value=0, max_value=100, allow_nan=False),
)
def test_p1_feature_toggle_gates_clip_creation(enabled: bool, score: float):
    """
    # Feature: smart-bin-video-retention, Property 1: Feature toggle gates clip creation

    When smart_bin_enabled is False, handle_threshold_crossing() must return
    None and no ClipRecord should be inserted into the database.

    Validates: Requirements 1.3, 1.4
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=enabled)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    mock_ws = MagicMock()
    mock_ws.broadcast = asyncio.coroutine(lambda msg: None) if False else MagicMock(
        return_value=asyncio.coroutine(lambda: None)()
    )

    # Use an async mock for ws_manager.broadcast
    async def fake_broadcast(msg):
        pass

    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        result = run(service.handle_threshold_crossing(
            camera_id="cam_test",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            final_score=score,
            alert_id=1,
        ))

    db = TestSession()
    try:
        count = db.query(ClipRecord).count()
    finally:
        db.close()

    if not enabled:
        assert result is None, f"Expected None when disabled, got {result}"
        assert count == 0, f"Expected 0 ClipRecords when disabled, got {count}"


# ---------------------------------------------------------------------------
# Property 3: Captured clip duration matches configuration
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(duration=st.integers(min_value=5, max_value=300))
def test_p3_clip_duration_matches_config(duration: int):
    """
    # Feature: smart-bin-video-retention, Property 3: Captured clip duration matches configuration

    For any configured clip_duration_seconds value d in [5, 300], the
    ClipRecord created by ClipCaptureService should have duration_sec == d.

    Validates: Requirements 2.5
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True, duration=duration)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        result = run(service.handle_threshold_crossing(
            camera_id="cam_dur",
            timestamp=datetime(2024, 6, 1, 0, 0, 0),
            final_score=80.0,
            alert_id=None,
        ))

    assert result is not None, "Expected a ClipRecord to be created"
    assert result.duration_sec == duration, (
        f"Expected duration_sec={duration}, got {result.duration_sec}"
    )


# ---------------------------------------------------------------------------
# Property 4: Clip capture is triggered with correct parameters
# ---------------------------------------------------------------------------

_alphanumeric = st.characters(whitelist_categories=("Lu", "Ll", "Nd"))

@settings(max_examples=100)
@given(
    camera_id=st.text(min_size=1, max_size=20, alphabet=_alphanumeric),
    timestamp=st.datetimes(),
)
def test_p4_correct_parameters_passed_to_video_storage(camera_id: str, timestamp: datetime):
    """
    # Feature: smart-bin-video-retention, Property 4: Clip capture is triggered with correct parameters

    When smart_bin_enabled is True, ClipCaptureService must call
    VideoStorageService.get_segment() with exactly (camera_id, timestamp, duration).

    Validates: Requirements 3.1, 3.2
    """
    configured_duration = 30
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True, duration=configured_duration)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        run(service.handle_threshold_crossing(
            camera_id=camera_id,
            timestamp=timestamp,
            final_score=90.0,
            alert_id=None,
        ))

    mock_video.get_segment.assert_called_once_with(camera_id, timestamp, configured_duration)


# ---------------------------------------------------------------------------
# Property 5: Successful capture produces a complete ClipRecord
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    camera_id=st.text(min_size=1, max_size=20),
    timestamp=st.datetimes(),
    duration=st.integers(min_value=5, max_value=300),
)
def test_p5_successful_capture_produces_complete_clip_record(
    camera_id: str, timestamp: datetime, duration: int
):
    """
    # Feature: smart-bin-video-retention, Property 5: Successful capture produces a complete ClipRecord

    For any camera ID, alert ID, and successful response from
    VideoStorageService.get_segment(), the resulting ClipRecord should have
    non-null values for camera_id, captured_at, file_path, duration_sec, and
    expires_at.

    Validates: Requirements 3.3
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True, duration=duration)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        result = run(service.handle_threshold_crossing(
            camera_id=camera_id,
            timestamp=timestamp,
            final_score=75.0,
            alert_id=None,
        ))

    assert result is not None, "Expected a ClipRecord to be created"
    assert result.camera_id is not None, "camera_id must not be None"
    assert result.captured_at is not None, "captured_at must not be None"
    assert result.file_path is not None, "file_path must not be None"
    assert result.duration_sec is not None, "duration_sec must not be None"
    assert result.expires_at is not None, "expires_at must not be None"


# ---------------------------------------------------------------------------
# Property 6: Storage error prevents partial ClipRecord creation
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    camera_id=st.text(min_size=1, max_size=20),
    timestamp=st.datetimes(),
)
def test_p6_storage_error_prevents_partial_clip_record(camera_id: str, timestamp: datetime):
    """
    # Feature: smart-bin-video-retention, Property 6: Storage error prevents partial ClipRecord creation

    If VideoStorageService.get_segment() raises VideoSegmentNotFoundError,
    no ClipRecord should be present in the database after the call returns.

    Validates: Requirements 3.4
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.side_effect = VideoSegmentNotFoundError("segment not found")

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        result = run(service.handle_threshold_crossing(
            camera_id=camera_id,
            timestamp=timestamp,
            final_score=60.0,
            alert_id=None,
        ))

    assert result is None, "Expected None when storage raises an error"

    db = TestSession()
    try:
        count = db.query(ClipRecord).count()
    finally:
        db.close()

    assert count == 0, f"Expected 0 ClipRecords after storage error, got {count}"


# ---------------------------------------------------------------------------
# Property 7: Duplicate capture prevention (idempotency)
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(call_count=st.integers(min_value=1, max_value=10))
def test_p7_duplicate_capture_prevention(call_count: int):
    """
    # Feature: smart-bin-video-retention, Property 7: Duplicate capture prevention (idempotency)

    Calling handle_threshold_crossing() N times with the same (camera_id,
    alert_id) pair should result in exactly one ClipRecord in the database.

    Validates: Requirements 3.6
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True)
    finally:
        db.close()

    # Single service instance — shares the _captured dedup set across calls
    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    camera_id = "cam_dedup"
    alert_id = 42
    timestamp = datetime(2024, 3, 15, 8, 0, 0)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        for _ in range(call_count):
            run(service.handle_threshold_crossing(
                camera_id=camera_id,
                timestamp=timestamp,
                final_score=85.0,
                alert_id=alert_id,
            ))

    db = TestSession()
    try:
        count = db.query(ClipRecord).filter(
            ClipRecord.camera_id == camera_id,
            ClipRecord.alert_id == alert_id,
        ).count()
    finally:
        db.close()

    assert count == 1, (
        f"Expected exactly 1 ClipRecord after {call_count} calls with same "
        f"(camera_id, alert_id), got {count}"
    )


# ---------------------------------------------------------------------------
# Property 14: Expiry date equals capture timestamp plus retention period
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    timestamp=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
    ),
    retention_days=st.integers(min_value=1, max_value=365),
)
def test_p14_expiry_date_equals_capture_plus_retention(
    timestamp: datetime, retention_days: int
):
    """
    # Feature: smart-bin-video-retention, Property 14: Expiry date equals capture timestamp plus retention period

    For any capture timestamp t and retention period r days, the ClipRecord
    created by ClipCaptureService should have expires_at == t + timedelta(days=r).

    Validates: Requirements 6.5
    """
    _, TestSession = make_test_db()

    db: Session = TestSession()
    try:
        seed_settings(db, enabled=True, retention=retention_days)
    finally:
        db.close()

    service = ClipCaptureService()

    mock_video = MagicMock()
    mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        result = run(service.handle_threshold_crossing(
            camera_id="cam_expiry",
            timestamp=timestamp,
            final_score=55.0,
            alert_id=None,
        ))

    assert result is not None, "Expected a ClipRecord to be created"
    expected_expiry = timestamp + timedelta(days=retention_days)
    assert result.expires_at == expected_expiry, (
        f"Expected expires_at={expected_expiry}, got {result.expires_at}"
    )
