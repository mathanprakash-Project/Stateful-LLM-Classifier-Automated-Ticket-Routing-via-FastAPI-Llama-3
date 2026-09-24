@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Stopping SupportHub AI Platform...
echo ==========================================================
echo.

docker compose down

echo.
echo All containers stopped successfully.
pause

