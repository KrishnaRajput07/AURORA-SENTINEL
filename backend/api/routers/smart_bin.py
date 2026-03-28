import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.db.models import ClipRecord

router = APIRouter()


class ClipRecordSchema(BaseModel):
    id: int
    camera_id: str
    alert_id: Optional[int]
    file_path: str
    duration_sec: int
    captured_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


@router.get("/clips", response_model=List[ClipRecordSchema])
def list_clips(db: Session = Depends(get_db)):
    """Return all non-expired ClipRecord rows ordered by captured_at desc."""
    now = datetime.utcnow()
    clips = (
        db.query(ClipRecord)
        .filter(ClipRecord.expires_at >= now)
        .order_by(ClipRecord.captured_at.desc())
        .all()
    )
    return clips


@router.get("/clips/{id}", response_model=ClipRecordSchema)
def get_clip(id: int, db: Session = Depends(get_db)):
    """Return a single ClipRecord or HTTP 404 if not found."""
    clip = db.query(ClipRecord).filter(ClipRecord.id == id).first()
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.get("/clips/{id}/stream")
def stream_clip(id: int, db: Session = Depends(get_db)):
    """Stream the clip file as video/mp4, or HTTP 404 if record or file is missing."""
    clip = db.query(ClipRecord).filter(ClipRecord.id == id).first()
    if clip is None:
        raise HTTPException(status_code=404, detail="Clip not found")
    if not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")
    return FileResponse(clip.file_path, media_type="video/mp4")
