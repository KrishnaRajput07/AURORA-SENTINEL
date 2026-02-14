# deploy.ps1 - Automated Deployment Script for Aurora Sentinel

Write-Host "Rocket Preparing Aurora Sentinel for Deployment..." -ForegroundColor Cyan

# 1. Build Frontend
Write-Host "Building Frontend Artifacts..." -ForegroundColor Yellow
Set-Location frontend
npm install
npm run build
Set-Location ..

# 2. Build Docker Image
Write-Host "Building Docker Container (Multi-stage)..." -ForegroundColor Yellow
docker build -t aurora-sentinel:latest .

Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "To run locally:" -ForegroundColor White
Write-Host "docker run -p 8000:8000 --gpus all aurora-sentinel:latest" -ForegroundColor Gray

Write-Host " "
Write-Host "To push to cloud (Example for Docker Hub):" -ForegroundColor White
Write-Host "docker tag aurora-sentinel:latest yourusername/aurora-sentinel:latest" -ForegroundColor Gray
Write-Host "docker push yourusername/aurora-sentinel:latest" -ForegroundColor Gray
