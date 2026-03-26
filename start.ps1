# Aurora Sentinel Startup Script
Set-Location "$PSScriptRoot"

Write-Host "Starting Aurora Sentinel..." -ForegroundColor Cyan

# Function to start a process in a new window
function Start-Component {
    param (
        [string]$Title,
        [string]$Command,
        [string]$Path
    )
    Write-Host "Starting $Title..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd '$Path'; $Command"
}

# 1. Start AI Intelligence Layer (Python-based with local models)
$provider = if ($env:PRIMARY_VLM_PROVIDER) { $env:PRIMARY_VLM_PROVIDER } else { "ollama_cloud" }
if ($provider -eq "ollama_cloud") {
    Write-Host "Starting AI Intelligence Layer (Ollama Cloud primary, local Qwen2 fallback)..." -ForegroundColor Yellow
} else {
    Write-Host "Starting AI Intelligence Layer (Local Qwen2 primary)..." -ForegroundColor Yellow
}

if (Test-Path ".\ai-intelligence-layer\venv_ai") {
    # Use Python-based AI layer with local models
    Start-Component -Title "AI Intelligence Layer (Local)" -Command ".\venv_ai\Scripts\Activate.ps1; python server_local.py" -Path "$PSScriptRoot\ai-intelligence-layer"
} elseif (Test-Path "$PSScriptRoot\venv") {
    # Use root venv which has AI layer dependencies installed
    Start-Component -Title "AI Intelligence Layer (Local)" -Command "..\venv\Scripts\Activate.ps1; python server_local.py" -Path "$PSScriptRoot\ai-intelligence-layer"
} elseif (Test-Path "$PSScriptRoot\ai-intelligence-layer\node_modules") {
    # Fallback to Node.js version if available
    Start-Component -Title "AI Intelligence Layer (Node)" -Command "npm start" -Path ".\ai-intelligence-layer"
} else {
    Write-Host "AI Intelligence Layer not set up. Run setup_ai_local.ps1 first" -ForegroundColor Yellow
    Write-Host "Or install Node.js dependencies: cd ai-intelligence-layer; npm install" -ForegroundColor Yellow
}

# Wait for AI layer to start
Write-Host "Waiting for AI Intelligence Layer to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 2. Start Backend
Start-Component -Title "Backend API" -Command "`$env:PYTHONPATH='.'; .\venv\Scripts\python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload" -Path "."

# Wait for backend to start and load AI models
Write-Host "Waiting for Backend to initialize and load AI models into GPU (this may take 15-30 seconds)..." -ForegroundColor Yellow
$apiReady = $false
$retryCount = 0
while (-not $apiReady -and $retryCount -lt 30) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $apiReady = $true
            Write-Host "Backend API is ready!" -ForegroundColor Green
        }
    } catch {
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
        $retryCount++
    }
}
Write-Host ""
if (-not $apiReady) {
    Write-Host "Warning: Backend initialization took longer than expected. Proceeding anyway..." -ForegroundColor Red
}
# 3. Start Frontend
# Check if node_modules exists, if not install
if (-not (Test-Path ".\frontend\node_modules")) {
    Write-Host "Installing Frontend Dependencies..." -ForegroundColor Yellow
    cd ".\frontend"
    npm install
    cd ..
}

Start-Component -Title "Frontend Dashboard" -Command "npm start" -Path ".\frontend"

Write-Host "System Starting!" -ForegroundColor Cyan
Write-Host "AI Intelligence Layer: http://localhost:3001 (Provider Router)" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Wait for all services to fully initialize before using the system" -ForegroundColor Yellow
Write-Host "Check each window for startup complete messages" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: Local fallback models are lazy-loaded on first fallback use" -ForegroundColor Cyan
Write-Host "If PRIMARY_VLM_PROVIDER=ollama_cloud, Qwen2 is not preloaded at startup" -ForegroundColor Cyan
