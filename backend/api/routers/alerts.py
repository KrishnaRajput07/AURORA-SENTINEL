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
        
    alerts = query.order_by(Alert.timestamp.desc(), Alert.risk_score.desc()).limit(limit).all()
    
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
    try:
        # Robust date handling
        ts_iso = alert.timestamp.isoformat() if alert.timestamp else datetime.utcnow().isoformat()
        ack_iso = alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        res_iso = alert.resolved_at.isoformat() if alert.resolved_at else None

        data = {
            "id": alert.id,
            "timestamp": ts_iso,
            "level": alert.level or "INFO",
            "risk_score": alert.risk_score or 0.0,
            "camera_id": alert.camera_id or "UNKNOWN",
            "location": alert.location or "Unknown Location",
            "status": alert.status or "pending",
            "operator_name": alert.operator_name,
            "resolution_type": alert.resolution_type,
            "resolution_notes": alert.resolution_notes,
            "acknowledged_at": ack_iso,
            "resolved_at": res_iso,
            "video_clip_path": alert.video_clip_path
        }
        
        # Flatten risk_factors for frontend compatibility
        if alert.risk_factors:
            try:
                if isinstance(alert.risk_factors, dict):
                    data.update(alert.risk_factors)
                elif isinstance(alert.risk_factors, str):
                    import json
                    extra = json.loads(alert.risk_factors)
                    if isinstance(extra, dict):
                        data.update(extra)
            except Exception as e:
                print(f"Warning: Failed to parse risk_factors for alert {alert.id}: {e}")
                
        return data
    except Exception as e:
        print(f"Error serializing alert {alert.id}: {e}")
        # Return a absolute bare-bones dict to avoid failing the whole list
        return {"id": alert.id, "error": str(e), "status": "error"}
