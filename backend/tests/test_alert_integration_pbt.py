# Feature: smart-bin-video-retention, Property 8: Alert record references ClipRecord
"""
Property-based tests for alert integration with ClipRecord.

P8: For any successfully created ClipRecord, the Alert row with the matching
    alert_id should have its video_clip_path set to the ClipRecord's file_path.

Validates: Requirements 4.1
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Alert, ClipRecord
from backend.db.database import Base
from backend.services.clip_capture_service import ClipCaptureService


# ---------------------------------------------------------------------------
# In-memory SQLite fixture helpers
# ---------------------------------------------------------------------------

def make_session():
    """Create a fresh in-memory SQLite session with all tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Printable, non-empty camera IDs (avoid characters that break file paths)
camera_id_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=32,
)

# Timestamps within a reasonable range (avoid far-future/past edge cases)
captured_at_st = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)

# Duration in the valid range
duration_st = st.integers(min_value=5, max_value=300)

# Retention days in the valid range
retention_st = st.integers(min_value=1, max_value=365)

# File paths (simple strings, no OS path traversal)
file_path_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/_-."),
    min_size=1,
    max_size=128,
).map(lambda s: f"storage/bin/{s}.mp4")


def clip_record_st(alert_id: int):
    """Build a ClipRecord strategy bound to a specific alert_id."""
    return st.builds(
        ClipRecord,
        camera_id=camera_id_st,
        alert_id=st.just(alert_id),
        file_path=file_path_st,
        duration_sec=duration_st,
        captured_at=captured_at_st,
        expires_at=captured_at_st.map(lambda dt: dt + timedelta(days=10)),
    )


# ---------------------------------------------------------------------------
# Property 8: Alert record references ClipRecord
# ---------------------------------------------------------------------------

@settings(max_examples=25)
@given(
    camera_id=camera_id_st,
    file_path=file_path_st,
    duration_sec=duration_st,
    captured_at=captured_at_st,
    retention_days=retention_st,
)
def test_p8_alert_record_references_clip_record(
    camera_id, file_path, duration_sec, captured_at, retention_days
):
    """
    # Feature: smart-bin-video-retention, Property 8: Alert record references ClipRecord

    For any successfully created ClipRecord, the Alert row with the matching
    alert_id should have video_clip_path set to the ClipRecord's file_path.

    Validates: Requirements 4.1
    """
    db = make_session()
    try:
        # Create an Alert row to associate with
        alert = Alert(
            timestamp=captured_at,
            level="critical",
            risk_score=80.0,
            camera_id=camera_id,
            location="test-location",
            video_clip_path=None,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Build and persist a ClipRecord referencing that alert
        expires_at = captured_at + timedelta(days=retention_days)
        clip = ClipRecord(
            camera_id=camera_id,
            alert_id=alert.id,
            file_path=file_path,
            duration_sec=duration_sec,
            captured_at=captured_at,
            expires_at=expires_at,
        )
        db.add(clip)
        db.commit()
        db.refresh(clip)

        # Simulate what ClipCaptureService._attach_clip_to_alert() does
        svc = ClipCaptureService()
        svc._attach_clip_to_alert(alert.id, clip.file_path, db)

        # Verify: the Alert row now references the ClipRecord's file_path
        db.refresh(alert)
        assert alert.video_clip_path == clip.file_path, (
            f"Expected alert.video_clip_path={clip.file_path!r}, "
            f"got {alert.video_clip_path!r}"
        )

        # Verify: the ClipRecord's alert_id matches the alert
        assert clip.alert_id == alert.id, (
            f"Expected clip.alert_id={alert.id}, got {clip.alert_id}"
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Property 9: WebSocket broadcast on ClipRecord creation
# ---------------------------------------------------------------------------
# Feature: smart-bin-video-retention, Property 9: WebSocket broadcast on ClipRecord creation
"""
P9: For any successfully created ClipRecord, WebSocketManager.broadcast() should
    be called exactly once with a message containing type == "alert", the correct
    camera_id, and the correct clip_id.

Validates: Requirements 4.2
"""

import asyncio
import builtins
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


def _make_shared_session():
    """
    Create an in-memory SQLite session using a uuid-named shared-cache URI
    so that the same in-memory database is accessible across threads/calls
    within a single test run.
    """
    db_name = uuid.uuid4().hex
    uri = f"file:{db_name}?mode=memory&cache=shared"
    engine = create_engine(
        f"sqlite:///{uri}",
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session, engine


@settings(max_examples=100)
@given(
    camera_id=camera_id_st,
    file_path=file_path_st,
    duration_sec=duration_st,
    captured_at=captured_at_st,
    retention_days=retention_st,
    final_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
)
def test_p9_websocket_broadcast_on_clip_record_creation(
    camera_id, file_path, duration_sec, captured_at, retention_days, final_score
):
    """
    # Feature: smart-bin-video-retention, Property 9: WebSocket broadcast on ClipRecord creation

    For any successfully created ClipRecord, ws_manager.broadcast() is called
    exactly once with a message containing type == "alert", the correct
    camera_id, and the correct clip_id.

    Validates: Requirements 4.2
    """
    Session, engine = _make_shared_session()

    # Seed required SystemSetting rows so the service proceeds
    seed_session = Session()
    try:
        from backend.db.models import SystemSetting
        seed_session.add(SystemSetting(key="smart_bin_enabled", value="true"))
        seed_session.add(SystemSetting(key="clip_duration_seconds", value=str(duration_sec)))
        seed_session.add(SystemSetting(key="clip_retention_days", value=str(retention_days)))

        # Create an Alert row to associate with
        alert = Alert(
            timestamp=captured_at,
            level="critical",
            risk_score=final_score,
            camera_id=camera_id,
            location="test-location",
            video_clip_path=None,
        )
        seed_session.add(alert)
        seed_session.commit()
        seed_session.refresh(alert)
        alert_id = alert.id
    finally:
        seed_session.close()

    # Build a mock ws_manager that captures broadcast calls
    mock_ws = MagicMock()
    mock_ws.broadcast = AsyncMock()

    # Build a mock video_storage_service that returns fake bytes
    mock_vss = MagicMock()
    mock_vss.get_segment = MagicMock(return_value=b"fake")

    with (
        patch("backend.services.clip_capture_service.ws_manager", mock_ws),
        patch("backend.services.clip_capture_service.video_storage_service", mock_vss),
        patch("backend.services.clip_capture_service.SessionLocal", Session),
        patch("os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        svc = ClipCaptureService()
        result = asyncio.get_event_loop().run_until_complete(
            svc.handle_threshold_crossing(
                camera_id=camera_id,
                timestamp=captured_at,
                final_score=final_score,
                alert_id=alert_id,
            )
        )

    # The service must have returned a ClipRecord (not None)
    assert result is not None, (
        "handle_threshold_crossing returned None; expected a ClipRecord"
    )

    # broadcast() must have been called exactly once
    assert mock_ws.broadcast.call_count == 1, (
        f"Expected ws_manager.broadcast to be called exactly once, "
        f"got {mock_ws.broadcast.call_count} call(s)"
    )

    # Inspect the broadcast payload
    broadcast_payload = mock_ws.broadcast.call_args[0][0]

    assert broadcast_payload.get("type") == "alert", (
        f"Expected broadcast type='alert', got {broadcast_payload.get('type')!r}"
    )
    assert broadcast_payload.get("camera_id") == camera_id, (
        f"Expected broadcast camera_id={camera_id!r}, "
        f"got {broadcast_payload.get('camera_id')!r}"
    )
    assert broadcast_payload.get("clip_id") == result.id, (
        f"Expected broadcast clip_id={result.id}, "
        f"got {broadcast_payload.get('clip_id')!r}"
    )

    engine.dispose()
