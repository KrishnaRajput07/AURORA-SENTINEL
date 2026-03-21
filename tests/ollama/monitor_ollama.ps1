# Monitor Ollama Download Progress
Set-Location "$PSScriptRoot\..\.."
Write-Host "Monitoring Ollama llava model download..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring`n" -ForegroundColor Yellow

while ($true) {
    Clear-Host
    Write-Host "=== Ollama Model Download Status ===" -ForegroundColor Green
    Write-Host ""
    
    # Check if model is installed
    $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
    $models = ollama list
    
    if ($models -match "llava") {
        Write-Host "✅ llava model is INSTALLED!" -ForegroundColor Green
        Write-Host ""
        ollama list
        Write-Host ""
        Write-Host "Download complete! You can now use Ollama for AI vision analysis." -ForegroundColor Green
        break
    } else {
        Write-Host "⏳ Download in progress..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Current models:" -ForegroundColor Cyan
        ollama list
        Write-Host ""
        Write-Host "Checking again in 30 seconds..." -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 30
}

Write-Host ""
Write-Host "Monitoring complete!" -ForegroundColor Green
