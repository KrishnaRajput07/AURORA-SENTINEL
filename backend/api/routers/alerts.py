from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import Alert
from backend.api.deps import get_db
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class ResolveRequest(BaseModel):
    resolution_type: str
    resolution_notes: Optional[str] = None
    operator_name: str = "Operator"

class AcknowledgeRequest(BaseModel):
    operator_name: str = "Operator"

@router.get("/recent")
async def get_recent_alerts(limit: int = 50, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get active alerts (pending/acknowledged)"""
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    else:
        # Default: Show non-resolved (Active)
        query = query.filter(Alert.status != "resolved")
        
    alerts = query.order_by(Alert.risk_score.desc(), Alert.timestamp.desc()).limit(limit).all()
    
    return {
        "count": len(alerts),
        "alerts": [alert_to_dict(a) for a in alerts]
    }

@router.get("/history")
async def get_alert_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get resolved history"""
    alerts = db.query(Alert).filter(Alert.status == "resolved")\
        .order_by(Alert.resolved_at.desc())\
        .limit(limit).all()
        
    return {
        "count": len(alerts),
        "alerts": [alert_to_dict(a) for a in alerts]
    }

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, req: AcknowledgeRequest, db: Session = Depends(get_db)):
    """Mark alert as acknowledged"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.operator_name = req.operator_name
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    return {"status": "success", "alert": alert_to_dict(alert)}

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, req: ResolveRequest, db: Session = Depends(get_db)):
    """Mark alert as resolved and archive"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolution_type = req.resolution_type
    alert.resolution_notes = req.resolution_notes
    alert.resolved_at = datetime.utcnow()
    
    # If not previously Ack'd, mark operator here too
    if not alert.operator_name:
        alert.operator_name = req.operator_name
    
    db.commit()
    return {"status": "success", "alert": alert_to_dict(alert)}

def alert_to_dict(alert: Alert):
    return {
        "id": alert.id,
        "timestamp": alert.timestamp.isoformat(),
        "level": alert.level,
        "risk_score": alert.risk_score,
        "camera_id": alert.camera_id,
        "location": alert.location,
        "status": alert.status,
        "risk_factors": alert.risk_factors,
        "operator_name": alert.operator_name,
        "resolution_type": alert.resolution_type,
        "resolution_notes": alert.resolution_notes,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
    }
