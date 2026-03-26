from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import SystemSetting
from backend.api.deps import get_db
from pydantic import BaseModel

router = APIRouter()

class SettingUpdate(BaseModel):
    value: str

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
