# Setup AI Intelligence Layer with Local Models
# This script sets up the Python-based AI layer with HuggingFace Transformers

Set-Location "$PSScriptRoot\..\.."
Write-Host "Setting up AI Intelligence Layer (Local Models)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Python not found. Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pythonVersion = & python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Navigate to AI layer directory
cd ai-intelligence-layer

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv_ai")) {
    Write-Host ""
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv_ai
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv_ai\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes on first install" -ForegroundColor Yellow
Write-Host "(PyTorch and Transformers are large packages)" -ForegroundColor Yellow
Write-Host ""

pip install --upgrade pip
pip install -r ../requirements/ai-intelligence.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Test the AI layer
Write-Host ""
Write-Host "Testing AI layer..." -ForegroundColor Yellow
python aiRouter_local.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "AI layer test passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "AI layer test had issues, but may still work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the AI layer:" -ForegroundColor Cyan
Write-Host "  cd ai-intelligence-layer" -ForegroundColor White
Write-Host "  .\venv_ai\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python server_local.py" -ForegroundColor White
Write-Host ""
Write-Host "Or use the updated start.ps1 script to start all services" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Models will download automatically on first use (2-3 GB)" -ForegroundColor Yellow
Write-Host "They are cached in: %USERPROFILE%\.cache\huggingface\" -ForegroundColor Yellow

cd ..
