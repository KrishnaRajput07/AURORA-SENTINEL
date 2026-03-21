# Move Ollama to D: Drive
Set-Location "$PSScriptRoot\..\.."
Write-Host "=== Moving Ollama to D: Drive ===" -ForegroundColor Cyan

# Stop Ollama
Write-Host "Stopping Ollama..." -ForegroundColor Yellow
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Create directory on D: drive
$newPath = "D:\Ollama"
Write-Host "Creating directory: $newPath" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $newPath -Force | Out-Null

# Copy existing data if any
$oldPath = "$env:USERPROFILE\.ollama"
if (Test-Path $oldPath) {
    Write-Host "Copying existing data..." -ForegroundColor Yellow
    Copy-Item -Path "$oldPath\*" -Destination $newPath -Recurse -Force -ErrorAction SilentlyContinue
}

# Set environment variable
Write-Host "Setting OLLAMA_MODELS environment variable..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $newPath, 'User')
$env:OLLAMA_MODELS = $newPath

Write-Host ""
Write-Host "Done! Ollama will now use D:\Ollama for models" -ForegroundColor Green
Write-Host "Environment variable set: OLLAMA_MODELS=$newPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Start Ollama and pull the model" -ForegroundColor Cyan
