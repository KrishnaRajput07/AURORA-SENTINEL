# Aurora Sentinel - Quick Start with Health Checks
# This script performs pre-flight checks before starting the system

Write-Host "🔍 Aurora Sentinel - Pre-Flight Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allChecksPass = $true

# Check 1: Python Virtual Environment
Write-Host "Checking Python virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found. Run: python -m venv venv" -ForegroundColor Red
    $allChecksPass = $false
}

# Check 2: Python Dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
$pythonCheck = & ".\venv\Scripts\python.exe" -c "import torch, ultralytics, fastapi; print('OK')" 2>&1
if ($pythonCheck -like "*OK*") {
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Python dependencies missing. Run: pip install -r requirements/backend.txt" -ForegroundColor Red
    $allChecksPass = $false
}

# Check 3: AI Intelligence Layer Dependencies
Write-Host "Checking AI Intelligence Layer..." -ForegroundColor Yellow
if (Test-Path ".\ai-intelligence-layer\node_modules") {
    Write-Host "✅ AI layer dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  AI layer dependencies missing. Will install automatically..." -ForegroundColor Yellow
}

# Check 4: Frontend Dependencies
Write-Host "Checking Frontend dependencies..." -ForegroundColor Yellow
if (Test-Path ".\frontend\node_modules") {
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend dependencies missing. Will install automatically..." -ForegroundColor Yellow
}

# Check 5: Database Migration
Write-Host "Checking database migration..." -ForegroundColor Yellow
if (Test-Path ".\aurora.db") {
    Write-Host "✅ Database file exists" -ForegroundColor Green
    # Check if migration was applied
    $migrationCheck = & ".\venv\Scripts\python.exe" -c "import sqlite3; conn = sqlite3.connect('aurora.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(alerts)'); cols = [col[1] for col in cursor.fetchall()]; print('ml_score' in cols)" 2>&1
    if ($migrationCheck -like "*True*") {
        Write-Host "✅ Database migration applied" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database migration not applied. Run: python apply_migration.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Database will be created on first run" -ForegroundColor Yellow
}

# Check 6: Port Availability
Write-Host "Checking port availability..." -ForegroundColor Yellow
$ports = @(3000, 3001, 8000)
$portsInUse = @()
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($connection) {
        $portsInUse += $port
    }
}
if ($portsInUse.Count -eq 0) {
    Write-Host "✅ All required ports available (3000, 3001, 8000)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Ports in use: $($portsInUse -join ', '). Services may already be running." -ForegroundColor Yellow
}

# Check 7: CUDA Availability
Write-Host "Checking GPU availability..." -ForegroundColor Yellow
$cudaCheck = & ".\venv\Scripts\python.exe" -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>&1
if ($cudaCheck -like "*CUDA*") {
    Write-Host "✅ CUDA GPU detected - will use GPU acceleration" -ForegroundColor Green
} else {
    Write-Host "⚠️  No CUDA GPU detected - will use CPU (slower)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allChecksPass) {
    Write-Host "✅ All critical checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting Aurora Sentinel..." -ForegroundColor Cyan
    Write-Host ""
    
    # Run the main startup script
    & ".\start.ps1"
} else {
    Write-Host "❌ Some critical checks failed. Please fix the issues above before starting." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "1. Create virtual environment: python -m venv venv" -ForegroundColor White
    Write-Host "2. Activate virtual environment: .\venv\Scripts\activate" -ForegroundColor White
    Write-Host "3. Install Python dependencies: pip install -r requirements/backend.txt" -ForegroundColor White
    Write-Host "4. Install AI layer dependencies: cd ai-intelligence-layer; npm install" -ForegroundColor White
    Write-Host "5. Install frontend dependencies: cd frontend; npm install" -ForegroundColor White
    Write-Host "6. Apply database migration: python apply_migration.py" -ForegroundColor White
    Write-Host ""
    Write-Host "For more help, see TROUBLESHOOTING.md" -ForegroundColor Cyan
}
