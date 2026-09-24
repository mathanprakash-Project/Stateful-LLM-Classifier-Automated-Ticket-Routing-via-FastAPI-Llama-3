# PowerShell script to stop the full SupportHub AI stack
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Stopping SupportHub AI Platform..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

docker compose down

Write-Host ""
Write-Host "All containers stopped successfully." -ForegroundColor Green
Read-Host -Prompt "Press Enter to exit"

