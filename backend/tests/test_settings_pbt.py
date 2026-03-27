# Feature: smart-bin-video-retention, Property 2: Input validation rejects out-of-range clip duration
"""
Property-based tests for the settings API.

P2: For any integer value submitted as clip_duration_seconds, the settings API
    should accept it if and only if the value is in [5, 300]; values outside
    this range should be rejected with HTTP 422 and the SystemSetting row
    should remain unchanged.

Validates: Requirements 2.2, 2.3
"""

import uuid
from hypothesis import given, settings
from hypothesis import strategies as st
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import all models before create_all so their tables are registered on Base
from backend.db.models import SystemSetting, Alert, ClipRecord  # noqa: F401
from backend.db.database import Base
from backend.api.routers import settings as settings_router
from backend.api.deps import get_db


# ---------------------------------------------------------------------------
# In-memory SQLite test app setup
# ---------------------------------------------------------------------------

def make_test_app():
    """
    Create a fresh FastAPI app backed by a uniquely-named shared in-memory
    SQLite database.  Using a named URI (cache=shared) ensures all connections
    within the same process see the same in-memory database, which is required
    because FastAPI's TestClient runs requests in a worker thread.
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
    app.include_router(settings_router.router)

    return app, TestSession


# ---------------------------------------------------------------------------
# Property 2: Input validation rejects out-of-range clip duration
# ---------------------------------------------------------------------------

CLIP_DURATION_KEY = "clip_duration_seconds"
CLIP_DURATION_MIN = 5
CLIP_DURATION_MAX = 300

# Strategy: integers spanning both in-range and out-of-range values
clip_duration_st = st.integers(min_value=-1000, max_value=1000)


@settings(max_examples=100)
@given(value=clip_duration_st)
def test_p2_clip_duration_validation(value: int):
    """
    # Feature: smart-bin-video-retention, Property 2: Input validation rejects out-of-range clip duration

    For any integer submitted as clip_duration_seconds:
    - If value ∈ [5, 300]: API returns 200 and persists the value.
    - If value ∉ [5, 300]: API returns 422 and the SystemSetting row is unchanged.

    Validates: Requirements 2.2, 2.3
    """
    app, TestSession = make_test_app()
    client = TestClient(app, raise_server_exceptions=True)

    in_range = CLIP_DURATION_MIN <= value <= CLIP_DURATION_MAX

    # Seed a pre-existing value so we can verify it is unchanged on rejection
    seed_value = "10"
    db: Session = TestSession()
    try:
        existing = SystemSetting(key=CLIP_DURATION_KEY, value=seed_value)
        db.add(existing)
        db.commit()
    finally:
        db.close()

    # Submit the value under test
    response = client.post(
        f"/{CLIP_DURATION_KEY}",
        json={"value": str(value)},
    )

    if in_range:
        assert response.status_code == 200, (
            f"Expected 200 for in-range value {value}, got {response.status_code}: {response.text}"
        )
        # Verify the value was persisted
        db = TestSession()
        try:
            row = db.query(SystemSetting).filter(SystemSetting.key == CLIP_DURATION_KEY).first()
            assert row is not None, "SystemSetting row should exist after successful POST"
            assert row.value == str(value), (
                f"Expected persisted value={value!r}, got {row.value!r}"
            )
        finally:
            db.close()
    else:
        assert response.status_code == 422, (
            f"Expected 422 for out-of-range value {value}, got {response.status_code}: {response.text}"
        )
        # Verify the row was NOT mutated — still holds the seed value
        db = TestSession()
        try:
            row = db.query(SystemSetting).filter(SystemSetting.key == CLIP_DURATION_KEY).first()
            assert row is not None, "SystemSetting row should still exist after rejected POST"
            assert row.value == seed_value, (
                f"Expected unchanged value={seed_value!r} after 422, got {row.value!r}"
            )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Property 13: Input validation rejects out-of-range retention period
# ---------------------------------------------------------------------------
# Feature: smart-bin-video-retention, Property 13: Input validation rejects out-of-range retention period

CLIP_RETENTION_KEY = "clip_retention_days"
CLIP_RETENTION_MIN = 1
CLIP_RETENTION_MAX = 365

# Strategy: integers spanning both in-range and out-of-range values
clip_retention_st = st.integers(min_value=-1000, max_value=1000)


@settings(max_examples=100)
@given(value=clip_retention_st)
def test_p13_retention_period_validation(value: int):
    """
    # Feature: smart-bin-video-retention, Property 13: Input validation rejects out-of-range retention period

    For any integer submitted as clip_retention_days:
    - If value ∈ [1, 365]: API returns 200 and persists the value.
    - If value ∉ [1, 365]: API returns 422 and the SystemSetting row is unchanged.

    Validates: Requirements 6.2, 6.3
    """
    app, TestSession = make_test_app()
    client = TestClient(app, raise_server_exceptions=True)

    in_range = CLIP_RETENTION_MIN <= value <= CLIP_RETENTION_MAX

    # Seed a pre-existing value so we can verify it is unchanged on rejection
    seed_value = "10"
    db: Session = TestSession()
    try:
        existing = SystemSetting(key=CLIP_RETENTION_KEY, value=seed_value)
        db.add(existing)
        db.commit()
    finally:
        db.close()

    # Submit the value under test
    response = client.post(
        f"/{CLIP_RETENTION_KEY}",
        json={"value": str(value)},
    )

    if in_range:
        assert response.status_code == 200, (
            f"Expected 200 for in-range value {value}, got {response.status_code}: {response.text}"
        )
        # Verify the value was persisted
        db = TestSession()
        try:
            row = db.query(SystemSetting).filter(SystemSetting.key == CLIP_RETENTION_KEY).first()
            assert row is not None, "SystemSetting row should exist after successful POST"
            assert row.value == str(value), (
                f"Expected persisted value={value!r}, got {row.value!r}"
            )
        finally:
            db.close()
    else:
        assert response.status_code == 422, (
            f"Expected 422 for out-of-range value {value}, got {response.status_code}: {response.text}"
        )
        # Verify the row was NOT mutated — still holds the seed value
        db = TestSession()
        try:
            row = db.query(SystemSetting).filter(SystemSetting.key == CLIP_RETENTION_KEY).first()
            assert row is not None, "SystemSetting row should still exist after rejected POST"
            assert row.value == seed_value, (
                f"Expected unchanged value={seed_value!r} after 422, got {row.value!r}"
            )
        finally:
            db.close()
