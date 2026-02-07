from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # CRITICAL, HIGH, MEDIUM, LOW
    risk_score = Column(Float)
    camera_id = Column(String)
    location = Column(String)
    risk_factors = Column(JSON)
    video_clip_path = Column(String, nullable=True)
    
    # Lifecycle Fields
    status = Column(String, default="pending")  # pending, acknowledged, resolved
    
    # Accountability Fields
    operator_name = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution Fields
    resolution_type = Column(String, nullable=True) # False Positive, Threat Neutralized, etc.
    resolution_notes = Column(String, nullable=True)
