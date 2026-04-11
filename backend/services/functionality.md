# Services — Functionality

This directory contains the core business logic services that power the AURORA Sentinel backend.

## Services

### `agent_service.py`
- Lightweight tool-calling agent built on Ollama
- Decomposes user questions into structured tool calls: `search_events`, `count_events`, `visual_qa`
- Reads agent config (model, max_calls, temperature) at call-time for hot-swappability
- Integrates with `search_service` for DB queries and `vlm_service` for visual analysis

### `alert_service.py`
- Generates operator alerts with two-tier score metadata
- Maps final scores to severity levels (CRITICAL/HIGH/MEDIUM/LOW) using configurable thresholds
- Applies sport/boxing risk cap (default 15%) to prevent false positives from sporting events
- Produces alert dicts ready for database insertion

### `audio_service.py`
- Audio event detection using HuggingFace AST model (`MIT/ast-finetuned-audioset-10-10-0.4593`)
- Lazy-loads model into RAM only when needed
- Monitors for critical sounds: gunshots, explosions, screaming, glass breaking, shouting, aggression
- Optional dependency — backend runs fine without audio support

### `chat_session_store.py`
- In-memory chat session store with TTL-based eviction
- Thread-safe with bounded history length (max 12 turns default)
- Sessions auto-expire after 30 minutes of inactivity
- Singleton `chat_session_store` instance used by intelligence and chatbot routers

### `clip_capture_service.py`
- Captures video clips automatically on threat escalation
- Deduplicates captures per (camera_id, alert_id) pair
- Integrates with `video_storage_service` for recording and `ws_manager` for real-time notifications
- Respects Smart Bin enable/disable setting from `SystemSetting`

### `enhanced_vlm_prompts.py`
- Builds context-rich forensic VLM analysis prompts
- Injects ML detection context: weapon details with position, person counts with spatial info, vehicle/object detection
- Adds temporal context (timestamp) and previous frame narrative for continuity
- Generates structured JSON prompts for high ML scores, simple prompts for low scores

### `ml_service.py`
- Singleton service that manages ML model lifecycle
- Loads `UnifiedDetector` (YOLOv8), `RiskScoringEngine`, and `PrivacyAnonymizer` on startup
- Supports both synchronous and asynchronous model loading
- GPU-first with automatic CPU fallback on CUDA OOM/driver errors
- Provides `wait_until_ready()` for blocking until models are loaded

### `offline_processor.py`
- Processes uploaded video files frame-by-frame
- Runs ML detection → two-tier scoring → alert generation pipeline
- Keyword-based fallback threat classification when VLM is unavailable
- Negation-aware keyword matching (e.g., "no fight detected")
- Extracts thumbnails at alert timestamps
- Indexes events into vector database for semantic search
- Generates video summaries with alert segments and H.264 transcoding

### `retention_scheduler.py`
- Background asyncio scheduler that deletes expired `ClipRecord` entries
- Runs on a 24-hour cycle, started at FastAPI startup
- Deletes both the database record and the physical file on disk

### `scoring_service.py`
- **Two-tier scoring service** — the core decision engine
- Combines ML risk engine score with AI intelligence verification
- Weighted formula: `final_score = max(ml_score, 0.3*ML + 0.7*AI)`
- ML-gating: skips AI analysis if ML score < 20 (no threat)
- Applies sport risk cap and confidence adjustments
- Determines `should_alert` based on threshold (default 60%)

### `search_service.py`
- Semantic search over video events using ChromaDB vector database
- Embeds queries with `sentence-transformers` (`all-MiniLM-L6-v2`)
- Falls back to keyword search when vector DB is unavailable
- Supports time-range filtering, filename filtering, and result ranking by score/timestamp
- Indexes events with rich metadata (risk scores, explanations, scene types, keywords)

### `system_settings_service.py`
- CRUD helper for the `SystemSetting` key-value store
- Provides typed getters/setters for `vlm_interval_seconds` with validation
- Used by the settings router for runtime configuration

### `video_storage_service.py`
- Manages video recording, clip storage, and lifecycle
- Handles live stream recording with `cv2.VideoWriter`
- Auto-transcodes clips to H.264 for browser compatibility
- Manages active clips (`storage/clips`) and bin (`storage/bin`) directories
- Periodic cleanup thread for expired clips based on retention policy
- Supports clip retrieval by camera ID and time range

### `vlm_service.py`
- VLM (Vision-Language Model) orchestrator with fallback chain
- **Primary**: Ollama (Qwen3-VL) → **Backup**: Gemini API → **Fallback**: ML-only description
- Optional Nemotron verification (lazy-load capable)
- Applies sport risk cap to AI scores
- Parses structured JSON from VLM responses with robust error handling

### `vlm_providers.py`
- Abstract `VLMProvider` base class with `analyze()` interface
- **`GeminiProvider`**: Google Gemini API integration (requires `GEMINI_API_KEY`)
- **`OllamaProvider`**: Local/cloud Ollama integration with configurable model
- **`NemotronProvider`**: NVIDIA Nemotron model for verification (lazy-loaded, GPU optional)
- Each provider handles its own initialization, availability checks, and error handling

### `ws_manager.py`
- WebSocket connection manager for broadcasting real-time data
- Maintains list of active connections
- Supports personal messages and JSON broadcast to all connected clients
- Handles dead connections gracefully
