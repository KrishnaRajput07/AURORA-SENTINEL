# Backend — Functionality

The backend is a Python FastAPI application that serves as the core intelligence and API layer for AURORA Sentinel.

## Architecture
- **Framework**: FastAPI + Uvicorn (port 8000)
- **Database**: SQLAlchemy ORM with SQLite (default) or PostgreSQL
- **ML Pipeline**: YOLOv8 detection → Risk scoring → VLM verification → Alert generation
- **Real-time**: WebSocket endpoints for live video streaming with ML overlay
- **AI Layer**: Multi-provider VLM orchestration (Ollama, Gemini, Nemotron)

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `api/` | FastAPI app setup, routers, dependency injection |
| `db/` | Database engine, ORM models, migrations |
| `services/` | Core business logic (16 service modules) |
| `tests/` | Backend-specific test suites (unit + PBT) |
| `utils/` | Shared utility functions (currently empty) |
| `video/` | Video processing (summarization, thumbnails) |

## Key Capabilities
1. **Two-tier scoring**: ML detection (30% weight) + AI verification (70% weight) → final alert score
2. **Live surveillance**: WebSocket-based real-time ML analysis with optional VLM intelligence
3. **Offline processing**: Frame-by-frame video analysis with full pipeline
4. **Semantic search**: Vector DB (ChromaDB) powered event search with embeddings
5. **Agent chatbot**: Tool-calling agent for natural language surveillance queries
6. **Alert lifecycle**: Create → acknowledge → resolve with full accountability
7. **Smart clip capture**: Auto-record threat clips with retention management
8. **Runtime configuration**: Hot-swappable settings via SystemSetting key-value store
