# 👋 Hey! Want to Run AURORA on Your Machine?

This guide is written in simple words. Follow step by step and it will work.

---

## 🤔 First — Clone or Pull?

**Simple rule:**
- **First time on your machine? → CLONE**
- **Already have it and just want latest changes? → PULL**

---

## ✅ Prerequisites

Install these before you start:

| Tool | Why? | Download Link |
|------|------|---------------|
| **Python 3.10+** | Runs the backend | [python.org](https://www.python.org/downloads/) |
| **Node.js 18+** | Runs the frontend | [nodejs.org](https://nodejs.org/) |
| **Git** | Downloads the code | [git-scm.com](https://git-scm.com/) |
| **FFmpeg** | Processes video clips | [ffmpeg.org](https://ffmpeg.org/download.html) |
| **Ollama** (Optional) | Local AI analysis | [ollama.com](https://ollama.com/) |

> [!IMPORTANT]
> **FFmpeg is required.** On Windows, download the "essentials" build, extract it, and add the `bin` folder to your Path.

---

## 🆕 FIRST TIME SETUP (Clone)

### Step 1 — Clone the project
```bash
git clone https://github.com/pratap-shrey/AURORA-SENTINEL.git
cd AURORA-SENTINEL
```

### Step 2 — Get the "Large Assets" (Optional but Recommended)
The AI models and sample videos are very large (~5GB). Instead of downloading them via scripts, ask the project owner for the **`AURORA_ASSETS.rar`** file.
- Extract it into the root folder.
- It should give you the `models/` and `data/` folders ready to use.

---

### Step 3 — Create a virtual environment
```bash
python -m venv venv
```
**Activate it:**
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### Step 4 — Install dependencies
```bash
# Install Backend dependencies
pip install -r requirements/backend.txt

# Install AI Intelligence dependencies
pip install -r requirements/ai-intelligence.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

---

### Step 5 — Create your `.env` file
Create a file named `.env` in the root folder and paste this:

```env
# AI Provider: gemini or ollama
VLM_PROVIDER=gemini

# Google Gemini API Key (Get at: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_key_here

# Local AI URL (Only if using local-ai-layer)
LOCAL_AI_URL=http://localhost:3001/analyze

# Database & Storage
DATABASE_URL=sqlite:///./aurora.db
STORAGE_DIR=storage/clips
```

---

## 🚀 HOW TO RUN (THE EASY WAY)

We've created automation scripts so you don't have to open 3 terminals.

### Windows (PowerShell):
```powershell
.\start.ps1
```

### Linux / WSL / Mac:
```bash
chmod +x start.sh
./start.sh
```
*This will automatically start the AI Layer, Backend, and Frontend for you.*

---

## 🐳 Running with Docker (Easiest)
If you have Docker Desktop installed, just run:
```bash
docker-compose up --build
```
Everything will start automatically inside containers.

---

## 🔄 ALREADY HAVE IT? (Update)
```bash
git pull origin main
pip install -r requirements/backend.txt
cd frontend && npm install && cd ..
python apply_migration.py
```

---

## ❓ Common Problems

- **"FFmpeg not found":** You must add FFmpeg to your system PATH.
- **Port 8000/3000 in use:** A previous run might still be stuck. Restart your terminal or kill the process.
- **Venv not active:** Make sure you see `(venv)` in your terminal before running commands.

---

## 📋 Quick Checklist
- [ ] Python 3.10+ & Node.js installed
- [ ] FFmpeg installed and in PATH
- [ ] `venv` created and activated
- [ ] `.env` file created with valid Gemini Key
- [ ] `npm install` done in `frontend/`
- [ ] Model files (`.pt`) present in root or `models/`

---

## 💬 Still Stuck?
Ask the project owner! They can help you debug specific environment issues.
