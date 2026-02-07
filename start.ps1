# Wrapper to start Aurora Sentinel from root
Write-Host "Redirecting to AURORA-SENTINEL startup script..." -ForegroundColor Cyan
& "$PSScriptRoot\AURORA-SENTINEL\start.ps1" @args
