# Aurora Sentinel Startup Script

Write-Host "🚀 Starting Aurora Sentinel..." -ForegroundColor Cyan

# Function to start a process in a new window
function Start-Component {
    param (
        [string]$Title,
        [string]$Command,
        [string]$Path
    )
    Write-Host "Starting $Title..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Path'; $Command"
}

# 1. Start Backend
Start-Component -Title "Backend API" -Command ".\venv\Scripts\python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload" -Path "$PSScriptRoot"

# 2. Start Frontend
# Check if node_modules exists, if not install
if (-not (Test-Path "$PSScriptRoot\frontend\node_modules")) {
    Write-Host "Installing Frontend Dependencies..." -ForegroundColor Yellow
    cd "$PSScriptRoot\frontend"
    npm install
    cd ..
}

Start-Component -Title "Frontend Dashboard" -Command "npm start" -Path "$PSScriptRoot\frontend"

Write-Host "✅ System Starting!" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:3000"
