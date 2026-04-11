# API — Functionality

This directory contains the FastAPI application setup and all HTTP/WebSocket route definitions.

## Key Files

### `main.py`
- Initializes the FastAPI app (`AURORA-SENTINEL API v2.0.0`)
- Configures CORS middleware (open origins for development)
- Creates database tables on startup via SQLAlchemy
- Loads ML models synchronously on startup (`ml_service.load_models()`)
- Starts the `RetentionScheduler` background task
- Mounts static file serving for recordings and frontend build
- Includes all 10 routers (alerts, analytics, stream, stream_vlm, video, archive, intelligence, settings, smart_bin, chatbot)
- Provides `GET /` (root status) and `GET /health` (detailed health check with AI model status, GPU, optional features)
- Global exception handler with CORS fallback

### `deps.py`
- Dependency injection helper — provides `get_db()` generator for SQLAlchemy session management in route handlers

### `routers/`
- Contains all individual router modules (see `routers/functionality.md`)

## Architecture
- **Framework**: FastAPI with Uvicorn
- **Port**: 8000
- **Database sessions**: Injected via `Depends(get_db)`
- **WebSocket**: Two separate WS endpoints for basic and intelligent live feeds
- **Static serving**: Frontend build served from `frontend/build/` at root path
