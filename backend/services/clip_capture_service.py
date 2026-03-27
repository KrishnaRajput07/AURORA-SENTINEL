"""
ClipCaptureService — captures video clips on threat escalation.

Called by the scoring pipeline after should_alert is True.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Set

from backend.db.database import SessionLocal
from backend.db.models import Alert, ClipRecord, SystemSetting
from backend.services.video_storage_service import video_storage_service
from backend.services.ws_manager import manager as ws_manager

logger = logging.getLogger(__name__)

_BIN_DIR = os.path.join("storage", "bin")


class ClipCaptureService:
    def __init__(self):
        # In-memory dedup set: prevents duplicate captures per (camera_id, alert_id)
        self._captured: Set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def handle_threshold_crossing(
        self,
        camera_id: str,
        timestamp: datetime,
        final_score: float,
        alert_id: Optional[int],
    ) -> Optional[ClipRecord]:
        """
        Capture a clip for the given threshold-crossing event.

        Returns the created ClipRecord on success, or None if the feature is
        disabled, a duplicate is detected, or an error occurs.
        """
        db = SessionLocal()
        try:
            if not self._is_enabled(db):
                return None

            dedup = self._dedup_key(camera_id, alert_id)
            if dedup in self._captured:
                logger.debug("Duplicate capture skipped for %s", dedup)
                return None

            duration = self._get_clip_duration(db)
            retention = self._get_retention_days(db)

            # Retrieve video segment
            try:
                video_bytes = video_storage_service.get_segment(camera_id, timestamp, duration)
            except Exception as exc:
                logger.error(
                    "ClipCaptureService: VideoStorageService error for camera=%s ts=%s: %s",
                    camera_id, timestamp, exc,
                )
                return None

            # Write clip file
            os.makedirs(_BIN_DIR, exist_ok=True)
            ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{camera_id}_{ts_str}.mp4"
            file_path = os.path.join(_BIN_DIR, filename)
            try:
                with open(file_path, "wb") as f:
                    f.write(video_bytes)
            except Exception as exc:
                logger.error(
                    "ClipCaptureService: file write error for camera=%s ts=%s path=%s: %s",
                    camera_id, timestamp, file_path, exc,
                )
                return None

            # Insert ClipRecord
            expires_at = timestamp + timedelta(days=retention)
            record = ClipRecord(
                camera_id=camera_id,
                alert_id=alert_id,
                file_path=file_path,
                duration_sec=duration,
                captured_at=timestamp,
                expires_at=expires_at,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            # Mark dedup
            self._captured.add(dedup)

            # Associate clip with alert
            if alert_id is not None:
                self._attach_clip_to_alert(alert_id, file_path, db)

            # Broadcast WebSocket event
            await ws_manager.broadcast({
                "type": "alert",
                "alert_id": alert_id,
                "camera_id": camera_id,
                "timestamp": timestamp.isoformat() + "Z",
                "clip_id": record.id,
                "clip_url": f"/smart-bin/clips/{record.id}/stream",
                "level": "critical" if final_score > 70 else "high",
            })

            logger.info(
                "ClipCaptureService: captured clip id=%s camera=%s score=%.1f",
                record.id, camera_id, final_score,
            )
            return record

        finally:
            db.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_enabled(self, db) -> bool:
        row = db.query(SystemSetting).filter(SystemSetting.key == "smart_bin_enabled").first()
        if row is None:
            logger.warning("ClipCaptureService: 'smart_bin_enabled' setting missing; treating as disabled")
            return False
        return row.value.lower() == "true"

    def _get_clip_duration(self, db) -> int:
        row = db.query(SystemSetting).filter(SystemSetting.key == "clip_duration_seconds").first()
        if row is None:
            logger.warning("ClipCaptureService: 'clip_duration_seconds' setting missing; using default 10")
            return 10
        try:
            return int(row.value)
        except (ValueError, TypeError):
            logger.warning("ClipCaptureService: invalid 'clip_duration_seconds' value; using default 10")
            return 10

    def _get_retention_days(self, db) -> int:
        row = db.query(SystemSetting).filter(SystemSetting.key == "clip_retention_days").first()
        if row is None:
            logger.warning("ClipCaptureService: 'clip_retention_days' setting missing; using default 10")
            return 10
        try:
            return int(row.value)
        except (ValueError, TypeError):
            logger.warning("ClipCaptureService: invalid 'clip_retention_days' value; using default 10")
            return 10

    def _dedup_key(self, camera_id: str, alert_id: Optional[int]) -> str:
        return f"{camera_id}:{alert_id}"

    def _attach_clip_to_alert(self, alert_id: int, file_path: str, db) -> None:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.video_clip_path = file_path
            db.commit()


clip_capture_service = ClipCaptureService()
