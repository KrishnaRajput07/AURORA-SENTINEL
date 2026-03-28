"""
Unit tests for ClipCaptureService.

Covers:
- Enabled/disabled toggle
- Default fallback values for missing settings
- Storage failure (VideoSegmentNotFoundError)
- File-write failure
- Duplicate prevention

Requirements: 1.3, 1.5, 2.6, 3.4, 3.6, 6.6
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401
from backend.db.database import Base
from backend.services.clip_capture_service import ClipCaptureService
from backend.services.video_storage_service import VideoSegmentNotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_db():
    db_name = f"test_{uuid.uuid4().hex}"
    db_url = f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    return engine, TestSession


def seed(session: Session, **kwargs):
    """Insert SystemSetting rows from keyword arguments."""
    for key, value in kwargs.items():
        session.add(SystemSetting(key=key, value=str(value)))
    session.commit()


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_patches(TestSession, video_side_effect=None, open_side_effect=None):
    """Return a list of context-manager patches for a standard test setup."""
    mock_video = MagicMock()
    if video_side_effect is not None:
        mock_video.get_segment.side_effect = video_side_effect
    else:
        mock_video.get_segment.return_value = b"fake_video_bytes"

    async def fake_broadcast(msg):
        pass

    mock_ws = MagicMock()
    mock_ws.broadcast = fake_broadcast

    mock_open = MagicMock()
    if open_side_effect is not None:
        mock_open.side_effect = open_side_effect

    return mock_video, mock_ws, mock_open


FIXED_TS = datetime(2024, 5, 10, 14, 30, 0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_disabled_returns_none():
    """smart_bin_enabled='false' → returns None, no ClipRecord inserted."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        seed(db, smart_bin_enabled="false", clip_duration_seconds="10", clip_retention_days="10")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(TestSession)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam1", FIXED_TS, 90.0, 1))

    assert result is None

    db = TestSession()
    try:
        assert db.query(ClipRecord).count() == 0
    finally:
        db.close()


def test_enabled_returns_clip_record():
    """smart_bin_enabled='true' → returns a ClipRecord."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        seed(db, smart_bin_enabled="true", clip_duration_seconds="15", clip_retention_days="7")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(TestSession)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam2", FIXED_TS, 75.0, None))

    assert result is not None
    assert isinstance(result, ClipRecord)
    assert result.camera_id == "cam2"
    assert result.duration_sec == 15


def test_default_duration_when_missing():
    """No clip_duration_seconds setting → uses default of 10."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        # Only set enabled; omit clip_duration_seconds
        seed(db, smart_bin_enabled="true", clip_retention_days="10")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(TestSession)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam3", FIXED_TS, 60.0, None))

    assert result is not None
    assert result.duration_sec == 10


def test_default_retention_when_missing():
    """No clip_retention_days setting → uses default of 10 days."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        # Only set enabled; omit clip_retention_days
        seed(db, smart_bin_enabled="true", clip_duration_seconds="10")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(TestSession)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam4", FIXED_TS, 50.0, None))

    assert result is not None
    expected_expiry = FIXED_TS + timedelta(days=10)
    assert result.expires_at == expected_expiry


def test_storage_failure_returns_none():
    """get_segment raises VideoSegmentNotFoundError → returns None, no ClipRecord."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        seed(db, smart_bin_enabled="true", clip_duration_seconds="10", clip_retention_days="10")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(
        TestSession,
        video_side_effect=VideoSegmentNotFoundError("not found"),
    )

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam5", FIXED_TS, 80.0, None))

    assert result is None

    db = TestSession()
    try:
        assert db.query(ClipRecord).count() == 0
    finally:
        db.close()


def test_file_write_failure_returns_none():
    """open() raises OSError → returns None, no ClipRecord."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        seed(db, smart_bin_enabled="true", clip_duration_seconds="10", clip_retention_days="10")
    finally:
        db.close()

    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(
        TestSession,
        open_side_effect=OSError("disk full"),
    )

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result = run(service.handle_threshold_crossing("cam6", FIXED_TS, 70.0, None))

    assert result is None

    db = TestSession()
    try:
        assert db.query(ClipRecord).count() == 0
    finally:
        db.close()


def test_duplicate_prevention():
    """Same (camera_id, alert_id) called twice → exactly 1 ClipRecord."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        seed(db, smart_bin_enabled="true", clip_duration_seconds="10", clip_retention_days="10")
    finally:
        db.close()

    # Single instance — shares _captured set
    service = ClipCaptureService()
    mock_video, mock_ws, mock_open = make_patches(TestSession)

    with patch("backend.services.clip_capture_service.video_storage_service", mock_video), \
         patch("backend.services.clip_capture_service.ws_manager", mock_ws), \
         patch("backend.services.clip_capture_service.SessionLocal", TestSession), \
         patch("os.makedirs"), \
         patch("builtins.open", mock_open):

        result1 = run(service.handle_threshold_crossing("cam7", FIXED_TS, 65.0, 99))
        result2 = run(service.handle_threshold_crossing("cam7", FIXED_TS, 65.0, 99))

    assert result1 is not None, "First call should return a ClipRecord"
    assert result2 is None, "Second call with same (camera_id, alert_id) should return None"

    db = TestSession()
    try:
        count = db.query(ClipRecord).filter(
            ClipRecord.camera_id == "cam7",
            ClipRecord.alert_id == 99,
        ).count()
        assert count == 1
    finally:
        db.close()
