import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.db.models import ClipRecord

logger = logging.getLogger(__name__)


class RetentionScheduler:
    """Background scheduler that periodically deletes expired ClipRecords."""

    async def start(self) -> None:
        """Called at FastAPI startup — launches _run_loop as an asyncio background task."""
        asyncio.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        """Loops forever: calls run_once, then sleeps 24 hours."""
        from backend.db.database import SessionLocal

        while True:
            db: Session = SessionLocal()
            try:
                deleted = await self.run_once(db)
                logger.info("RetentionScheduler: deleted %d expired clip(s).", deleted)
            except Exception:
                logger.exception("RetentionScheduler: unexpected error during run_once.")
            finally:
                db.close()

            await asyncio.sleep(86400)  # 24 hours

    async def run_once(self, db: Session) -> int:
        """
        Query ClipRecords where expires_at < utcnow(), attempt deletion of each.
        Returns the count of successfully deleted records.
        """
        now = datetime.utcnow()
        expired_records = (
            db.query(ClipRecord)
            .filter(ClipRecord.expires_at < now)
            .all()
        )

        deleted_count = 0
        for record in expired_records:
            try:
                await self._delete_clip(record, db)
                deleted_count += 1
            except Exception:
                # _delete_clip already logs; skip counting this record
                pass

        return deleted_count

    async def _delete_clip(self, record: ClipRecord, db: Session) -> None:
        """
        Delete the file at record.file_path and then remove the DB row.

        - FileNotFoundError  → log WARNING, still delete the DB row.
        - Other OSError      → log ERROR with record.id and file_path, do NOT delete the DB row.
        - Success            → delete file, then delete DB row.
        """
        try:
            os.remove(record.file_path)
        except FileNotFoundError:
            logger.warning(
                "RetentionScheduler: file not found for ClipRecord id=%s path=%s — "
                "deleting DB row anyway.",
                record.id,
                record.file_path,
            )
        except OSError as exc:
            logger.error(
                "RetentionScheduler: failed to delete file for ClipRecord id=%s "
                "path=%s — retaining DB row for retry. Error: %s",
                record.id,
                record.file_path,
                exc,
            )
            raise  # re-raise so run_once does not count this as deleted

        # Reaches here on success OR FileNotFoundError — delete the DB row in both cases
        db.delete(record)
        db.commit()
