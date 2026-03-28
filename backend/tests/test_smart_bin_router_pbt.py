# Feature: smart-bin-video-retention, Property 11: Smart Bin API returns clips ordered by timestamp descending
# Feature: smart-bin-video-retention, Property 12: Smart Bin API excludes expired clips and includes required fields
"""
Property-based tests for the Smart Bin REST API router.

P11: Smart Bin API returns clips ordered by timestamp descending
P12: Smart Bin API excludes expired clips and includes required fields
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401 — register all tables
from backend.db.database import Base
from backend.api.routers import smart_bin
from backend.api.deps import get_db


# ---------------------------------------------------------------------------
# Shared test infrastructure
# ---------------------------------------------------------------------------

def make_test_app():
    """
    Return (TestClient, TestSession) backed by a fresh uniquely-named
    in-memory SQLite database.
    """
    db_name = f"test_{uuid.uuid4().hex}"
    db_url = f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    app = FastAPI()

    def override_get_db():
        db: Session = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(smart_bin.router)

    return TestClient(app, raise_server_exceptions=True), TestSession


def insert_clip(
    session: Session,
    captured_at: datetime,
    expires_at: datetime,
    camera_id: str = "cam_test",
) -> ClipRecord:
    """Insert a ClipRecord and return it."""
    record = ClipRecord(
        camera_id=camera_id,
        file_path=f"/fake/path/{uuid.uuid4().hex}.mp4",
        duration_sec=10,
        captured_at=captured_at,
        expires_at=expires_at,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Property 11: Smart Bin API returns clips ordered by timestamp descending
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    captured_ats=st.lists(
        st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)),
        min_size=0,
        max_size=10,
    )
)
def test_p11_clips_ordered_by_timestamp_descending(captured_ats: list):
    """
    # Feature: smart-bin-video-retention, Property 11: Smart Bin API returns clips ordered by timestamp descending

    For any set of ClipRecord rows in the database, GET /clips should return
    them sorted by captured_at descending.

    Validates: Requirements 5.1
    """
    client, TestSession = make_test_app()

    # All clips are non-expired (expires_at far in the future)
    future = datetime(2099, 12, 31, 23, 59, 59)

    db: Session = TestSession()
    try:
        for captured_at in captured_ats:
            insert_clip(db, captured_at=captured_at, expires_at=future)
    finally:
        db.close()

    # Fix "now" to a point well before all expires_at values
    fixed_now = datetime(2024, 1, 1, 0, 0, 0)

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = fixed_now

        response = client.get("/clips")

    assert response.status_code == 200
    data = response.json()

    returned_timestamps = [item["captured_at"] for item in data]

    # Verify descending order
    assert returned_timestamps == sorted(returned_timestamps, reverse=True), (
        f"Expected clips ordered by captured_at descending, got: {returned_timestamps}"
    )


# ---------------------------------------------------------------------------
# Property 12: Smart Bin API excludes expired clips and includes required fields
# ---------------------------------------------------------------------------

# Strategy: each clip is described by an offset in seconds from "now".
# Negative offset → expires_at is in the past (expired).
# Positive offset → expires_at is in the future (non-expired).
_offset_strategy = st.integers(
    min_value=-365 * 24 * 3600,
    max_value=365 * 24 * 3600,
)

_FIXED_NOW = datetime(2025, 6, 1, 12, 0, 0)


@settings(max_examples=100)
@given(
    offsets=st.lists(_offset_strategy, min_size=0, max_size=10),
)
def test_p12_expired_clips_excluded_and_required_fields_present(offsets: list):
    """
    # Feature: smart-bin-video-retention, Property 12: Smart Bin API excludes expired clips and includes required fields

    For any set of ClipRecord rows with mixed expires_at values,
    GET /clips should return only those where expires_at >= utcnow(), and
    each returned record should include camera_id, captured_at, duration_sec,
    and expires_at.

    Validates: Requirements 5.2, 5.5
    """
    client, TestSession = make_test_app()

    now = _FIXED_NOW
    captured_base = datetime(2024, 1, 1, 0, 0, 0)

    db: Session = TestSession()
    non_expired_ids = set()
    try:
        for i, offset in enumerate(offsets):
            expires_at = now + timedelta(seconds=offset)
            captured_at = captured_base + timedelta(hours=i)
            record = insert_clip(db, captured_at=captured_at, expires_at=expires_at)
            if expires_at >= now:
                non_expired_ids.add(record.id)
    finally:
        db.close()

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = now

        response = client.get("/clips")

    assert response.status_code == 200
    data = response.json()

    returned_ids = {item["id"] for item in data}

    # Only non-expired clips should be returned
    assert returned_ids == non_expired_ids, (
        f"Expected only non-expired clip IDs {non_expired_ids}, got {returned_ids}"
    )

    # Each returned record must include the required fields
    required_fields = {"camera_id", "captured_at", "duration_sec", "expires_at"}
    for item in data:
        missing = required_fields - item.keys()
        assert not missing, (
            f"Clip id={item.get('id')} is missing required fields: {missing}"
        )
        # Values must not be None
        for field in required_fields:
            assert item[field] is not None, (
                f"Clip id={item.get('id')} has None value for required field '{field}'"
            )
