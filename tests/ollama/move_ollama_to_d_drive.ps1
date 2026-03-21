# Move Ollama to D: Drive
Set-Location "$PSScriptRoot\..\.."
Write-Host "=== Moving Ollama to D: Drive ===" -ForegroundColor Cyan
Write-Host ""

# Stop Ollama service if running
Write-Host "1. Stopping Ollama service..." -ForegroundColor Yellow
Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✓ Ollama stopped (if it was running)" -ForegroundColor Green

# Create new Ollama directory on D: drive
$newOllamaPath = "D:\Ollama"
Write-Host ""
Write-Host "2. Creating Ollama directory on D: drive..." -ForegroundColor Yellow
if (-not (Test-Path $newOllamaPath)) {
    New-Item -ItemType Directory -Path $newOllamaPath -Force | Out-Null
    Write-Host "   ✓ Created: $newOllamaPath" -ForegroundColor Green
} else {
    Write-Host "   ℹ Directory already exists: $newOllamaPath" -ForegroundColor Gray
}

# Check if old Ollama data exists
$oldOllamaPath = "$env:USERPROFILE\.ollama"
Write-Host ""
Write-Host "3. Checking for existing Ollama data..." -ForegroundColor Yellow
if (Test-Path $oldOllamaPath) {
    $size = (Get-ChildItem $oldOllamaPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   ℹ Found existing data: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
    
    Write-Host "   Moving data to D: drive..." -ForegroundColor Yellow
    Copy-Item -Path "$oldOllamaPath\*" -Destination $newOllamaPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Data moved to D: drive" -ForegroundColor Green
} else {
    Write-Host "   ℹ No existing data found" -ForegroundColor Gray
}

# Set environment variable for Ollama
Write-Host ""
Write-Host "4. Setting OLLAMA_MODELS environment variable..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $newOllamaPath, [System.EnvironmentVariableTarget]::User)
$env:OLLAMA_MODELS = $newOllamaPath
Write-Host "   ✓ OLLAMA_MODELS = $newOllamaPath" -ForegroundColor Green

# Verify the setting
Write-Host ""
Write-Host "5. Verifying configuration..." -ForegroundColor Yellow
Write-Host "   Current session: $env:OLLAMA_MODELS" -ForegroundColor Gray
Write-Host "   User profile: $([System.Environment]::GetEnvironmentVariable('OLLAMA_MODELS', [System.EnvironmentVariableTarget]::User))" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Configuration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart Ollama service (it will use D: drive automatically)" -ForegroundColor White
Write-Host "2. Run: ollama pull llava" -ForegroundColor White
Write-Host ""
Write-Host "The model will now download to: $newOllamaPath" -ForegroundColor Yellow
Write-Host ""
