# 👋 Hey! Want to Run AURORA on Your Machine?

This guide is written in simple words. Follow step by step and it will work.

---

## 🤔 First — Clone or Pull?

**Simple rule:**
- **First time on your machine? → CLONE**
- **Already have it and just want latest changes? → PULL**

---

## 🆕 FIRST TIME SETUP (Clone)

### Step 1 — Clone the project

```bash
git clone https://github.com/YOUR_USERNAME/aurora-fight-detection.git
cd aurora-fight-detection
```

> Replace `YOUR_USERNAME` with the actual GitHub username

---

### Step 2 — Install Python

Make sure you have **Python 3.10+** installed.
Check by running:
```bash
python --version
```

If not installed → download from https://www.python.org/downloads/

---

### Step 3 — Create a virtual environment

This keeps all packages separate from your system Python. **Don't skip this.**

```bash
python -m venv venv
```

Now activate it:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

You'll see `(venv)` appear in your terminal. That means it's active. ✅

---

### Step 4 — Install all Python packages

This will take 5-10 minutes. It downloads PyTorch, OpenCV, etc.

```bash
pip install -r requirements/backend.txt
```

Then install the AI layer packages too:

```bash
pip install -r requirements/ai-intelligence.txt
```

> ☕ Grab a coffee. PyTorch alone is ~3GB download.

---

### Step 5 — What about the missing files?

When you clone, some files are **intentionally NOT included** (they're in `.gitignore`).
Here's what's missing and what to do:

| Missing File/Folder | Why Missing | What To Do |
|---------------------|-------------|------------|
| `venv/` | Too big (5GB), everyone creates their own | Done in Step 3 above |
| `.env` | Contains secret API keys | Create it yourself (Step 6 below) |
| `storage/` | Generated at runtime | Auto-created when you run the app |
| `aurora.db` | Database, generated at runtime | Auto-created when you run the app |
| `frontend/node_modules/` | Too big, everyone installs their own | Run `npm install` in frontend folder |

---

### Step 6 — Create your `.env` file

The `.env` file has API keys. It's not pushed to GitHub for security.
Create a new file called `.env` in the root folder and paste this:

```env
# AI Intelligence Layer
LOCAL_AI_URL=http://localhost:3001/analyze

# Google Gemini API (optional but gives best accuracy)
# Get free key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_key_here

# HuggingFace Token (optional)
# Get free token from: https://huggingface.co/settings/tokens
HF_ACCESS_TOKEN=your_hf_token_here

# Settings
VLM_PROVIDER=auto
ALERT_THRESHOLD=60
DATABASE_URL=sqlite:///./aurora.db
STORAGE_DIR=storage/clips
```

> Ask the project owner (your friend who pushed it) to share their API keys with you privately — **never put real keys in GitHub.**

---

### Step 7 — Install Ollama (for local AI)

Ollama runs AI models locally on your machine. It's free.

1. Download from: https://ollama.com/download
2. Install it
3. Open a terminal and run:
   ```bash
   ollama pull llava:7b
   ```
   This downloads the AI model (~4GB). Do it once.

4. Start Ollama:
   ```bash
   ollama serve
   ```

---

### Step 8 — Setup the database

```bash
python apply_migration.py
```

---

### Step 9 — Install frontend packages

```bash
cd frontend
npm install
cd ..
```

---

### Step 10 — Run the project!

You need **3 terminals** open at the same time:

**Terminal 1 — Backend:**
```bash
venv\Scripts\activate
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — AI Intelligence Layer:**
```bash
venv\Scripts\activate
python ai-intelligence-layer/server_local.py
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm start
```

Now open your browser: **http://localhost:3000** 🎉

---

## 🔄 ALREADY HAVE IT — Just Want Latest Changes (Pull)

If you already cloned it before and just want the new code your friend pushed:

```bash
# Make sure venv is active first
venv\Scripts\activate

# Get latest code
git pull origin main

# Install any new packages that were added
pip install -r requirements/backend.txt

# Run the project (same as Step 10 above)
```

---

## ✏️ Want to Make Changes and Push Back?

### If you have direct access to the repo:

```bash
# 1. Get latest code first (always do this before making changes)
git pull origin main

# 2. Make your changes in the code...

# 3. See what you changed
git status

# 4. Stage your changes
git add -A

# 5. Save your changes with a message
git commit -m "what you changed here"

# 6. Push to GitHub
git push origin main
```

### If you DON'T have direct access (fork workflow):

```bash
# 1. Fork the repo on GitHub (click Fork button on GitHub)

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/aurora-fight-detection.git

# 3. Make changes, commit, push to YOUR fork

# 4. On GitHub, click "Pull Request" to send changes to the original repo
```

---

## ❓ Common Problems & Fixes

**"venv is not activated"**
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**"Module not found" error**
```bash
pip install -r requirements/backend.txt
```

**"Port 8000 already in use"**
```bash
# Windows — find and kill the process
netstat -ano | findstr :8000
taskkill /PID <the_number_shown> /F
```

**"Ollama not available"**
- Make sure Ollama is installed and running (`ollama serve`)
- Or just use Gemini API key instead

**"CUDA not available" (no GPU acceleration)**
- That's fine! It will run on CPU, just slower
- GPU is optional

**Frontend not loading**
```bash
cd frontend
npm install   # reinstall packages
npm start
```

---

## 📋 Quick Checklist

Before running, make sure you have:

- [ ] Python 3.10+ installed
- [ ] `venv` created and activated
- [ ] `pip install -r requirements/backend.txt` done
- [ ] `.env` file created with API keys
- [ ] Ollama installed and running (or Gemini key in .env)
- [ ] `python apply_migration.py` run once
- [ ] `npm install` done in frontend folder
- [ ] All 3 terminals running

---

## 💬 Still Stuck?

Ask your friend (the one who owns the repo) — they've already set it up and can help!

Or check `TROUBLESHOOTING_VLM.md` in the project for VLM-specific issues.
