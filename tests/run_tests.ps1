#!/usr/bin/env pwsh
# AURORA-SENTINEL Test Runner
# Professional test execution with reporting

Set-Location "$PSScriptRoot\..\.."
param(
    [string]$Category = "all",  # all, ml, vlm, api, fast, synthetic
    [switch]$Coverage,
    [switch]$Verbose
)

Write-Host "🧪 AURORA-SENTINEL Test Suite" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if pytest is installed
try {
    python -m pytest --version | Out-Null
} catch {
    Write-Host "❌ pytest not found. Installing..." -ForegroundColor Red
    pip install pytest httpx
}

# Build test command
$testCmd = "python -m pytest"
$testArgs = @()

# Select test category
switch ($Category) {
    "ml" {
        Write-Host "📊 Running ML Layer Tests..." -ForegroundColor Yellow
        $testArgs += "tests/test_ml_smoke.py"
    }
    "vlm" {
        Write-Host "🧠 Running VLM Service Tests..." -ForegroundColor Yellow
        $testArgs += "tests/test_vlm_service.py"
    }
    "api" {
        Write-Host "🌐 Running API Tests..." -ForegroundColor Yellow
        $testArgs += "tests/test_api_video_upload.py", "tests/test_api_search.py"
    }
    "fast" {
        Write-Host "⚡ Running Fast Tests (no video processing)..." -ForegroundColor Yellow
        $testArgs += "tests/test_ml_smoke.py", "tests/test_vlm_service.py"
    }
    "synthetic" {
        Write-Host "🎬 Generating Synthetic Test Data..." -ForegroundColor Yellow
        python tests/synthetic_data/video_generator.py
        exit 0
    }
    default {
        Write-Host "🔍 Running All Tests..." -ForegroundColor Yellow
        $testArgs += "tests/"
    }
}

# Add verbose flag
if ($Verbose) {
    $testArgs += "-v"
} else {
    $testArgs += "-v"  # Always verbose for better output
}

# Add coverage
if ($Coverage) {
    Write-Host "📈 Coverage analysis enabled" -ForegroundColor Green
    $testArgs += "--cov=backend", "--cov=models", "--cov-report=html", "--cov-report=term"
}

# Add color and summary
$testArgs += "--color=yes", "-ra"

Write-Host ""
Write-Host "Command: $testCmd $($testArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run tests
$startTime = Get-Date
& $testCmd @testArgs
$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "⏱️  Duration: $([math]::Round($duration, 2))s" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed (exit code: $exitCode)" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "  - Run specific category: .\run_tests.ps1 -Category ml" -ForegroundColor Gray
Write-Host "  - Generate test data: .\run_tests.ps1 -Category synthetic" -ForegroundColor Gray
Write-Host "  - Enable coverage: .\run_tests.ps1 -Coverage" -ForegroundColor Gray
Write-Host ""

exit $exitCode
