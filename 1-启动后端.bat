@echo off
title BiliAgent - Backend (port 8300)
cd /d "%~dp0"

echo.
echo ==========================================
echo    BiliAgent  Backend Service
echo    URL: http://127.0.0.1:8300
echo    API docs: http://127.0.0.1:8300/docs
echo ==========================================
echo.
echo Keep this window open.
echo To stop: press Ctrl+C or just close this window.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual env not found: .venv
    echo Run these in this folder first:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] .env not found
    echo Copy .env.example to .env and fill in your keys.
    echo.
    pause
    exit /b 1
)

.venv\Scripts\python.exe server_extended.py

echo.
echo Server stopped.
pause
