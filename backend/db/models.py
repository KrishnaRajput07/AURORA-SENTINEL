from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # CRITICAL, HIGH, MEDIUM, LOW
    risk_score = Column(Float)  # Legacy field - kept for backward compatibility
    camera_id = Column(String)
    location = Column(String)
    risk_factors = Column(JSON)
    video_clip_path = Column(String, nullable=True)
    
    # ENHANCED FIGHT DETECTION: Two-Tier Scoring Fields
    ml_score = Column(Float, nullable=True)  # ML risk score (0-100)
    ai_score = Column(Float, nullable=True)  # AI risk score (0-100)
    final_score = Column(Float, nullable=True)  # MAX(ml_score, ai_score)
    detection_source = Column(String, nullable=True)  # "ml" | "ai" | "both" | "none"
    ai_explanation = Column(String, nullable=True)  # AI reasoning
    ai_scene_type = Column(String, nullable=True)  # "real_fight" | "boxing" | "drama" | "normal"
    ai_confidence = Column(Float, nullable=True)  # AI confidence (0-1)
    
    # Lifecycle Fields
    status = Column(String, default="pending")  # pending, acknowledged, resolved
    
    # Accountability Fields
    operator_name = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution Fields
    resolution_type = Column(String, nullable=True) # False Positive, Threat Neutralized, etc.
    resolution_notes = Column(String, nullable=True)
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(String)  # Stored as string, can be parsed as JSON if needed
