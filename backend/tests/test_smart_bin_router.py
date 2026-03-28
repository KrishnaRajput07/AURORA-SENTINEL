"""
Unit tests for the Smart Bin REST API router.

Covers:
1. test_list_clips_empty          — no clips → 200 with empty list
2. test_list_clips_ordered        — 3 clips with different timestamps → desc order
3. test_list_clips_excludes_expired — mix of expired/non-expired → only non-expired
4. test_get_clip_found            — existing clip → 200 with correct data
5. test_get_clip_not_found        — non-existent id → 404
6. test_stream_clip_not_found_record — non-existent id → 404
7. test_stream_clip_file_missing  — record exists but file not on disk → 404
8. test_stream_clip_success       — record exists and file exists → 200 FileResponse
9. test_required_fields_present   — response includes camera_id, captured_at,
                                    duration_sec, expires_at

Requirements: 5.1–5.5
"""

import os
import tempfile
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401
from backend.db.database import Base
from backend.api.routers import smart_bin
from backend.api.deps import get_db


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

def make_test_app():
    """Return (TestClient, TestSession) backed by a fresh in-memory SQLite DB."""
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
    camera_id: str = "cam_01",
    file_path: str = None,
    duration_sec: int = 10,
) -> ClipRecord:
    record = ClipRecord(
        camera_id=camera_id,
        file_path=file_path or f"/fake/{uuid.uuid4().hex}.mp4",
        duration_sec=duration_sec,
        captured_at=captured_at,
        expires_at=expires_at,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


# Convenience datetimes
NOW = datetime(2025, 6, 1, 12, 0, 0)
FUTURE = NOW + timedelta(days=30)
PAST = NOW - timedelta(days=1)


# ---------------------------------------------------------------------------
# 1. test_list_clips_empty
# ---------------------------------------------------------------------------

def test_list_clips_empty():
    """No clips in DB → GET /clips returns 200 with an empty list."""
    client, _ = make_test_app()

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = NOW
        response = client.get("/clips")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# 2. test_list_clips_ordered
# ---------------------------------------------------------------------------

def test_list_clips_ordered():
    """3 clips with different timestamps → returned in captured_at descending order."""
    client, TestSession = make_test_app()

    ts1 = datetime(2025, 1, 1, 8, 0, 0)
    ts2 = datetime(2025, 3, 15, 12, 0, 0)
    ts3 = datetime(2025, 5, 20, 18, 0, 0)

    db: Session = TestSession()
    try:
        insert_clip(db, captured_at=ts1, expires_at=FUTURE)
        insert_clip(db, captured_at=ts2, expires_at=FUTURE)
        insert_clip(db, captured_at=ts3, expires_at=FUTURE)
    finally:
        db.close()

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = NOW
        response = client.get("/clips")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    returned_timestamps = [item["captured_at"] for item in data]
    assert returned_timestamps == sorted(returned_timestamps, reverse=True), (
        f"Expected descending order, got: {returned_timestamps}"
    )


# ---------------------------------------------------------------------------
# 3. test_list_clips_excludes_expired
# ---------------------------------------------------------------------------

def test_list_clips_excludes_expired():
    """Mix of expired and non-expired clips → only non-expired are returned."""
    client, TestSession = make_test_app()

    db: Session = TestSession()
    try:
        non_expired = insert_clip(db, captured_at=datetime(2025, 5, 1), expires_at=FUTURE)
        insert_clip(db, captured_at=datetime(2025, 4, 1), expires_at=PAST)   # expired
        insert_clip(db, captured_at=datetime(2025, 3, 1), expires_at=PAST)   # expired
    finally:
        db.close()

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = NOW
        response = client.get("/clips")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == non_expired.id


# ---------------------------------------------------------------------------
# 4. test_get_clip_found
# ---------------------------------------------------------------------------

def test_get_clip_found():
    """GET /clips/{id} for an existing clip → 200 with correct data."""
    client, TestSession = make_test_app()

    db: Session = TestSession()
    try:
        clip = insert_clip(
            db,
            captured_at=datetime(2025, 5, 10, 9, 0, 0),
            expires_at=FUTURE,
            camera_id="cam_42",
            duration_sec=30,
        )
        clip_id = clip.id
    finally:
        db.close()

    response = client.get(f"/clips/{clip_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == clip_id
    assert data["camera_id"] == "cam_42"
    assert data["duration_sec"] == 30


# ---------------------------------------------------------------------------
# 5. test_get_clip_not_found
# ---------------------------------------------------------------------------

def test_get_clip_not_found():
    """GET /clips/{id} for a non-existent id → 404."""
    client, _ = make_test_app()

    response = client.get("/clips/99999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. test_stream_clip_not_found_record
# ---------------------------------------------------------------------------

def test_stream_clip_not_found_record():
    """GET /clips/{id}/stream for a non-existent id → 404."""
    client, _ = make_test_app()

    response = client.get("/clips/99999/stream")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 7. test_stream_clip_file_missing
# ---------------------------------------------------------------------------

def test_stream_clip_file_missing():
    """Record exists but file is not on disk → 404."""
    client, TestSession = make_test_app()

    db: Session = TestSession()
    try:
        clip = insert_clip(
            db,
            captured_at=datetime(2025, 5, 1),
            expires_at=FUTURE,
            file_path="/nonexistent/path/clip.mp4",
        )
        clip_id = clip.id
    finally:
        db.close()

    response = client.get(f"/clips/{clip_id}/stream")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 8. test_stream_clip_success
# ---------------------------------------------------------------------------

def test_stream_clip_success():
    """Record exists and file exists on disk → 200 with video/mp4 content."""
    client, TestSession = make_test_app()

    # Create a real temporary file to serve
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(b"fake mp4 content")
        tmp_path = tmp.name

    try:
        db: Session = TestSession()
        try:
            clip = insert_clip(
                db,
                captured_at=datetime(2025, 5, 1),
                expires_at=FUTURE,
                file_path=tmp_path,
            )
            clip_id = clip.id
        finally:
            db.close()

        response = client.get(f"/clips/{clip_id}/stream")

        assert response.status_code == 200
        assert "video/mp4" in response.headers.get("content-type", "")
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# 9. test_required_fields_present
# ---------------------------------------------------------------------------

def test_required_fields_present():
    """GET /clips response includes camera_id, captured_at, duration_sec, expires_at."""
    client, TestSession = make_test_app()

    db: Session = TestSession()
    try:
        insert_clip(
            db,
            captured_at=datetime(2025, 5, 1, 10, 0, 0),
            expires_at=FUTURE,
            camera_id="cam_fields",
            duration_sec=15,
        )
    finally:
        db.close()

    with patch("backend.api.routers.smart_bin.datetime") as mock_dt:
        mock_dt.utcnow.return_value = NOW
        response = client.get("/clips")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    item = data[0]
    required_fields = {"camera_id", "captured_at", "duration_sec", "expires_at"}
    for field in required_fields:
        assert field in item, f"Missing required field: {field}"
        assert item[field] is not None, f"Required field '{field}' is None"
