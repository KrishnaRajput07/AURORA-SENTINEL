from backend.db.database import SessionLocal
from backend.db.models import Alert
import json

db = SessionLocal()
alerts = db.query(Alert).all()
print(f"Total Alerts: {len(alerts)}")
for a in alerts:
    print(f"ID: {a.id}, Camera: {a.camera_id}, Level: {a.level}, Status: {a.status}, Video: {a.video_clip_path}")
db.close()
