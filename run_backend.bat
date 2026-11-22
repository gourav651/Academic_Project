@echo off
title Backend Server (FastAPI :8000)
cd /d "%~dp0backend"
echo Activating virtual environment and starting FastAPI backend...
call .\venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
pause
