# Aurora Sentinel 🛡️

**Aurora Sentinel** is an advanced intelligent video analytics and surveillance platform providing real-time threat detection, AI-powered scene understanding, and full incident management through a modern responsive dashboard.

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat&logo=react)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.7.1+cu118-EE4C2C?style=flat&logo=pytorch)](https://pytorch.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.4.14-00FFFF?style=flat)](https://docs.ultralytics.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🚀 Features

### 🔴 Live Detection (WebSocket)
- **Real-time object & person tracking** via YOLOv8 + ByteTrack
- **Weapon detection** using a custom-trained `wepon.pt` model (~250MB) with red bounding box overlays
- **Pose estimation** via `yolov8n-pose.pt` to detect aggressive postures
- **Privacy anonymization** — automatic face blur on live feed
- **Adaptive frame skipping** — dynamically adjusts processing rate to stay real-time

### 🧠 AI Scene Intelligence (VLM)
- **Dual-provider VLM** — switch between:
  - **Google Gemini 2.0 Flash** (cloud, high throughput)
  - **Ollama / LLaVA** (local, fully offline)
- **Offline batch processor** — scans recorded clips, runs VLM analysis, extracts threat descriptions
- **Semantic search** (`ChromaDB` + `sentence-transformers`) — natural language queries like *"find a person with a knife near the gate"*
- **Audio analysis** — extracts audio from video clips via `moviepy`, runs HuggingFace `transformers` audio pipeline

### 🚨 Alert & Incident Management
- Risk scoring engine with configurable thresholds (alerts trigger at score > 65, recording starts at > 80)
- Alert lifecycle: **Pending → Acknowledged → Resolved** with operator name tracking
- Alert deduplication with 10-second cooldown to prevent DB flooding
- Auto video recording on high-risk events (saved to `storage/recordings/`)
- Incident report generation (PDF export via `jsPDF` + `jspdf-autotable`)

### 📊 Dashboard & Analytics
- Live feed panel with detection overlays and risk meter
- Historical alert timeline with filterable status
- Geospatial camera map (Leaflet / React-Leaflet)
- Real-time charts (Recharts + Framer Motion animations)
- Archive viewer with VLM-generated descriptions and severity tags

---

## 🛠️ Tech Stack

### Backend
| Component | Package | Version |
|---|---|---|
| API Framework | FastAPI | 0.129.0 |
| Server | Uvicorn | 0.40.0 |
| Object Detection | Ultralytics YOLOv8 | 8.4.14 |
| ML Framework | PyTorch (CUDA 11.8) | 2.7.1+cu118 |
| Computer Vision | OpenCV | 4.13.0 |
| VLM — Cloud | google-generativeai (Gemini 2.0 Flash) | 0.8.6 |
| VLM — Local | Ollama Python client | 0.6.1 |
| Audio/Video | MoviePy | 2.2.1 |
| Audio ML | HuggingFace Transformers | 5.1.0 |
| Embeddings | sentence-transformers | 5.2.2 |
| Vector DB | ChromaDB | 1.5.0 |
| Database ORM | SQLAlchemy | 2.0.46 |
| Language | Python | 3.10+ |

### Frontend
| Component | Package | Version |
|---|---|---|
| Framework | React | 18.2.0 |
| UI Library | Material UI (MUI) | 5.14.5 |
| Icons | Lucide React | 0.563.0 |
| Animations | Framer Motion | 12.33.0 |
| Maps | React-Leaflet | 4.2.1 |
| Charts | Recharts | 2.8.0 |
| Real-time | Socket.io-client | 4.7.2 |
| HTTP | Axios | 1.5.0 |
| PDF Reports | jsPDF + jspdf-autotable | 4.1.0 / 5.0.7 |

---

## 📡 API Overview

| Route | Method | Description |
|---|---|---|
| `/ws/live-feed` | WebSocket | Real-time video stream with ML detections |
| `/vlm/vlm-feed` | WebSocket | VLM-enhanced stream with AI scene descriptions |
| `/alerts/recent` | GET | Active alerts (pending/acknowledged) |
| `/alerts/history` | GET | Resolved alert history |
| `/alerts/{id}/acknowledge` | POST | Acknowledge an alert |
| `/alerts/{id}/resolve` | POST | Resolve and archive an alert |
| `/intelligence/search` | GET | Semantic search across recorded footage |
| `/intelligence/process` | POST | Trigger offline VLM processing |
| `/intelligence/latest` | GET | Latest AI-generated insights |
| `/analytics` | GET | Dashboard statistics |
| `/archive` | GET | Paginated recording archive |
| `/health` | GET | System health + model status |
| `/docs` | GET | Swagger UI |

---

## 🏁 Getting Started

> **See [REPLICATION.md](REPLICATION.md) for the full step-by-step setup guide.**

### Quick Start (Windows)

```powershell
# 1. Clone
git clone https://github.com/git-pratap-shrey/AURORA-SENTINEL.git
cd AURORA-SENTINEL
git checkout finalreplication

# 2. Python environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure
copy .env.example .env   # then edit .env with your settings

# 4. Frontend
cd frontend; npm install; cd ..

# 5. Run
.\start.ps1
```

### Access Points

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 📂 Project Structure

```
AURORA-SENTINEL/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app, CORS, router registration
│   │   └── routers/
│   │       ├── stream.py        # WebSocket live feed (YOLO + risk engine)
│   │       ├── stream_vlm.py    # WebSocket VLM-enhanced feed
│   │       ├── alerts.py        # Alert CRUD & lifecycle management
│   │       ├── intelligence.py  # Semantic search & offline processing
│   │       ├── video.py         # Offline video upload & processing
│   │       ├── archive.py       # Recording archive browser
│   │       └── analytics.py     # Dashboard statistics
│   ├── services/
│   │   ├── vlm_service.py       # Gemini / Ollama provider abstraction
│   │   ├── ml_service.py        # YOLO model loader & inference
│   │   ├── audio_service.py     # Audio extraction & HuggingFace pipeline
│   │   ├── offline_processor.py # Batch VLM analysis of recordings
│   │   ├── search_service.py    # ChromaDB vector search
│   │   └── video_storage_service.py # Auto-recording on high-risk events
│   └── db/
│       ├── models.py            # SQLAlchemy Alert model
│       └── database.py          # DB engine (SQLite default / PostgreSQL)
├── frontend/                    # React dashboard
├── models/                      # Python model scoring/detection logic
├── data/                        # Sample videos & datasets
├── storage/                     # Runtime recordings (gitignored)
├── wepon.pt                     # Custom weapon detection weights (~250MB)
├── yolov8n.pt                   # YOLOv8 Nano general detection
├── yolov8s.pt                   # YOLOv8 Small general detection
├── yolov8n-pose.pt              # YOLOv8 Pose estimation
├── requirements.txt
├── .env.example                 # Environment template
├── REPLICATION.md               # Full dev setup guide
├── start.ps1                    # Windows one-click launcher
└── docker-compose.yml           # Container orchestration
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```env
VLM_PROVIDER=ollama          # gemini | ollama
GEMINI_API_KEY=...           # required if VLM_PROVIDER=gemini
OLLAMA_MODEL=llava           # llava | llava:13b | moondream | bakllava
```

---

## 🐳 Docker

```bash
docker-compose up --build
```

Starts backend, PostgreSQL, and Redis. Frontend served statically from `frontend/build`.
