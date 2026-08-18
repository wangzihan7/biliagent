@echo off
title BiliAgent - Frontend (port 5173)
cd /d "%~dp0frontend"

echo.
echo ==========================================
echo    BiliAgent  Frontend
echo    URL: http://127.0.0.1:5173
echo ==========================================
echo.
echo Keep this window open.
echo Then open http://127.0.0.1:5173 in your browser.
echo.

if not exist "package.json" (
    echo [ERROR] package.json not found in %CD%
    echo This bat file must stay in the project root folder.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [WARN] frontend\.env not found
    echo Copy frontend\.env.example to frontend\.env
    echo.
)

if not exist "node_modules" (
    echo [INFO] First run, installing dependencies...
    echo.
    call npm install --registry=https://registry.npmmirror.com
    echo.
)

call npm run dev

echo.
echo Server stopped.
pause
