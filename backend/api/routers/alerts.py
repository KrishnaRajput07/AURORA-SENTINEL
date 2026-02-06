from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import Alert
from backend.api.deps import get_db

router = APIRouter()

@router.get("/recent")
async def get_recent_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent alerts from database"""
    alerts = db.query(Alert)\
        .order_by(Alert.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": alert.id,
                "timestamp": alert.timestamp.isoformat(),
                "level": alert.level,
                "risk_score": alert.risk_score,
                "camera_id": alert.camera_id,
                "status": alert.status,
                "risk_factors": alert.risk_factors
            }
            for alert in alerts
        ]
    }

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark alert as acknowledged"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    db.commit()
    return {"status": "success", "alert_id": alert_id}
