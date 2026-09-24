@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Starting SupportHub AI Platform (Full Docker Stack)
echo ==========================================================
echo.
echo Starting Database (PostgreSQL), Backend (FastAPI), and Frontend (Angular)...
echo.

docker compose up -d

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start Docker Compose containers.
    echo Please make sure Docker Desktop is running.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Containers launched successfully!
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul

echo.
echo ==========================================================
echo   Services are running:
echo   - Web Application:       http://localhost:3000
echo   - Ticket Status Tracker: http://localhost:3000/ticket-status
echo   - Swagger API Docs:      http://localhost:8000/docs
echo   - Backend Health Check:  http://localhost:8000/health
echo   - PostgreSQL Database:   localhost:5432
echo.
echo   Default Test Users (Password: password123):
echo   - User/Customer:  venu@company.com / kasi@company.com
echo   - Support Agent:  eegan@company.com / hari@company.com
echo   - Manager:        mathan@company.com
echo   - Administrator:  adhi@company.com / giri@company.com
echo ==========================================================
echo.
pause

