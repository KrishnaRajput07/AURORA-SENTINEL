# Feature: smart-bin-video-retention, Property 15: Retention scheduler identifies exactly the expired records
"""
Property-based tests for RetentionScheduler.

P15: Retention scheduler identifies exactly the expired records
P16: Expired records and files are fully removed; file errors preserve the record
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import Alert, ClipRecord, SystemSetting  # noqa: F401
from backend.db.database import Base
from backend.services.retention_scheduler import RetentionScheduler


# ---------------------------------------------------------------------------
# Shared test infrastructure
# ---------------------------------------------------------------------------

def make_test_db():
    """
    Return (engine, TestSession) backed by a uniquely-named shared in-memory
    SQLite database.
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


def run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def insert_clip(session: Session, expires_at: datetime, file_path: str = None) -> ClipRecord:
    """Insert a ClipRecord with the given expires_at and return it."""
    record = ClipRecord(
        camera_id="cam_test",
        file_path=file_path or f"/fake/path/{uuid.uuid4().hex}.mp4",
        duration_sec=10,
        captured_at=datetime(2024, 1, 1, 0, 0, 0),
        expires_at=expires_at,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# A "now" datetime in a reasonable range
_now_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 1, 1),
)

# Offsets in seconds: negative = before now (expired), positive = after now (not expired)
_offset_strategy = st.integers(min_value=-365 * 24 * 3600, max_value=365 * 24 * 3600)


# ---------------------------------------------------------------------------
# Property 15: Retention scheduler identifies exactly the expired records
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    offsets=st.lists(_offset_strategy, min_size=0, max_size=10),
    now=_now_strategy,
)
def test_p15_scheduler_identifies_exactly_expired_records(
    offsets: list, now: datetime
):
    """
    # Feature: smart-bin-video-retention, Property 15: Retention scheduler identifies exactly the expired records

    For any set of ClipRecord rows with mixed expires_at values and a given
    "current time" now, RetentionScheduler.run_once() should attempt deletion
    of exactly those records where expires_at < now and leave all others
    untouched.

    Validates: Requirements 7.2
    """
    _, TestSession = make_test_db()

    # Insert records: each offset determines expires_at relative to now
    db: Session = TestSession()
    inserted_ids = []
    expired_ids = set()
    try:
        for offset in offsets:
            expires_at = now + timedelta(seconds=offset)
            record = insert_clip(db, expires_at=expires_at)
            inserted_ids.append(record.id)
            if expires_at < now:
                expired_ids.add(record.id)
    finally:
        db.close()

    scheduler = RetentionScheduler()

    # Patch os.remove to succeed silently (no real files)
    # Patch datetime.utcnow in the scheduler module to return our test "now"
    mock_datetime = MagicMock()
    mock_datetime.utcnow.return_value = now

    with patch("backend.services.retention_scheduler.datetime", mock_datetime), \
         patch("os.remove"):
        db = TestSession()
        try:
            run(scheduler.run_once(db))
        finally:
            db.close()

    # Verify: expired records are gone, non-expired remain
    db = TestSession()
    try:
        remaining_ids = {r.id for r in db.query(ClipRecord).all()}
    finally:
        db.close()

    non_expired_ids = set(inserted_ids) - expired_ids

    assert expired_ids.isdisjoint(remaining_ids), (
        f"Some expired records were NOT deleted: "
        f"{expired_ids & remaining_ids}"
    )
    assert non_expired_ids == remaining_ids, (
        f"Some non-expired records were incorrectly deleted. "
        f"Expected remaining: {non_expired_ids}, got: {remaining_ids}"
    )


# ---------------------------------------------------------------------------
# Property 16: Expired records and files are fully removed; file errors preserve the record
# ---------------------------------------------------------------------------

# Strategy for the file-deletion outcome of each expired record:
#   "ok"           → os.remove succeeds
#   "missing"      → os.remove raises FileNotFoundError (DB row still deleted)
#   "os_error"     → os.remove raises OSError (DB row retained)
_deletion_outcome = st.sampled_from(["ok", "missing", "os_error"])


@settings(max_examples=100)
@given(
    expired_outcomes=st.lists(_deletion_outcome, min_size=0, max_size=8),
    non_expired_count=st.integers(min_value=0, max_value=5),
)
def test_p16_expired_records_fully_removed_file_errors_preserve_record(
    expired_outcomes: list,
    non_expired_count: int,
):
    """
    # Feature: smart-bin-video-retention, Property 16: Expired records and files are fully removed; file errors preserve the record

    For expired ClipRecords:
    - After a successful run_once, both the file and the DB row are absent.
    - If os.remove raises FileNotFoundError, the DB row is still deleted.
    - If os.remove raises a non-FileNotFoundError OSError, the DB row is retained.

    Non-expired records are never touched.

    Validates: Requirements 7.3, 7.4, 7.5, 7.6
    """
    now = datetime(2025, 6, 1, 12, 0, 0)
    past = now - timedelta(days=1)
    future = now + timedelta(days=1)

    _, TestSession = make_test_db()

    # Insert expired records, one per outcome
    db: Session = TestSession()
    expired_records = []  # list of (record_id, file_path, outcome)
    non_expired_ids = set()
    try:
        for outcome in expired_outcomes:
            fp = f"/fake/expired/{uuid.uuid4().hex}.mp4"
            record = insert_clip(db, expires_at=past, file_path=fp)
            expired_records.append((record.id, fp, outcome))

        for _ in range(non_expired_count):
            record = insert_clip(db, expires_at=future)
            non_expired_ids.add(record.id)
    finally:
        db.close()

    scheduler = RetentionScheduler()

    # Build a per-path side-effect map for os.remove
    remove_effects: dict = {}
    for _, fp, outcome in expired_records:
        if outcome == "missing":
            remove_effects[fp] = FileNotFoundError(f"no such file: {fp}")
        elif outcome == "os_error":
            remove_effects[fp] = OSError(f"permission denied: {fp}")
        # "ok" → no entry (remove succeeds)

    def fake_remove(path):
        if path in remove_effects:
            raise remove_effects[path]

    mock_datetime = MagicMock()
    mock_datetime.utcnow.return_value = now

    with patch("backend.services.retention_scheduler.datetime", mock_datetime), \
         patch("os.remove", side_effect=fake_remove):
        db = TestSession()
        try:
            run(scheduler.run_once(db))
        finally:
            db.close()

    db = TestSession()
    try:
        remaining_ids = {r.id for r in db.query(ClipRecord).all()}
    finally:
        db.close()

    # Non-expired records must all still be present
    assert non_expired_ids.issubset(remaining_ids), (
        f"Non-expired records were deleted: {non_expired_ids - remaining_ids}"
    )

    for record_id, fp, outcome in expired_records:
        if outcome in ("ok", "missing"):
            # DB row must be gone
            assert record_id not in remaining_ids, (
                f"Expired record id={record_id} (outcome={outcome}) should have been "
                f"deleted from DB but was not."
            )
        elif outcome == "os_error":
            # DB row must be retained
            assert record_id in remaining_ids, (
                f"Expired record id={record_id} (outcome=os_error) should have been "
                f"retained in DB but was deleted."
            )
