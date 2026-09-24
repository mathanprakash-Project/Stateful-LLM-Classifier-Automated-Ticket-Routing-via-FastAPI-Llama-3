# PowerShell script to start the full SupportHub AI stack
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting SupportHub AI Platform (Full Docker Stack)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Database, Backend API, and Frontend..." -ForegroundColor Yellow

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to start Docker Compose containers." -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running." -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Containers launched successfully! Waiting 5s for initialization..." -ForegroundColor Green
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Services are running:" -ForegroundColor Green
Write-Host "  - Web Application:       http://localhost:3000" -ForegroundColor White
Write-Host "  - Ticket Status Tracker: http://localhost:3000/ticket-status" -ForegroundColor White
Write-Host "  - Swagger API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Backend Health Check:  http://localhost:8000/health" -ForegroundColor White
Write-Host "  - PostgreSQL Database:   localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "  Default Test Users (Password: password123):" -ForegroundColor Yellow
Write-Host "  - User/Customer:  venu@company.com / kasi@company.com"
Write-Host "  - Support Agent:  eegan@company.com / hari@company.com"
Write-Host "  - Manager:        mathan@company.com"
Write-Host "  - Administrator:  adhi@company.com / giri@company.com"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host -Prompt "Press Enter to close this window"

