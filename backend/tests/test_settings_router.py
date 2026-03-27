"""
Unit tests for the settings router — boundary values and GET /{key} behaviour.

Covers:
- clip_duration_seconds: min (5), max (300), below min (4), above max (301)
- clip_retention_days:   min (1), max (365), below min (0), above max (366)
- Out-of-range POST returns HTTP 422 and does NOT mutate the DB
- In-range boundary POST returns HTTP 200 and IS persisted
- GET /settings/{key} returns 404 for a missing key
- GET /settings/{key} returns 200 with the correct value for an existing key

Requirements: 2.2, 2.3, 6.2, 6.3
"""

import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.db.models import SystemSetting, Alert, ClipRecord  # noqa: F401 — register all tables
from backend.db.database import Base
from backend.api.routers import settings as settings_router
from backend.api.deps import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_app():
    """Return a (TestClient, TestSession) pair backed by a fresh in-memory SQLite DB."""
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

    return TestClient(app, raise_server_exceptions=True), TestSession


def seed_setting(TestSession, key: str, value: str) -> None:
    db: Session = TestSession()
    try:
        db.add(SystemSetting(key=key, value=value))
        db.commit()
    finally:
        db.close()


def read_setting(TestSession, key: str):
    db: Session = TestSession()
    try:
        return db.query(SystemSetting).filter(SystemSetting.key == key).first()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# clip_duration_seconds — boundary values
# ---------------------------------------------------------------------------

class TestClipDurationBoundaries:
    KEY = "clip_duration_seconds"
    SEED = "10"

    def test_min_value_accepted(self):
        """POST clip_duration_seconds=5 (min) → 200 and value persisted."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "5"})

        assert resp.status_code == 200
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == "5"

    def test_max_value_accepted(self):
        """POST clip_duration_seconds=300 (max) → 200 and value persisted."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "300"})

        assert resp.status_code == 200
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == "300"

    def test_below_min_rejected(self):
        """POST clip_duration_seconds=4 (below min) → 422 and DB unchanged."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "4"})

        assert resp.status_code == 422
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == self.SEED  # unchanged

    def test_above_max_rejected(self):
        """POST clip_duration_seconds=301 (above max) → 422 and DB unchanged."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "301"})

        assert resp.status_code == 422
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == self.SEED  # unchanged


# ---------------------------------------------------------------------------
# clip_retention_days — boundary values
# ---------------------------------------------------------------------------

class TestClipRetentionBoundaries:
    KEY = "clip_retention_days"
    SEED = "10"

    def test_min_value_accepted(self):
        """POST clip_retention_days=1 (min) → 200 and value persisted."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "1"})

        assert resp.status_code == 200
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == "1"

    def test_max_value_accepted(self):
        """POST clip_retention_days=365 (max) → 200 and value persisted."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "365"})

        assert resp.status_code == 200
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == "365"

    def test_below_min_rejected(self):
        """POST clip_retention_days=0 (below min) → 422 and DB unchanged."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "0"})

        assert resp.status_code == 422
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == self.SEED  # unchanged

    def test_above_max_rejected(self):
        """POST clip_retention_days=366 (above max) → 422 and DB unchanged."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, self.KEY, self.SEED)

        resp = client.post(f"/{self.KEY}", json={"value": "366"})

        assert resp.status_code == 422
        row = read_setting(TestSession, self.KEY)
        assert row is not None
        assert row.value == self.SEED  # unchanged


# ---------------------------------------------------------------------------
# GET /{key} — missing key and existing key
# ---------------------------------------------------------------------------

class TestGetSetting:
    def test_missing_key_returns_404(self):
        """GET /settings/nonexistent_key → 404."""
        client, _ = make_test_app()

        resp = client.get("/nonexistent_key_xyz")

        assert resp.status_code == 404

    def test_existing_key_returns_200_with_value(self):
        """GET /settings/{key} for a seeded key → 200 with correct key/value."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, "clip_duration_seconds", "42")

        resp = client.get("/clip_duration_seconds")

        assert resp.status_code == 200
        body = resp.json()
        assert body["key"] == "clip_duration_seconds"
        assert body["value"] == "42"

    def test_existing_retention_key_returns_200_with_value(self):
        """GET /settings/clip_retention_days for a seeded key → 200 with correct value."""
        client, TestSession = make_test_app()
        seed_setting(TestSession, "clip_retention_days", "30")

        resp = client.get("/clip_retention_days")

        assert resp.status_code == 200
        body = resp.json()
        assert body["key"] == "clip_retention_days"
        assert body["value"] == "30"
