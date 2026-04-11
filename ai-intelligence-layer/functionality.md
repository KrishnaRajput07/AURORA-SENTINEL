# AI Intelligence Layer — Functionality

This directory implements the **Contextual Brain** of the dual-brain architecture — the AI tier that provides context-aware scene understanding and verification.

## Key Files

### `aiRouter_enhanced.py`
- **Enhanced AI Intelligence Router** — the core routing and orchestration module (960 lines)
- Supports multiple VLM providers: Qwen2-VL (GPU local), Ollama (cloud/local), HuggingFace (fallback)
- Reads provider configuration from `config.py` at runtime
- `analyze_image()`: Routes image analysis to the primary provider with automatic fallback
- `answer_question()`: Routes visual Q&A to the appropriate VLM
- `get_model_status()`: Returns availability status of all AI models for health checks
- Implements ML-score-gated prompting: skips AI if ML < 20, uses structured JSON prompt if ML > 70
- Timeout management per provider (Qwen: 2s, Nemotron: 3s, total: 5s)

### `model_availability.py`
- **Model Availability Tracker** — implements the circuit breaker pattern for AI models
- Tracks per-model status: consecutive failures, last failure/success time, availability
- Marks model unavailable after 3 consecutive failures
- 5-minute cooldown before retrying an unavailable model
- Provides status reporting for the `/health` endpoint
- Tracks: Qwen2-VL, Nemotron, Ollama

### `qwen2vl_integration.py`
- **Qwen2-VL-2B Integration** — local GPU VLM for systems with limited VRAM (4–6GB)
- GPU mode: float16 with `device_map="auto"`
- CPU mode: float32 fallback
- Configurable pixel resolution for video processing (min/max pixels)
- Handles image and video input with proper preprocessing

### `server_local.py`
- **Flask-based local AI router server** (port 3001)
- REST endpoints:
  - `GET /health` — Service health check with provider/model info
  - `POST /analyze` — Image analysis routing
  - `POST /chat` — Visual Q&A routing
- Can run as a standalone microservice separate from the main FastAPI backend

### `test_chat.py`
- Quick CLI test script for validating chat/Q&A functionality against the AI layer

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `cli_testing_scripts/` | CLI tools for testing intelligence upload |

## Architecture
- **Primary provider**: Configured via `PRIMARY_VLM_PROVIDER` (default: `ollama_cloud`)
- **Fallback chain**: Primary → Secondary → ML-only description
- **Circuit breaker**: Models are automatically disabled after repeated failures
- **Lazy loading**: Heavy models (Qwen2-VL, Nemotron) load on first use when `PRELOAD_LOCAL_MODELS=False`
