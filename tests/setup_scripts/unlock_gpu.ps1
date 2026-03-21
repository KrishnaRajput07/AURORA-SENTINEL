# AURORA-SENTINEL: GPU Performance Unlocker
# This script installs CUDA-enabled PyTorch to leverage your RTX 4060.

Set-Location "$PSScriptRoot\..\.."
Write-Host "--- AURORA-SENTINEL: Hardware Unlocking Mode ---" -ForegroundColor Cyan
Write-Host "Target: RTX 4060 GPU + 16-Core Ryzen CPU" -ForegroundColor Gray

# 1. Ensure we are in the right directory
if (!(Test-Path "venv")) {
    Write-Error "Virtual environment 'venv' not found. Please run this from the project root."
    exit
}

# 2. Install CUDA-enabled PyTorch
Write-Host "`n[1/2] Installing CUDA-enabled PyTorch (cu121)..." -ForegroundColor Yellow
Write-Host "This is a large download (~2GB). Please wait." -ForegroundColor Gray
.\venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall

# 3. Verify CUDA
Write-Host "`n[2/2] Verifying CUDA Status..." -ForegroundColor Yellow
.\venv\Scripts\python -c "import torch; print('CUDA Available: ' + str(torch.cuda.is_available())); if torch.cuda.is_available(): print('Device: ' + torch.cuda.get_device_name(0))"

Write-Host "`n--- UNLOCK COMPLETE ---" -ForegroundColor Green
Write-Host "Your RTX 4060 is now ready to handle real-time forensic detection." -ForegroundColor Gray
