from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:hackathon2024@postgres:5432/aurora")

try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    with engine.connect() as connection:
        pass
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print(f"Connected to Database: {DATABASE_URL}")
except Exception as e:
    print(f"Database connection error: {e}. Falling back to SQLite for dev.")
    DATABASE_URL = "sqlite:///./aurora.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
