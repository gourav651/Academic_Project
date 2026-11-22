@echo off
title Agentic AI Framework Launcher
echo ===================================================================
echo   Launching Agentic AI Framework (Backend + Frontend)
echo ===================================================================
echo.
start "Backend Server (FastAPI :8000)" cmd /k "cd /d %~dp0backend && call .\venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
start "Frontend Server (Vite :5173)" cmd /k "cd /d %~dp0frontend && npm run dev"
echo [SUCCESS] Both Backend (http://127.0.0.1:8000) and Frontend (http://localhost:5173) are running!
echo You can close this window now.
timeout /t 5 >nul
