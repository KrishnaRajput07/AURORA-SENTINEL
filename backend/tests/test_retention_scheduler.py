"""
Unit tests for RetentionScheduler.

Covers:
- Empty DB → run_once returns 0
- All records expired → all deleted, returns correct count
- No records expired → none deleted, returns 0
- Mixed → only expired records deleted
- Missing file (FileNotFoundError) → DB row still deleted
- File deletion OS error → DB row retained

Requirements: 7.1–7.6
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401
from backend.db.database import Base
from backend.services.retention_scheduler import RetentionScheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_db():
    """In-memory SQLite with a unique name so tests are fully isolated."""
    db_name = f"test_{uuid.uuid4().hex}"
    db_url = f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    return engine, TestSession


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# Fixed reference point for all tests
NOW = datetime(2025, 6, 1, 12, 0, 0)
PAST = NOW - timedelta(days=1)
FUTURE = NOW + timedelta(days=1)


def insert_clip(session: Session, expires_at: datetime, file_path: str = None) -> ClipRecord:
    record = ClipRecord(
        camera_id="cam_test",
        file_path=file_path or f"/fake/{uuid.uuid4().hex}.mp4",
        duration_sec=10,
        captured_at=datetime(2024, 1, 1),
        expires_at=expires_at,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def make_scheduler_with_patched_now(now: datetime):
    """Return a RetentionScheduler and a context-manager that patches datetime.utcnow."""
    mock_dt = MagicMock()
    mock_dt.utcnow.return_value = now
    return RetentionScheduler(), mock_dt


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_db():
    """No ClipRecords → run_once returns 0."""
    _, TestSession = make_test_db()
    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove"):
        db: Session = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    assert deleted == 0


def test_all_expired():
    """All records expired → all deleted, returns correct count."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        r1 = insert_clip(db, expires_at=PAST)
        r2 = insert_clip(db, expires_at=PAST)
        r3 = insert_clip(db, expires_at=PAST)
    finally:
        db.close()

    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove"):
        db = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    assert deleted == 3

    db = TestSession()
    try:
        assert db.query(ClipRecord).count() == 0
    finally:
        db.close()


def test_none_expired():
    """No records expired → none deleted, returns 0."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        insert_clip(db, expires_at=FUTURE)
        insert_clip(db, expires_at=FUTURE)
    finally:
        db.close()

    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove"):
        db = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    assert deleted == 0

    db = TestSession()
    try:
        assert db.query(ClipRecord).count() == 2
    finally:
        db.close()


def test_mixed():
    """Some expired, some not → only expired records deleted."""
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        expired1 = insert_clip(db, expires_at=PAST)
        expired2 = insert_clip(db, expires_at=PAST)
        kept1 = insert_clip(db, expires_at=FUTURE)
        kept2 = insert_clip(db, expires_at=FUTURE)
    finally:
        db.close()

    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove"):
        db = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    assert deleted == 2

    db = TestSession()
    try:
        remaining_ids = {r.id for r in db.query(ClipRecord).all()}
    finally:
        db.close()

    assert expired1.id not in remaining_ids
    assert expired2.id not in remaining_ids
    assert kept1.id in remaining_ids
    assert kept2.id in remaining_ids


def test_missing_file():
    """
    File not found (FileNotFoundError) → DB row is still deleted.
    Requirement 7.4: missing file logs warning but record is removed.
    """
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        record = insert_clip(db, expires_at=PAST, file_path="/nonexistent/clip.mp4")
    finally:
        db.close()

    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove", side_effect=FileNotFoundError("no such file")):
        db = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    # Should count as deleted (DB row removed)
    assert deleted == 1

    db = TestSession()
    try:
        assert db.query(ClipRecord).filter(ClipRecord.id == record.id).count() == 0
    finally:
        db.close()


def test_file_deletion_error():
    """
    os.remove raises OSError (not FileNotFoundError) → DB row is retained.
    Requirement 7.5: file I/O error keeps the record for retry on next run.
    """
    _, TestSession = make_test_db()
    db: Session = TestSession()
    try:
        record = insert_clip(db, expires_at=PAST, file_path="/locked/clip.mp4")
    finally:
        db.close()

    scheduler, mock_dt = make_scheduler_with_patched_now(NOW)

    with patch("backend.services.retention_scheduler.datetime", mock_dt), \
         patch("os.remove", side_effect=OSError("permission denied")):
        db = TestSession()
        try:
            deleted = run(scheduler.run_once(db))
        finally:
            db.close()

    # Should NOT count as deleted (DB row retained)
    assert deleted == 0

    db = TestSession()
    try:
        assert db.query(ClipRecord).filter(ClipRecord.id == record.id).count() == 1
    finally:
        db.close()
