# API Routers — Functionality

This directory contains all FastAPI router modules that define the REST and WebSocket endpoints for the AURORA Sentinel backend.

## Routers

### `alerts.py`
- **Prefix**: `/alerts`
- **Endpoints**:
  - `GET /recent` — Retrieve active (non-resolved) alerts with optional status filtering
  - `POST /{id}/acknowledge` — Mark an alert as acknowledged by an operator
  - `POST /{id}/resolve` — Resolve an alert with a resolution type and notes
- **Purpose**: Full alert lifecycle management — from creation through acknowledgment to resolution with accountability tracking

### `analytics.py`
- **Prefix**: `/analytics`
- **Endpoints**:
  - `GET /dashboard` — Aggregate alert statistics (total, critical, high, medium, low counts)
- **Purpose**: Provides dashboard analytics data for the frontend analytics widgets

### `archive.py`
- **Prefix**: `/archive`
- **Endpoints**:
  - `GET /list` — List video clips from active storage, bin (deleted), or processed directories
  - `GET /clips/{filename}` — Serve a specific clip file for playback
  - `DELETE /clips/{filename}` — Move a clip from active storage to the bin
  - `POST /restore/{filename}` — Restore a clip from the bin back to active storage
  - `DELETE /bin/{filename}` — Permanently delete a clip from the bin
- **Purpose**: Video archive gallery management with soft-delete (bin) and restore capabilities

### `chatbot.py`
- **Prefix**: `/chatbot`
- **Endpoints**:
  - `POST /ask` — Natural language Q&A over surveillance data
- **Purpose**: AI-powered surveillance chatbot with forced routing (time ranges → search, counting → count), confidence-based VLM trigger, and Gemini-based answer generation

### `intelligence.py`
- **Prefix**: `/intelligence`
- **Endpoints**:
  - `POST /search` — Semantic search over video events using vector embeddings (ChromaDB)
  - `POST /chat` — Multi-turn chat with VLM visual Q&A and agent-based tool calling
  - `POST /upload` — Upload intelligence data for indexing
- **Purpose**: Intelligence hub — semantic search, conversational AI, and agent-driven analysis over indexed surveillance events

### `settings.py`
- **Prefix**: `/settings`
- **Endpoints**:
  - `GET /maintenance` / `POST /maintenance` — Toggle maintenance mode
  - `GET /vlm-interval` / `POST /vlm-interval` — Get/set VLM analysis interval (2–30s guardrails)
  - `GET /{key}` / `POST /{key}` — Generic CRUD for any SystemSetting key with validation
- **Purpose**: Runtime-configurable system settings with validation and persistence

### `smart_bin.py`
- **Prefix**: `/smart-bin`
- **Endpoints**:
  - `GET /clips` — List non-expired ClipRecords
  - `GET /clips/{id}` — Get a single ClipRecord
  - `GET /clips/{id}/stream` — Stream a clip file as video/mp4
- **Purpose**: Smart Bin clip management — browse and stream auto-captured threat clips with expiration tracking

### `stream.py`
- **Prefix**: `/ws`
- **Endpoints**:
  - `WebSocket /live-feed` — Real-time live video stream with ML detection overlay
- **Purpose**: WebSocket-based live surveillance feed with frame-by-frame ML analysis, skeleton drawing, and alert generation

### `stream_vlm.py`
- **Prefix**: `/vlm`
- **Endpoints**:
  - `WebSocket /intelligent-feed` — Enhanced live stream with two-tier scoring (ML + VLM)
- **Purpose**: Intelligent live stream combining ML detection with periodic VLM analysis, motion detection, scene-change triggers, and two-tier alert generation

### `video.py`
- **Prefix**: `/process` (no prefix, standalone routes)
- **Endpoints**:
  - `POST /upload` — Upload and process a video file with full two-tier scoring pipeline
  - `GET /results/{video_id}` — Retrieve processing results for an uploaded video
- **Purpose**: Offline video processing — upload, frame-by-frame ML + AI analysis, skeleton overlay rendering, and result persistence
