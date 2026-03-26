# 👋 Hey! Want to Run AURORA on Your Machine?

This guide is simple and updated for the current codebase.

---

## 🤔 First: Clone or Pull?

Simple rule:
- First time on your machine -> **CLONE**
- You already have the repo -> **PULL**

---

## ✅ Prerequisites

Install these first:

| Tool | Why? | Download |
|------|------|----------|
| Python 3.10+ | Backend + AI layer | [python.org](https://www.python.org/downloads/) |
| Node.js 18+ | Frontend dev server | [nodejs.org](https://nodejs.org/) |
| Git | Clone/pull code | [git-scm.com](https://git-scm.com/) |
| FFmpeg | Video processing/transcode | [ffmpeg.org](https://ffmpeg.org/download.html) |
| Ollama (optional) | If using Ollama provider | [ollama.com](https://ollama.com/) |

> [!IMPORTANT]
> FFmpeg must be on your system `PATH`.

---

## 🆕 First-Time Setup (Clone)

### 1) Clone
```bash
git clone https://github.com/git-pratap-shrey/AURORA-SENTINEL.git
cd AURORA-SENTINEL
```

### 2) Large assets (optional but recommended)
Models + sample data can be large. If available, get `AURORA_ASSETS.rar` from the project owner and extract at repo root so folders like `models/` and `data/` are present.

### 3) Create and activate virtual environment
```bash
python -m venv venv
```

Activate:
- Windows: `venv\Scripts\activate`
- Linux/Mac/WSL: `source venv/bin/activate`

### 4) Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements/backend.txt
pip install -r requirements/ai-intelligence.txt
cd frontend && npm install && cd ..
```

### 5) Create `.env` in repo root
Use this starter:

```env
# AI provider routing
# Options: ollama_cloud | qwen2vl_local
PRIMARY_VLM_PROVIDER=ollama_cloud

# Ollama model tag used by backend VLM provider
OLLAMA_CLOUD_MODEL=qwen3-vl:235b-cloud

# Local Qwen2-VL model
QWEN2VL_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct

# Optional cloud fallback
GEMINI_API_KEY=your_key_here

# Local heavy model gate (Nemotron verification)
ENABLE_HEAVY_MODELS=false

# DB + storage
DATABASE_URL=sqlite:///./aurora.db
STORAGE_DIR=storage/clips
PROCESSED_PATH=storage/processed
BIN_PATH=storage/bin
TEMP_PATH=storage/temp
```

---

## 🚀 Run (Easy Way)

### Windows (PowerShell)
```powershell
.\start.ps1
```

### Linux / WSL / Mac
```bash
chmod +x start.sh
./start.sh
```

This starts:
- AI layer on `http://localhost:3001`
- Backend API on `http://localhost:8000/docs`
- Frontend on `http://localhost:3000`

---

## 🔄 Update Existing Setup

```bash
git pull origin main
pip install -r requirements/backend.txt
pip install -r requirements/ai-intelligence.txt
cd frontend && npm install && cd ..
```

Notes:
- Do **not** run `python apply_migration.py` (that script does not exist).
- Database/table creation and alert-column compatibility are handled at backend startup.

---

## 🐳 Docker (What It Actually Starts)

```bash
docker-compose up --build
```

Current compose starts:
- `api` (FastAPI on `8000`)
- `postgres`
- `redis`

It does not start the frontend dev server on `3000`.

---

## ❓ Common Problems

- `"ffmpeg not found"`: Add FFmpeg `bin` to `PATH`.
- Ports busy (`3000`, `3001`, `8000`): stop old processes and retry.
- Venv not active: ensure prompt shows `(venv)` before pip/python commands.
- AI layer fails to start: run `pip install -r requirements/ai-intelligence.txt` again in your active venv.
- Ollama errors with `PRIMARY_VLM_PROVIDER=ollama_cloud`: start Ollama locally or switch to `PRIMARY_VLM_PROVIDER=qwen2vl_local`.
- First run is slow: model downloads can take several GB.

---

## 📋 Quick Checklist

- [ ] Python 3.10+ and Node.js 18+ installed
- [ ] FFmpeg installed and available on `PATH`
- [ ] `venv` created and activated
- [ ] Backend + AI + frontend dependencies installed
- [ ] `.env` created with valid values
- [ ] Model files (`yolov8*.pt`) available in repo root (or downloaded on first use)

---

## 💬 Still Stuck?

Share:
- Your OS
- The exact command you ran
- The full error text

Then the project owner can debug quickly.