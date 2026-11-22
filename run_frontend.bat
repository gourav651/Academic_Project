@echo off
title Frontend Server (Vite :5173)
cd /d "%~dp0frontend"
echo Starting Vite Frontend development server...
npm run dev
pause
