from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine, Base
from backend.api.routers import alerts, analytics, video, stream, archive
from backend.services.ml_service import ml_service
import os

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="AURORA-SENTINEL API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Broaden for reliable communications during hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL EXCEPTION: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"} # Manual CORS fallback
    )

# Initialize Models on Startup
@app.on_event("startup")
async def startup_event():
    ml_service.load_models()

# Routers are included below using 'app.include_router'

# ... imports ...

# Include Routers
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(stream.router, prefix="/ws", tags=["Live Stream"])
app.include_router(video.router, tags=["Video Processing"])
app.include_router(archive.router, prefix="/archive", tags=["Archive"])

# Serve Static Files (Frontend)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if build directory exists
if os.path.exists("frontend/build"):
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Prevent intercepting API routes
        if full_path.startswith(("alerts", "analytics", "ws", "process", "archive", "health")):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse("frontend/build/index.html")
else:
    print("WARNING: frontend/build directory not found. Frontend will not be served by backend.")


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
