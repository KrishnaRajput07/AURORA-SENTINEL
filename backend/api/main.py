from dotenv import load_dotenv
load_dotenv() # MUST BE FIRST

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine, Base, ensure_alert_columns
from backend.api.routers import alerts, analytics, video, stream, archive, stream_vlm, intelligence, settings
from backend.services.ml_service import ml_service
import os
import shutil

# Create tables
Base.metadata.create_all(bind=engine)
ensure_alert_columns()

# Initialize FastAPI
app = FastAPI(title="AURORA-SENTINEL API", version="2.0.0")

from fastapi.staticfiles import StaticFiles

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Broaden for reliable communications during hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve recorded videos
os.makedirs("storage/recordings", exist_ok=True)
app.mount("/recordings", StaticFiles(directory="storage/recordings"), name="recordings")

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
    print("STARTUP: Starting ml_service.load_models()...")
    try:
        ml_service.load_models()
        print("STARTUP: ml_service.load_models() completed.")
    except Exception as e:
        print(f"STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e

# Routers are included below using 'app.include_router'



# Include Routers
print("Including alerts router...")
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
print("Including analytics router...")
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
print("Including stream router...")
app.include_router(stream.router, prefix="/ws", tags=["Live Stream"]) 
print("Including stream_vlm router...")
app.include_router(stream_vlm.router, prefix="/vlm", tags=["Intelligent Stream"]) 
print("Including video router...")
app.include_router(video.router, tags=["Video Processing"]) 
print("Including archive router...")
app.include_router(archive.router, prefix="/archive", tags=["Archive"])
print("Including intelligence router...")
app.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence"]) 
print("Including settings router...")
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
print("All routers included.")

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
    # Optional dependency status (report, don't fail health)
    try:
        import chromadb  # noqa: F401
        chroma_ok = True
    except Exception:
        chroma_ok = False

    try:
        import sentence_transformers  # noqa: F401
        st_ok = True
    except Exception:
        st_ok = False

    try:
        import google.generativeai  # noqa: F401
        gemini_pkg_ok = True
    except Exception:
        gemini_pkg_ok = False

    try:
        import ollama  # noqa: F401
        ollama_pkg_ok = True
    except Exception:
        ollama_pkg_ok = False

    ffmpeg_ok = bool(shutil.which("ffmpeg"))
    
    # Get AI model availability status
    ai_model_status = {}
    try:
        # Import and get status from AI router
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ai_layer_path = os.path.join(project_root, 'ai-intelligence-layer')
        if ai_layer_path not in sys.path:
            sys.path.insert(0, ai_layer_path)
        
        from aiRouter_enhanced import get_model_status
        ai_model_status = get_model_status()
    except Exception as e:
        print(f"Could not get AI model status: {e}")
        ai_model_status = {
            'error': 'AI model status unavailable',
            'details': str(e)
        }

    return {
        "status": "healthy",
        "models_loaded": ml_service.loaded,
        "model_load_error": ml_service.load_error,
        "model_device": ml_service.device_in_use,
        "gpu_available": getattr(ml_service.detector, 'device', 'cpu') == 'cuda' if ml_service.detector else False,
        "database": "connected",
        "ai_models": ai_model_status,
        "optional_features": {
            "gemini_pkg": gemini_pkg_ok,
            "ollama_pkg": ollama_pkg_ok,
            "chromadb": chroma_ok,
            "sentence_transformers": st_ok,
            "ffmpeg": ffmpeg_ok
        }
    }

# Serve Static Files (Frontend)
from fastapi.responses import FileResponse

# Register API routes first so they are not shadowed by static mount.
if os.path.exists("frontend/build"):
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Prevent intercepting API routes
        if full_path.split('/')[0] in ["alerts", "analytics", "ws", "vlm", "process", "archive", "intelligence", "health", "docs", "openapi.json"]:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse("frontend/build/index.html")
else:
    print("WARNING: frontend/build directory not found. Frontend will not be served by backend.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
