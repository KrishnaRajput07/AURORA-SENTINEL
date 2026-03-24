#!/bin/bash
cd "$(dirname "$0")"
echo -e "\e[36mStarting Aurora Sentinel...\e[0m"

# Trap CTRL+C to kill all background jobs
trap "kill 0" EXIT

# 1. Start AI Intelligence Layer
echo -e "\e[33mStarting AI Intelligence Layer (Local Models)...\e[0m"
if [ -d "./ai-intelligence-layer/venv_ai" ]; then
    (cd ai-intelligence-layer && source venv_ai/bin/activate && python server_local.py) &
elif [ -d "./ai-intelligence-layer/node_modules" ]; then
    (cd ai-intelligence-layer && npm start) &
else
    echo -e "\e[33mAI Intelligence Layer not set up. Run setup_ai_local.ps1 first\e[0m"
    echo -e "\e[33mOr install Node.js dependencies: cd ai-intelligence-layer; npm install\e[0m"
fi

sleep 5

# 2. Start Backend
echo -e "\e[32mStarting Backend API...\e[0m"
(export PYTHONPATH='.'; source venv/bin/activate; python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload) &

sleep 5

# 3. Start Frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "\e[33mInstalling Frontend Dependencies...\e[0m"
    (cd frontend && npm install)
fi

echo -e "\e[32mStarting Frontend Dashboard...\e[0m"
(cd frontend && npm start) &

echo -e "\e[36mSystem Starting!\e[0m"
echo -e "\e[37mAI Intelligence Layer: http://localhost:3001 (Local Models)\e[0m"
echo -e "\e[37mBackend API: http://localhost:8000/docs\e[0m"
echo -e "\e[37mFrontend Dashboard: http://localhost:3000\e[0m"
echo -e ""
echo -e "\e[33mIMPORTANT: Wait for all services to fully initialize before using the system\e[0m"
echo -e "\e[33mPress Ctrl+C to stop all services\e[0m"
echo -e ""
echo -e "\e[36mNote: AI models will download automatically on first use (2-3 GB)\e[0m"
echo -e "\e[36mSubsequent starts will be much faster\e[0m"

# Wait for all background processes
wait
