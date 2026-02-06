from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.models import Alert
from backend.api.deps import get_db

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Get dashboard analytics data"""
    try:
        # Get alert statistics
        total_alerts = db.query(Alert).count()
        critical_alerts = db.query(Alert)\
            .filter(Alert.level == "CRITICAL")\
            .count()
        
        return {
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "alert_levels": {
                "critical": critical_alerts,
                "high": db.query(Alert).filter(Alert.level == "HIGH").count(),
                "medium": db.query(Alert).filter(Alert.level == "MEDIUM").count(),
                "low": db.query(Alert).filter(Alert.level == "LOW").count()
            }
        }
    except Exception as e:
        return {"error": str(e)}
