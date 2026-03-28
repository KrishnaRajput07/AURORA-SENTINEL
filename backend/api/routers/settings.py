from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import SystemSetting
from backend.api.deps import get_db
from pydantic import BaseModel

from backend.services.system_settings_service import (
    VLM_INTERVAL_KEY,
    get_vlm_interval_seconds,
    set_vlm_interval_seconds,
)

router = APIRouter()

class SettingUpdate(BaseModel):
    value: str


class VlmIntervalUpdate(BaseModel):
    seconds: int

# Validation rules for Smart Bin settings keys
_SETTING_VALIDATORS = {
    "clip_duration_seconds": (5, 300),
    "clip_retention_days": (1, 365),
}

def _validate_setting(key: str, value: str) -> None:
    """Raise HTTP 422 if the value is out of range for a validated key."""
    if key not in _SETTING_VALIDATORS:
        return
    lo, hi = _SETTING_VALIDATORS[key]
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail=f"Value for '{key}' must be an integer.",
        )
    if not (lo <= int_val <= hi):
        raise HTTPException(
            status_code=422,
            detail=f"Value for '{key}' must be between {lo} and {hi} (inclusive). Got {int_val}.",
        )

@router.get("/maintenance")
async def get_maintenance_mode(db: Session = Depends(get_db)):
    """Get the current maintenance mode status"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == "maintenance_mode").first()
    if not setting:
        return {"maintenance_mode": False}
    return {"maintenance_mode": setting.value.lower() == "true"}

@router.post("/maintenance")
async def set_maintenance_mode(req: SettingUpdate, db: Session = Depends(get_db)):
    """Set the maintenance mode status"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == "maintenance_mode").first()
    if not setting:
        setting = SystemSetting(key="maintenance_mode", value=req.value)
        db.add(setting)
    else:
        setting.value = req.value
    
    db.commit()
    return {"status": "success", "maintenance_mode": setting.value.lower() == "true"}


# --- VLM-specific endpoints (from main) ---

@router.get("/vlm-interval")
async def get_vlm_interval():
    """Get persisted global VLM analysis interval in seconds."""
    interval = get_vlm_interval_seconds(default_value=10)
    return {"key": VLM_INTERVAL_KEY, "seconds": int(interval)}


@router.post("/vlm-interval")
async def set_vlm_interval(req: VlmIntervalUpdate):
    """
    Set persisted global VLM interval.
    Guardrails: 2-30 seconds.
    """
    seconds = int(req.seconds)
    if seconds < 2 or seconds > 30:
        raise HTTPException(status_code=400, detail="seconds must be between 2 and 30")

    saved = set_vlm_interval_seconds(seconds)
    return {"status": "success", "key": VLM_INTERVAL_KEY, "seconds": int(saved)}


# --- Generic settings CRUD (from feature) ---
# NOTE: These must come AFTER specific routes like /maintenance and /vlm-interval
# to avoid the path parameter {key} shadowing them.

@router.get("/{key}")
async def get_setting(key: str, db: Session = Depends(get_db)):
    """Return the current value for a SystemSetting key."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    return {"key": setting.key, "value": setting.value}


@router.post("/{key}")
async def set_setting(key: str, req: SettingUpdate, db: Session = Depends(get_db)):
    """Create or update a SystemSetting key after validating the value."""
    _validate_setting(key, req.value)
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=req.value)
        db.add(setting)
    else:
        setting.value = req.value
    db.commit()
    return {"key": setting.key, "value": setting.value}
