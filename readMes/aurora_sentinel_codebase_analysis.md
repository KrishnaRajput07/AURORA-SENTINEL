# AURORA-SENTINEL — AI/ML System Briefing (v2 — Updated)

> **For:** Incoming AI/ML Engineer  
> **Date:** March 2026  
> **Scope:** Comprehensive deep-dive into every AI/ML subsystem, storage architecture, agentic intelligence, and VLM orchestration

---

## 1. Architecture Overview

The system operates as a **centralized Python FastAPI monolith** backed by a React/Next.js frontend. A legacy Node.js AI Intelligence Layer still exists on disk (`ai-intelligence-layer/`) but the main backend **no longer routes through it at runtime** — all VLM inference is handled natively within the FastAPI process via `vlm_service.py` and `vlm_providers.py`.

```text
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (React/Next.js)                                       │
└─────────────────┬───────────────────────────────────────────────┘
                  │ REST + WebSocket
┌─────────────────▼───────────────────────────────────────────────┐
│  Backend (FastAPI)                                               │
│                                                                  │
│  ROUTERS                                                         │
│  ├─ stream.py          ML-only live camera feed (WebSocket)      │
│  ├─ stream_vlm.py      ML+VLM live camera feed (WebSocket)      │
│  ├─ intelligence.py    Chat, search, upload, cross-search (REST) │
│  ├─ video.py           Video CRUD management                    │
│  └─ alerts.py          Alert lifecycle CRUD                     │
│                                                                  │
│  SERVICES                                                        │
│  ├─ ml_service.py           YOLOv8 singleton (detector + risk)   │
│  ├─ vlm_service.py          VLM orchestrator (Ollama → Gemini)   │
│  ├─ vlm_providers.py        Provider implementations             │
│  ├─ scoring_service.py      Two-tier weighted scorer             │
│  ├─ agent_service.py        ReAct tool-calling agent             │
│  ├─ chat_session_store.py   Multi-turn conversation memory       │
│  ├─ search_service.py       ChromaDB vector search + RAG         │
│  ├─ offline_processor.py    Uploaded video analysis pipeline     │
│  ├─ video_storage_service.py Smart retention + bin lifecycle     │
│  ├─ alert_service.py        Alert generation from scores         │
│  ├─ audio_service.py        Threat-sound detection (audio)       │
│  └─ system_settings_service.py  Runtime config (VLM interval)   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Config File: `config.py`

| Setting | Default | Notes |
|---|---|---|
| `PRIMARY_VLM_PROVIDER` | `ollama_cloud` | Primary VLM provider selection |
| `OLLAMA_CLOUD_MODEL` | `qwen3-vl:235b-cloud` | The big cloud-hosted Qwen3 VL model |
| `PRELOAD_LOCAL_MODELS` | `False` | Set `True` on GPU-equipped machines |
| `ENABLE_AGENT_CHAT` | `False` (env) | Feature flag for the ReAct agent chat |
| `AGENT_MODEL` | `qwen3:4B` | Local Ollama model for the tool-calling agent |
| `EMBEDDING_MODEL_ID` | `all-MiniLM-L6-v2` | Sentence-transformer for RAG |
| `NEMOTRON_MODEL_ID` | `nvidia/nemotron-colembed-vl-4b-v2` | Verification embedding model |
| `ML_SCORE_WEIGHT` / `AI_SCORE_WEIGHT` | `0.3` / `0.7` | Two-tier formula weights |
| `ALERT_THRESHOLD` | `60.0` | Uploaded video alert trigger |
| `LIVE_ALERT_THRESHOLD` | `65` | Live stream alert trigger |
| `RECORDING_THRESHOLD` | `50` | Auto-record above this score |
| `SPORT_RISK_CAP` | `15` | Max risk if boxing/sport detected |

---

## 2. The ML Layer (YOLOv8)

**File:** `backend/services/ml_service.py`

`MLService` is a thread-safe singleton that loads three sub-models in a **background thread** so API startup is never blocked:

| Sub-model | Source | Role |
|---|---|---|
| `UnifiedDetector` | `models/detection/detector.py` | YOLOv8 object/pose/weapon detection |
| `RiskScoringEngine` | `models/scoring/risk_engine.py` | Detections → ML risk score (0-100) |
| `PrivacyAnonymizer` | `models/privacy/anonymizer.py` | Face blurring for GDPR/privacy |

**What `UnifiedDetector.process_frame()` returns:**
```python
{
  'poses':   [...],   # YOLO-pose keypoints per person
  'objects': [...],   # Bounding boxes + class + track_id
  'weapons': [...],   # Dedicated weapon sub-model hits
  'patterns': [...]   # High-level behavioural patterns
}
```

**Thresholds (live stream):**
- Risk > `LIVE_ALERT_THRESHOLD` (65) → alert generated
- Risk > `RECORDING_THRESHOLD` (50) → auto-starts clip recording
- Adaptive frame skipping kicks in if processing exceeds 50ms

---

## 3. The Two-Tier Scoring Service

**File:** `backend/services/scoring_service.py`

This is the **canonical scoring formula** used across both uploaded video processing and the live VLM feed:

```
Final_Score = 0.3 × ML_Score + 0.7 × AI_Score   (if both available)
Final_Score = ML_Score                             (if AI unavailable, confidence=0.3)
Final_Score = AI_Score                             (if ML unavailable, confidence=0.6)
Final_Score = 0.0                                  (if neither available)
```

**Key behaviors:**
- **ML gating:** If `ML_Score < 20`, AI analysis is skipped entirely to conserve resources
- **`aggregate_existing_scores()` method:** Used by `stream_vlm.py` to re-aggregate scores in the live loop without re-running AI inference. This is critical — it means the two-tier formula is now **wired into the live feed**, not just uploaded video processing
- **Alert threshold:** `final_score > 60` (uploaded) or `> 65` (live)
- **Audit logging:** Every score computation is logged with `[AUDIT]` tags for forensic review, including Nemotron verification details when available

---

## 4. The VLM Layer — Simplified Orchestrator

### 4a. Provider Definitions

**File:** `backend/services/vlm_providers.py`

Three clean provider implementations:

| Provider | Class | Model | Type |
|---|---|---|---|
| **Ollama** | `OllamaProvider` | `qwen3-vl:235b-cloud` | Generative VLM |
| **Gemini** | `GeminiProvider` | Rotates: `gemini-1.5-flash-latest`, `gemini-1.5-pro`, etc. | Cloud VLM |
| **Nemotron** | `NemotronProvider` | `nvidia/nemotron-colembed-vl-4b-v2` | Embedding verifier |

**GeminiProvider** has built-in model rotation: on 429/quota errors or 404/503, it automatically rotates through 5 model variants (`gemini-1.5-flash-latest` → `gemini-1.5-flash` → `gemini-1.5-flash-002` → `gemini-1.5-pro-latest` → `gemini-1.5-pro`).

**NemotronProvider** gates behind `ENABLE_HEAVY_MODELS=true` env var. It uses PyTorch `AutoModel` with automatic `float16`/CUDA when available.

### 4b. VLM Service Orchestration

**File:** `backend/services/vlm_service.py`

The VLM orchestrator is now a **Simplified Single-Model + Fallback** architecture (down from the previous 6-provider waterfall):

```
Primary: OllamaProvider (Qwen3-VL)
   ↓ fails
Backup:  GeminiProvider (if configured)
   ↓ fails
Fallback: ML-only mode (no VLM description, pass-through risk score)
```

**Key methods:**

| Method | Purpose |
|---|---|
| `analyze_scene(frame_pil, prompt, risk_score)` | Single-frame VLM analysis with Nemotron verification |
| `answer_question(image_data, question)` | Multi-modal Q&A for visual queries |
| `answer_with_context(question, context_blocks, history)` | Text-only context Q&A for timeline chat |
| `summarize_events(filename, events)` | Generates video-level executive summaries |

**`analyze_scene()` flow:**
1. Build a context-aware prompt based on `risk_score` magnitude
2. Call Ollama → if fails, Gemini → if fails, return ML-only
3. Extract risk from VLM text via keyword matching (`_extract_risk_from_text()`)
4. Apply Nemotron verification if enabled (lazy-loaded on first use)
5. Apply sport/boxing safety cap: if boxing/sparring/referee keywords present AND no street-fight/assault keywords, risk capped at `SPORT_RISK_CAP` (15)

**Nemotron Verification Pipeline:**
1. Encode frame → image embedding
2. Encode VLM text summary → text embedding
3. Cosine similarity > 0.6 → "verified"
4. Compare against 4 threat category embeddings: `real_fight`, `organized_sport`, `normal`, `suspicious`
5. Highest-scoring category determines `nemotron_scene_type`
6. If verified + agreement → average scores (confidence=0.9)
7. If not verified or disagreement → take max score (confidence=0.5)
8. Timeout: configurable via `NEMOTRON_TIMEOUT` (default 3s), falls back to raw VLM score

---

## 5. The Agentic Intelligence System (NEW)

### 5a. ReAct Tool-Calling Agent

**File:** `backend/services/agent_service.py`

The previous chatbot was a simple stateless waterfall. It has been replaced with a full **ReAct-style tool-calling agent** powered by a local Ollama model (`AGENT_MODEL`, default `qwen3:4B`).

**Tool Registry:**

| Tool | Description | Search Backend |
|---|---|---|
| `timeline_search` | Find events within a video timeline, supports `start_ts`/`end_ts` ranges | `search_service.timeline_search()` / `range_search()` |
| `count_events` | Count matching events across all videos, filter by severity | `search_service.count_matching()` |
| `visual_qa` | Extract a frame at a specific timestamp and run VLM Q&A | `vlm_service.answer_question()` |
| `cross_video_search` | Find matching events across multiple videos | `search_service.cross_video_search()` |
| `get_video_info` | Get metadata, duration, and summary for a video | `search_service.get_video_record()` |

**Execution loop:**
1. System prompt instructs the agent as a surveillance analyst
2. Injects last 6 turns of conversation history
3. Calls `ollama.chat()` with `tools=` parameter for native tool calling
4. Iterates up to `AGENT_MAX_TOOL_CALLS` (default 3) rounds
5. Executes tool calls, feeds results back as `role: tool` messages
6. When no more tool calls are needed, returns the final text answer
7. Strips `<think>` tags from reasoning models (Qwen3 thinking mode)

**Config (all hot-swappable at call-time):**
- `AGENT_MODEL`: `qwen3:4B` (local)
- `AGENT_TEMPERATURE`: `0.1` (deterministic)
- `AGENT_MAX_TOOL_CALLS`: `3`
- `ENABLE_AGENT_CHAT`: `false` (feature-flagged, enable via env var)

### 5b. Multi-Turn Conversation Memory

**File:** `backend/services/chat_session_store.py`

Thread-safe in-memory session store replacing the previous stateless `/chat` endpoint:

| Parameter | Default | Purpose |
|---|---|---|
| `ttl_seconds` | `1800` (30 min) | Session expiry timeout |
| `max_turns` | `12` | Rolling history window |

**Mechanics:**
- `get_or_create_session_id()`: Creates or retrieves a session (UUID-based)
- `append_turn()`: Adds user/assistant messages with timestamps
- `_cleanup_expired_locked()`: Automated LRU-style eviction of stale sessions
- All operations are thread-safe via `threading.Lock`

### 5c. Intelligence Chat Router (Dual-Path)

**File:** `backend/api/routers/intelligence.py` → `POST /intelligence/chat`

The chat endpoint supports **two execution paths**, switchable via `ENABLE_AGENT_CHAT`:

**Path A — Deterministic (default):**
```
1. Parse question → extract timestamp hints (regex: "2 minutes", "1:30", "beginning", etc.)
2. Parse time ranges ("from 80s to 120s", "between 80 and 120 seconds")
3. timeline_search() → find relevant events in ChromaDB/metadata
4. If time range detected → use range_search() for bounded window
5. vlm_service.answer_with_context() → LLM synthesizes answer from event descriptions
6. If visual query detected ("what color", "who is", etc.) → extract frame at timestamp → visual_qa
7. Return answer + timeline payload + used_sources
```

**Path B — Agent (feature-flagged):**
```
1. agent_service.run(question, filename, history)
2. Agent autonomously decides which tools to call
3. Can combine timeline_search + visual_qa + cross_video_search in a single query
4. Returns structured answer with tools_called audit trail
```

**Smart frame extraction:** The system now extracts frames at **relevant timestamps** instead of always using `total_frames // 2`. It parses timestamps from questions via regex, queries ChromaDB for relevant events, and extracts the frame at the best-matching timestamp.

---

## 6. Live Video Pipelines

### 6a. `/stream/live-feed` (ML-only)

**File:** `backend/api/routers/stream.py`

- Receives raw JPEG frames over WebSocket
- Runs YOLO detection + risk scoring every frame (with adaptive skipping if >50ms)
- Face anonymization via `PrivacyAnonymizer`
- Saves alerts to SQLite DB (configurable cooldown)
- Auto-starts clip recording at risk > `RECORDING_THRESHOLD`
- **Does NOT call VLM in real-time**

### 6b. `/stream/vlm-feed` (ML + VLM + Two-Tier Scoring)

**File:** `backend/api/routers/stream_vlm.py`

This is a significantly enhanced pipeline that integrates:

**Motion Detection (EMA-based MAD):**
- Downscales frames to 160×90 grayscale
- Computes mean absolute difference against previous frame
- EMA smoothing with α=0.12
- Motion spike: `diff > max(10, ema × 2.5)`
- Scene change: `diff > max(22, ema × 4.0)`

**Async VLM Analysis (runs in thread executor, doesn't block video):**
- Triggers every `VLM_ANALYSIS_INTERVAL` seconds (default 10, runtime-controllable)
- OR if `risk_score > 60` and last VLM was > `VLM_HIGH_RISK_INTERVAL` seconds ago
- OR if motion spike/scene change detected (with `CHANGE_TRIGGER_COOLDOWN`)
- While VLM is running, YOLO is paused and cached results are reused ("AI Thinking...")

**Rolling Narrative Context:**
- Maintains a `deque(maxlen=LIVE_VLM_CONTEXT_WINDOW)` of recent VLM narratives
- Injects prior narratives into the VLM prompt for temporal reasoning
- Enables the VLM to detect escalation/de-escalation patterns

**Two-Tier Score Integration:**
- Uses `TwoTierScoringService.aggregate_existing_scores()` to combine ML + VLM scores
- When VLM completes: `final_score = 0.3 × ML + 0.7 × AI`
- When VLM hasn't run: `final_score = ML_Score` (confidence=0.3)
- WebSocket response includes `ml_score`, `ai_score`, `final_score` separately

**Alert Persistence (now with VLM data):**
- `save_alert_sync()` now writes `ai_explanation`, `ai_scene_type`, `ai_confidence` to the `alerts` table
- Also stores `ml_score`, `ai_score`, `final_score`, and `detection_source`

**Runtime VLM Interval Control:**
- Frontend can send `{ "type": "set_vlm_interval", "seconds": N }` via WebSocket
- Bounded by `VLM_INTERVAL_MIN_SECONDS` (2) to `VLM_INTERVAL_MAX_SECONDS` (30)
- Persisted via `system_settings_service`

---

## 7. Uploaded Video Pipeline

**File:** `backend/services/offline_processor.py`

When a video is uploaded through the intelligence tab:

1. **Scan:** Finds all `.mp4/.avi/.mkv` files in `storage/clips/`
2. **ML Fast Filter:** Runs YOLO every `OFFLINE_ANALYSIS_INTERVAL` (2s) of video
3. **VLM Trigger:** Fires VLM analysis if:
   - YOLO detected a weapon, OR
   - YOLO detected people, OR
   - Periodic check every 6 seconds
4. **Audio Analysis:** Analyzes the audio track for threat sounds
5. **Video Summary:** Generates an LLM-synthesized executive summary via `vlm_service.summarize_events()`
6. **Metadata Store:** Saves events to `storage/metadata.json` (thread-safe with lock)
7. **Vector Index:** Auto-indexes all events + summary into ChromaDB
8. **Parallel Processing:** Up to 4 videos processed concurrently (`ThreadPoolExecutor`)

**Event structure stored per timestamp:**
```python
{
  "timestamp": 12.50,
  "description": "...",    # VLM-generated text
  "threats": ["fight"],    # Keyword-extracted tags
  "severity": "high",      # low/medium/high
  "provider": "CORTEX-VLM",
  "confidence": 0.85
}
```

---

## 8. Smart Video Storage & Bin Architecture

**File:** `backend/services/video_storage_service.py`

Industry-standard two-phase retention lifecycle with automatic background cleanup:

### Storage Layout
```
storage/
├── clips/     ← Active recordings land here
├── bin/       ← Soft-deleted clips awaiting final purge
├── metadata.json
└── vectordb/  ← ChromaDB persistent store
```

### Lifecycle Phases

| Phase | Location | Retention | Trigger |
|---|---|---|---|
| **Active** | `storage/clips/` | `LIVE_CLIP_RETENTION_HOURS` (default 24h) | Clips created by live recording |
| **Bin (Soft Delete)** | `storage/bin/` | `BIN_RETENTION_DAYS` (default 7 days) | Automatic sweep from clips/ |
| **Hard Delete** | Removed | — | Automatic sweep from bin/ |

### Recording Mechanics
- `start_recording(camera_id)`: Creates an `.mp4` file with `cv2.VideoWriter` at 10 FPS
- `add_frame(camera_id, frame)`: Writes frames; auto-stops after 30 seconds to chunk files
- `stop_recording(camera_id)`: Releases the writer
- Background cleanup thread runs every `cleanup_interval` (3600s)

---

## 9. Semantic Search (RAG)

**File:** `backend/services/search_service.py`

### Vector Store
- **Vector DB:** ChromaDB (persistent at `storage/vectordb`)
- **Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers (lazy-loaded on first search)
- **Collection:** `video_events_v2`
- **Fallback:** Keyword linear scan over `metadata.json` if ChromaDB/sentence-transformers not installed

### Search Methods

| Method | Description |
|---|---|
| `search(query, n_results, filename)` | Semantic vector search with keyword fallback |
| `timeline_search(query, filename, target_ts, limit)` | Hybrid retrieval: `0.55 × semantic + 0.25 × lexical + 0.20 × temporal` |
| `range_search(query, filename, start_ts, end_ts, limit)` | Time-bounded window search (temporal score = 1.0 for in-range events) |
| `count_matching(query, severity)` | Global counting grouped by video filename (top-K vector scan) |
| `cross_video_search(query, limit, severity)` | Cross-video grouping with per-video summary and event ranking |
| `get_video_record(filename)` | Direct metadata lookup for a specific video |

### Indexing
- `upsert_record(video_record)`: Indexes events + video summary incrementally
- `index_metadata()`: Bulk re-index from `metadata.json`
- Both summary text and individual events are stored as separate vector documents
- Summaries have `timestamp=-1.00` and `is_summary="true"` metadata flags

---

## 10. Database (SQLite/SQLAlchemy)

**File:** `backend/db/models.py`

Two tables:

**`alerts`** — Real-time threat alerts from live stream:
- `ml_score`, `ai_score`, `final_score`, `detection_source`
- `ai_explanation`, `ai_scene_type`, `ai_confidence`
- `status` (pending → acknowledged → resolved)
- `resolution_type`, `resolution_notes` (operator accountability)

**`system_settings`** — Key-value store for runtime config (e.g., VLM interval)

> [!NOTE]
> The `metadata.json` file (flat JSON) and `chromadb` (vector DB) are **separate** from SQLite. SQLite stores live-stream alerts; JSON/ChromaDB stores uploaded-video analysis. These are never merged/cross-queried at present.

---

## 11. Remaining Improvement Opportunities

### 🟡 Medium Priority

1. **Cross-camera ReID:** The `cross_video_search` groups by filename but doesn't track the same person across cameras. An embedding-based person re-identification model would enable "track suspect across all feeds."

2. **Audio-Visual Fusion:** `audio_service.py` runs independently during offline processing. Integrating audio threat cues (screams, glass breaking) into the two-tier scoring service would improve accuracy.

3. **Agent observation memory:** The agent currently gets 6 turns of history. A longer-term memory (e.g., summarized session context) would help in extended forensic investigation sessions.

### 🟢 Feature Upgrades

4. **Streaming VLM narrative history to frontend:** The rolling `narrative_history` deque in `stream_vlm.py` is only used for prompt context. Exposing it via the WebSocket response would let the frontend render a live event timeline.

5. **Batch visual QA:** The agent's `visual_qa` tool extracts one frame at a time. A batch mode extracting N frames across a time range would enable richer visual analysis.

6. **Confidence calibration:** VLM providers return different confidence ranges. A provider-specific calibration layer would normalize scores before fusion.
