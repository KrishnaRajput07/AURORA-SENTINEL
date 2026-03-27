# AURORA-SENTINEL — System Changelog & Diff Report

> **Date:** March 2026  
> **Compared:** Original analysis (v1) → Updated system (v2)  
> **Purpose:** Documents every architectural change, new subsystem, and fixed limitation

---

## Summary of Changes

| Area | Status | Impact |
|---|---|---|
| VLM Architecture | 🔄 **Refactored** | 6-provider waterfall → 2-provider + Nemotron verifier |
| AI Intelligence Layer (Node.js) | ⬇️ **Deprecated** | No longer in the runtime path |
| VLM Providers | 🔄 **Extracted** | Moved to dedicated `vlm_providers.py` module |
| Agentic Chatbot | ✅ **NEW** | ReAct tool-calling agent with 5 tools |
| Chat Sessions | ✅ **NEW** | Multi-turn memory with TTL eviction |
| Smart Video Storage | ✅ **NEW** | Clips → Bin → Delete lifecycle |
| Two-Tier Scoring in Live Feed | 🔧 **Fixed** | Was upload-only, now wired into `stream_vlm.py` |
| Alert DB VLM Fields | 🔧 **Fixed** | `ai_explanation`, `ai_scene_type` now persisted |
| Live VLM Context | 🔧 **Fixed** | Rolling narrative history in VLM prompts |
| Video Summary Generation | ✅ **NEW** | LLM-synthesized executive summaries |
| Timeline-Aware Chat | 🔧 **Fixed** | Hybrid retrieval replaces middle-frame heuristic |
| Runtime VLM Interval Control | ✅ **NEW** | Frontend can adjust VLM frequency via WebSocket |
| Config System | 🔄 **Expanded** | 50+ configurable parameters, env-var overrides |
| Cross-Video Search | ✅ **NEW** | `/intelligence/cross-search` endpoint |
| Range Search | ✅ **NEW** | Time-bounded window queries |

---

## Detailed Change Log

### 1. VLM Architecture — From 6-Provider Waterfall to Simplified Orchestrator

**BEFORE (v1):**
```
LocalAIProvider (port 3001)   ← Primary (calls Node.js AI Intelligence Layer)
 ↓ fails
Qwen2VLProvider               ← Local GPU model
 ↓ fails
OllamaProvider                ← Local Ollama
 ↓ fails
GeminiProvider                ← Cloud fallback
 ↓ fails
QwenProvider / HuggingFaceProvider  ← HF API (last resort)
```
- 6 providers with weighted fusion engine
- Primary route went through a Node.js HTTP server on port 3001
- Fusion weights: Qwen2-VL=0.30, Gemini=0.30, Ollama=0.15, Qwen=0.10, Nemotron=0.10, HF=0.05

**AFTER (v2):**
```
OllamaProvider (Qwen3-VL:235b-cloud)  ← Primary
 ↓ fails
GeminiProvider (rotating 5 model variants)  ← Backup
 ↓ fails
ML-only passthrough ← Fallback
```
- 2 providers with sequential fallback (no fusion — single provider result used)
- Nemotron is an optional **verifier**, not a provider
- No Node.js dependency in the runtime path
- Provider implementations extracted to `vlm_providers.py` (clean separation)

**Why:** Reduced latency, eliminated single-point-of-failure in Node.js layer, simplified debugging. The fusion engine's marginal accuracy gains didn't justify the complexity and cascading timeout risks.

---

### 2. Node.js AI Intelligence Layer — Deprecated

**BEFORE (v1):**
- `ai-intelligence-layer/server_local.py` ran on port 3001
- `aiRouter_enhanced.py` contained the Qwen2-VL → Ollama → Nemotron decision chain
- Backend called it via HTTP: `LocalAIProvider → POST http://localhost:3001/analyze`
- Had its own `model_availability.py` with cooldown tracking

**AFTER (v2):**
- Files still exist on disk but are **not referenced** by the backend at runtime
- All VLM inference handled natively within FastAPI process
- `vlm_service.py` directly calls `OllamaProvider` and `GeminiProvider`

> [!IMPORTANT]
> The `ai-intelligence-layer/` directory still exists in the repository. It contains legacy code including `aiRouter_enhanced.py` (38KB), `model_availability.py`, and `qwen2vl_integration.py`. These are not imported or executed by the current system.

---

### 3. Agentic Chatbot — NEW System

**BEFORE (v1):**
```python
# Old flow (4-level waterfall):
1. Find video file (or use latest)
2. Extract ONE frame from the MIDDLE of the video
3. Call vlm_service.answer_question(image_data, question)
4. Fallback: keyword-match against metadata.json
5. Return: "Please upload a video first"
```
- **Stateless** — no conversation history
- **Middle-frame only** — no timeline awareness
- **No tool selection** — always ran the same waterfall

**AFTER (v2):**

New `agent_service.py` provides a ReAct tool-calling agent:
```python
# New flow (agent loop):
1. Load conversation history (last 6 turns)
2. LLM decides which tool(s) to call:
   - timeline_search (with optional time ranges)
   - count_events (aggregate statistics)
   - visual_qa (frame extraction at specific timestamp)
   - cross_video_search (multi-camera correlation)
   - get_video_info (video metadata)
3. Execute tool → inject results → LLM decides next action
4. Repeat up to AGENT_MAX_TOOL_CALLS (3) iterations
5. Return synthesized answer with audit trail
```

The deterministic path (Path A) also received major upgrades:
- **Timestamp extraction** from natural language ("2 minutes", "1:30", "beginning")
- **Time range parsing** ("from 80s to 120s", "between 80 and 120 seconds")
- **Hybrid timeline search** with `0.55 × semantic + 0.25 × lexical + 0.20 × temporal` blending
- **Smart visual fallback** — only triggers VLM for visual queries ("what color", "who is")
- **Frame extraction at relevant timestamp** instead of middle frame

---

### 4. Multi-Turn Conversation Memory — NEW System

**BEFORE (v1):**
- The `/chat` endpoint was completely stateless
- Each request was independent — no concept of "follow-up" questions

**AFTER (v2):**

New `chat_session_store.py`:
```python
InMemoryChatSessionStore(
    ttl_seconds=1800,  # 30 min session lifetime
    max_turns=12        # Rolling history window
)
```
- UUID-based session IDs
- Thread-safe with `threading.Lock`
- Automatic TTL-based eviction
- History injected into both agent and deterministic chat paths

---

### 5. Smart Video Storage & Bin — NEW System

**BEFORE (v1):**
- No mention of storage lifecycle management
- Clips accumulated without cleanup

**AFTER (v2):**

New `video_storage_service.py`:
```
clips/ ──(24h)──> bin/ ──(7 days)──> deleted
```
- Background daemon thread runs cleanup every hour
- Configurable via `LIVE_CLIP_RETENTION_HOURS` and `BIN_RETENTION_DAYS`
- Thread-safe recording management with auto-chunking (30s max per file)
- Failed cleanups don't crash the daemon (exception handling in loop)

---

### 6. Two-Tier Scoring — Now Wired into Live Feed

**BEFORE (v1):**

> [!WARNING]
> The original analysis flagged this as a medium-priority bug: *"stream.py and stream_vlm.py use the RiskScoringEngine directly but don't use TwoTierScoringService. That means the 0.3×ML + 0.7×AI weighted formula is only applied in uploaded video processing, not live surveillance."*

**AFTER (v2):**

`stream_vlm.py` now creates `TwoTierScoringService` and calls `aggregate_existing_scores()`:
- On every ML-only frame: aggregates with `ai_score=None` → `final_score = ml_score`
- When VLM completes: aggregates with both scores → `final_score = 0.3×ML + 0.7×AI`
- WebSocket response includes separate `ml_score`, `ai_score`, and `final_score` fields
- Alert generation uses the full `TwoTierScoringService` result with `AlertService`

---

### 7. Alert DB — VLM Fields Now Populated

**BEFORE (v1):**

> [!WARNING]
> The original analysis flagged: *"When a VLM analysis escalates risk during live feed, the save_alert_sync() function doesn't write the ai_explanation or ai_scene_type to the alerts table."*

**AFTER (v2):**

`save_alert_sync()` in `stream_vlm.py` now writes:
```python
Alert(
    ml_score=...,
    ai_score=...,
    final_score=...,
    detection_source=...,
    ai_explanation=alert_data.get("ai_explanation") or alert_data.get("ai_analysis"),
    ai_scene_type=alert_data.get("ai_scene_type"),
    ai_confidence=float(alert_data.get("ai_confidence", 0.0)),
)
```

---

### 8. Live VLM Context — Rolling Narrative History

**BEFORE (v1):**

> [!WARNING]
> Original flag: *"The stream_vlm.py VLM trigger sends a single frame with no history. Pass the last N VLM narratives as context in the prompt."*

**AFTER (v2):**

```python
narrative_history = deque(maxlen=LIVE_VLM_CONTEXT_WINDOW)  # default 4
```

When triggering a new VLM analysis, the prompt now includes:
```
Recent scene history:
- Prior (72.0%): Two individuals engaged in physical confrontation
- Prior (45.0%): Scene appears calm, normal pedestrian activity
```
This enables the VLM to detect escalation/de-escalation patterns and provide temporally-aware analysis.

---

### 9. Video Summary Generation — NEW Feature

**BEFORE (v1):**

> The original analysis recommended: *"After offline_processor finishes, generate a single LLM-synthesized paragraph summarizing the entire video."*

**AFTER (v2):**

`vlm_service.summarize_events(filename, events)`:
- Takes the first 20 events from a processed video
- Formats them as context blocks: `[timestamp][severity] description`
- Feeds to `answer_with_context()` with prompt: "Provide an executive summary for video 'filename'"
- Returns `{ summary, provider, confidence }`
- Stored in `metadata.json` as `video_summary` field
- Indexed in ChromaDB as a separate document (`is_summary: "true"`)

---

### 10. Search Enhancements — Range Search & Cross-Video

**BEFORE (v1):**
- Basic semantic search with keyword fallback
- No time-bounded queries
- No cross-video grouping

**AFTER (v2):**

| New Method | Capability |
|---|---|
| `range_search(query, filename, start_ts, end_ts)` | Time-bounded window; hybrid scoring with temporal=1.0 for in-range events |
| `cross_video_search(query, limit, severity)` | Groups results by filename, includes video summary, per-video event ranking |
| `count_matching(query, severity)` | Global counting with severity filter, returns `{ total_videos, total_events, videos: [...] }` |
| `timeline_search()` | Upgraded: now uses blended `0.55 × semantic + 0.25 × lexical + 0.20 × temporal` scoring |

New endpoint: `GET /intelligence/cross-search?q=fight&limit=5&severity=high`

---

### 11. Runtime VLM Interval Control — NEW Feature

**BEFORE (v1):**

> Original recommendation: *"Let the frontend set VLM_INTERVAL via a WebSocket message."*

**AFTER (v2):**

Frontend sends via WebSocket:
```json
{ "type": "set_vlm_interval", "seconds": 5 }
```
Backend responds:
```json
{ "type": "config_ack", "vlm_interval_seconds": 5 }
```
- Bounded by `VLM_INTERVAL_MIN_SECONDS` (2) to `VLM_INTERVAL_MAX_SECONDS` (30)
- Persisted via `system_settings_service.py` (survives reconnections within session)

---

### 12. Config System Expansion

**BEFORE (v1):** ~6 config settings  

**AFTER (v2):** 30+ settings organized by category:

| Category | Example Settings |
|---|---|
| Model Selection | `PRIMARY_VLM_PROVIDER`, `OLLAMA_CLOUD_MODEL`, `AGENT_MODEL` |
| Scoring Weights | `ML_SCORE_WEIGHT`, `AI_SCORE_WEIGHT`, `SPORT_RISK_CAP` |
| Thresholds | `ALERT_THRESHOLD`, `LIVE_ALERT_THRESHOLD`, `RECORDING_THRESHOLD` |
| Timing | `VLM_ANALYSIS_INTERVAL`, `ALERT_COOLDOWN_SECONDS`, `CHANGE_TRIGGER_COOLDOWN` |
| Timeouts | `AI_TOTAL_TIMEOUT`, `NEMOTRON_TIMEOUT`, `QWEN_TIMEOUT` |
| Severity | `SEVERITY_HIGH_THRESHOLD`, `SEVERITY_MEDIUM_THRESHOLD` |
| Confidence | `CONFIDENCE_BOTH_AVAILABLE`, `CONFIDENCE_ML_ONLY`, `CONFIDENCE_AI_ONLY` |
| Chat | `CHAT_SESSION_TTL_SECONDS`, `CHAT_MAX_TURNS`, `CHAT_TIMELINE_LIMIT` |
| Agent | `AGENT_MAX_TOOL_CALLS`, `AGENT_TEMPERATURE`, `COUNT_SEARCH_LIMIT` |

All settings support `os.getenv()` overrides for deployment flexibility.

---

## Original Recommendations — Status Tracker

| # | Recommendation | Priority | Status |
|---|---|---|---|
| 1 | Timeline-aware chatbot | 🔴 High | ✅ **DONE** — timeline_search + range_search + hybrid scoring |
| 2 | Multi-turn conversation context | 🔴 High | ✅ **DONE** — `chat_session_store.py` |
| 3 | Smarter frame selection for visual Q&A | 🔴 High | ✅ **DONE** — timestamp parsing + event-based frame extraction |
| 4 | Return structured timeline in chat | 🔴 High | ✅ **DONE** — `timeline` field in chat response |
| 5 | Live feed VLM is stateless | 🟡 Medium | ✅ **DONE** — rolling `narrative_history` deque |
| 6 | Two-tier scoring not wired into live feed | 🟡 Medium | ✅ **DONE** — `aggregate_existing_scores()` in stream_vlm |
| 7 | Alert DB doesn't store VLM narrative | 🟡 Medium | ✅ **DONE** — `save_alert_sync()` writes all AI fields |
| 8 | Nemotron disabled by default | 🟡 Medium | ✅ **DONE** — lazy-load on first use via `_get_nemotron()` |
| 9 | Video-level summary | 🟢 Feature | ✅ **DONE** — `summarize_events()` in vlm_service |
| 10 | Cross-video search | 🟢 Feature | ✅ **DONE** — `cross_video_search()` + REST endpoint |
| 11 | Agent-style chatbot loop | 🟢 Feature | ✅ **DONE** — full ReAct agent, feature-flagged |
| 12 | Real-time VLM frequency control | 🟢 Feature | ✅ **DONE** — WebSocket `set_vlm_interval` message |

**All 12 original recommendations have been addressed.**
