from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String)
    risk_score = Column(Float)
    camera_id = Column(String)
    location = Column(String)
    risk_factors = Column(JSON)
    video_clip_path = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, acknowledged, resolved
