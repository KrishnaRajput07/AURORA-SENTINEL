# Move entire project to D: drive
Set-Location "$PSScriptRoot\..\.."
Write-Host "=== Moving Project to D: Drive ===" -ForegroundColor Cyan

$currentPath = Get-Location
$projectName = Split-Path -Leaf $currentPath
$newPath = "D:\Projects\$projectName"

Write-Host "Current location: $currentPath" -ForegroundColor Yellow
Write-Host "New location: $newPath" -ForegroundColor Green

# Create Projects directory on D: drive
Write-Host "`nCreating D:\Projects directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "D:\Projects" -Force | Out-Null

# Check if destination already exists
if (Test-Path $newPath) {
    Write-Host "`nWarning: $newPath already exists!" -ForegroundColor Red
    $response = Read-Host "Do you want to overwrite? (yes/no)"
    if ($response -ne "yes") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit
    }
}

# Copy entire project
Write-Host "`nCopying project files to D: drive..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

Copy-Item -Path $currentPath -Destination "D:\Projects\" -Recurse -Force

Write-Host "`n✅ Project copied successfully!" -ForegroundColor Green
Write-Host "`nNew project location: $newPath" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. cd $newPath" -ForegroundColor White
Write-Host "2. Verify files are there: dir" -ForegroundColor White
Write-Host "3. Continue working from D: drive" -ForegroundColor White
Write-Host "`nNote: You can delete the C: drive copy after verifying D: drive works" -ForegroundColor Gray
