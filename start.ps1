# AURORA Sentinel - One-command startup
# Usage: .\start.ps1

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AURORA Sentinel - Starting All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Helper: write a temp .ps1 and open it in a new window
function Start-Window {
    param([string]$Title, [string]$WorkDir, [string[]]$Lines)
    $tmp = [System.IO.Path]::GetTempFileName() + ".ps1"
    $Lines | Set-Content -Path $tmp -Encoding UTF8
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $tmp
    Write-Host "  [OK] $Title" -ForegroundColor Green
}

# ── 1. AI Intelligence Layer ──────────────────────────────────────────────────
Write-Host "Starting AI Intelligence Layer..." -ForegroundColor Yellow
$aiDir = Join-Path $Root "ai-intelligence-layer"

if (Test-Path (Join-Path $aiDir "venv_ai\Scripts\Activate.ps1")) {
    Start-Window -Title "AI Layer" -WorkDir $aiDir -Lines @(
        "Set-Location '$aiDir'",
        "& '.\venv_ai\Scripts\Activate.ps1'",
        "python server_local.py"
    )
} elseif (Test-Path (Join-Path $Root "venv\Scripts\Activate.ps1")) {
    Start-Window -Title "AI Layer" -WorkDir $aiDir -Lines @(
        "Set-Location '$aiDir'",
        "& '..\venv\Scripts\Activate.ps1'",
        "python server_local.py"
    )
} elseif (Test-Path (Join-Path $aiDir "node_modules")) {
    Start-Window -Title "AI Layer (Node)" -WorkDir $aiDir -Lines @(
        "Set-Location '$aiDir'",
        "npm start"
    )
} else {
    Write-Host "  [SKIP] AI layer not set up - run setup first" -ForegroundColor DarkYellow
}

Write-Host "  Waiting 5s for AI layer..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

# ── 2. Backend API ────────────────────────────────────────────────────────────
Write-Host "Starting Backend API..." -ForegroundColor Yellow

$venvPy = ""
if (Test-Path (Join-Path $Root "venv\Scripts\python.exe")) {
    $venvPy = Join-Path $Root "venv\Scripts\python.exe"
} elseif (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
} else {
    $venvPy = "python"
}

Start-Window -Title "Backend API" -WorkDir $Root -Lines @(
    "Set-Location '$Root'",
    "`$env:PYTHONPATH = '$Root'",
    "& '$venvPy' -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload"
)

# Wait for backend health
Write-Host "  Waiting for backend health check..." -ForegroundColor DarkGray
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Write-Host -NoNewline "."
}
Write-Host ""
if ($ready) {
    Write-Host "  [OK] Backend ready!" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Backend slow to start - check its window" -ForegroundColor DarkYellow
}

# ── 3. Frontend ───────────────────────────────────────────────────────────────
Write-Host "Starting Frontend..." -ForegroundColor Yellow
$feDir = Join-Path $Root "frontend"

if (-not (Test-Path (Join-Path $feDir "node_modules"))) {
    Write-Host "  Installing frontend deps (first run)..." -ForegroundColor DarkYellow
    Push-Location $feDir
    npm install
    Pop-Location
}

Start-Window -Title "Frontend" -WorkDir $feDir -Lines @(
    "Set-Location '$feDir'",
    "npm start"
)

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services launched!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  AI Layer:    http://localhost:3001/health" -ForegroundColor White
Write-Host ""
