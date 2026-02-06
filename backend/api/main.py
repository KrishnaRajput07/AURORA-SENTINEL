from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine, Base
from backend.api.routers import alerts, analytics, video, stream
from backend.services.ml_service import ml_service
import os

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="AURORA-SENTINEL API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Models on Startup
@app.on_event("startup")
async def startup_event():
    ml_service.load_models()

# Include Routers
from backend.api.routers import alerts, analytics, video, stream

# ... imports ...

# Include Routers
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(stream.router, prefix="/ws", tags=["Live Stream"]) # Mounts at /ws/live-feed
app.include_router(video.router, tags=["Video Processing"]) # Mounts at /process/video (explicit in router)


@app.get("/")
async def root():
    return {
        "message": "AURORA-SENTINEL API",
        "version": "2.0.0",
        "status": "operational",
        "models_loaded": ml_service.loaded
    }

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "models_loaded": ml_service.loaded,
        "gpu_available": getattr(ml_service.detector, 'device', 'cpu') == 'cuda' if ml_service.detector else False,
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
