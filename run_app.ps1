# Little Millennium - Nest Daycare (Kharadi Branch)
# Enterprise ERP & CRM PowerShell Launcher

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "       LITTLE MILLENNIUM - NEST DAYCARE (KHARADI BRANCH)                       " -ForegroundColor Yellow
Write-Host "       Enterprise Preschool & Daycare ERP and CRM Web Application             " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

$pythonExec = "C:\Python312\python.exe"
if (-not (Test-Path $pythonExec)) {
    $pythonExec = "python"
}

Write-Host "`n[1/3] Verifying Python Environment..." -ForegroundColor Green
& $pythonExec --version

Write-Host "[2/3] Checking Database..." -ForegroundColor Green
& $pythonExec database.py

Write-Host "[3/3] Starting Web Server on http://127.0.0.1:5000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:5000"

& $pythonExec app.py
