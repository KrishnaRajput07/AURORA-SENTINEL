from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# DATABASE_URL from environment variable (e.g., PostgreSQL for production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aurora.db")

# SQLite specific argument
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Test connection
    with engine.connect() as connection:
        pass
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print(f"Connected to Database Service: {DATABASE_URL}")
except Exception as e:
    print(f"Database connection error: {e}. Falling back to SQLite for safety.")
    DATABASE_URL = "sqlite:///./aurora.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
