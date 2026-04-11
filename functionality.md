# AURORA Sentinel — Root Functionality

AURORA Sentinel is an AI-powered real-time surveillance and violence detection system with a dual-brain architecture combining ML detection with AI intelligence verification.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AURORA SENTINEL                              │
│                    Dual-Brain Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────┐    ┌──────────────────────────┐    │
│  │   🔬 ANALYTICAL BRAIN    │    │  🎨 CONTEXTUAL BRAIN     │    │
│  │      (ML Detection)      │◄──►│    (AI Intelligence)     │    │
│  │                          │    │                          │    │
│  │  • YOLOv8 Detection      │    │  • VLM Verification      │    │
│  │  • Pose Estimation       │    │  • Scene Understanding   │    │
│  │  • Risk Scoring Engine   │    │  • Natural Language QA   │    │
│  │  • Anomaly Detection     │    │  • Multi-Model Ensemble  │    │
│  └──────────────────────────┘    └──────────────────────────┘    │
│           │                                    │                   │
│           └──────────────┬───────────────────────┘                   │
│                          ▼                                         │
│              ┌─────────────────────┐                              │
│              │   TWO-TIER SCORING  │                              │
│              │   final_score =     │                              │
│              │   max(ML, 0.3ML +    │                              │
│              │   0.7*AI)           │                              │
│              └─────────────────────┘                              │
│                          │                                         │
│                          ▼                                         │
│              ┌─────────────────────┐                              │
│              │   ALERT GENERATION  │                              │
│              │   → Operator UI     │                              │
│              │   → Smart Clips     │                              │
│              │   → Archive         │                              │
│              └─────────────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

| Directory | Purpose | See |
|-----------|---------|-----|
| `ai-intelligence-layer/` | AI VLM orchestration and routing | `ai-intelligence-layer/functionality.md` |
| `backend/` | FastAPI backend services | `backend/functionality.md` |
| `config/` | YAML configuration files | `config/functionality.md` |
| `frontend/` | React web application | `frontend/functionality.md` |
| `models/` | ML detection and scoring models | `models/functionality.md` |
| `readMes/` | Documentation files | `readMes/functionality.md` |
| `requirements/` | Python dependencies | `requirements/functionality.md` |
| `scripts/` | Utility and diagnostic scripts | `scripts/functionality.md` |
| `test_results/` | Test execution outputs | `test_results/functionality.md` |
| `tests/` | Comprehensive test suite | `tests/functionality.md` |

## Key Configuration Files

### `config.py` (Root Level)
- Central configuration hub for the entire system
- **AI Model Selection**: `PRIMARY_VLM_PROVIDER` (ollama_cloud | qwen2vl_local)
- **Scoring Weights**: `ML_SCORE_WEIGHT=0.3`, `AI_SCORE_WEIGHT=0.7`
- **Thresholds**: Alert at 60%, recording at 50%, skip AI below 20%
- **Timeouts**: AI total 5s, Nemotron 3s, Qwen 2s
- **Agent Settings**: Model, max tool calls, temperature

### `Dockerfile`
- Multi-stage build: Node.js frontend → Python backend
- CPU-optimized PyTorch (saves ~2.5GB vs CUDA)
- System dependencies: ffmpeg, OpenCV libraries

### `docker-compose.yml`
- Full stack orchestration: API, PostgreSQL, Redis
- GPU reservations for NVIDIA support
- Volume mounts for data persistence

### `start.sh` / `start.ps1`
- Cross-platform startup scripts
- Environment initialization and server launch

## Data Flow

1. **Live Stream**: WebSocket → ML Detection → Two-tier Scoring → Alert → Smart Clip
2. **Upload**: HTTP POST → Offline Processor → Frame-by-frame Analysis → Results
3. **Search**: Query → Embedding → ChromaDB → Ranked Results → Frontend
4. **Chatbot**: Question → Intent Routing → Tool Call → DB/VLM → Answer

## Key Features

| Feature | Description | Accuracy |
|---------|-------------|----------|
| Violence Detection | ML+AI two-tier scoring | 97% with Gemini |
| Sport Discrimination | Distinguishes real fights from boxing | Zero false positives |
| Smart Clip Capture | Auto-record 10s before+after incident | Configurable |
| Semantic Search | Natural language event search | Vector-based |
| AI Chatbot | Surveillance Q&A with tool calling | Context-aware |
| Privacy Anonymization | Face blurring for compliance | Real-time |

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React, MUI, Framer Motion, Leaflet, Recharts |
| Backend | FastAPI, SQLAlchemy, WebSocket |
| ML | YOLOv8, MediaPipe, PyTorch, scikit-learn |
| AI | Ollama, Gemini API, Qwen2-VL, Nemotron |
| Database | SQLite (dev) / PostgreSQL (prod), ChromaDB |
| DevOps | Docker, Docker Compose, Git LFS |

## Performance
- ML Detection: <100ms latency
- AI Analysis: 2–5 seconds (GPU)
- Frame Rate: 30 FPS live processing
- Concurrent Streams: Multi-camera ready

## Documentation
Each directory contains its own `functionality.md` with detailed component descriptions.
