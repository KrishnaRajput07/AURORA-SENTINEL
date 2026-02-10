from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./aurora.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    from backend.db.models import Alert
    alerts = db.query(Alert).filter(Alert.camera_id == 'FORENSIC-01').all()
    print(f"Forensic Alerts Found: {len(alerts)}")
    for a in alerts:
        print(f"ID: {a.id}, Status: {a.status}, VideoPath: {a.video_clip_path}")
except Exception as e:
    print(f"Error: {e}")

bin_path = os.path.abspath("storage/bin")
if os.path.exists(bin_path):
    files = os.listdir(bin_path)
    print(f"Files in Smart Bin ({bin_path}): {files}")
else:
    print(f"Smart Bin path does NOT exist: {bin_path}")

db.close()
