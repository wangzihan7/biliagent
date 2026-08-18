@echo off
setlocal enabledelayedexpansion
title BiliAgent - Environment Check
cd /d "%~dp0"

echo.
echo ============================================================
echo    BiliAgent  Environment Check
echo ============================================================
echo.

set NEED=0

REM ---------- 1. Python ----------
echo [1/6] Python  (need 3.9+, recommend 3.12)
where python >nul 2>&1
if errorlevel 1 (
    echo       NOT FOUND
    echo       -^> Install Python 3.12 from python.org
    echo          IMPORTANT: check "Add python.exe to PATH"
    set NEED=1
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    python -c "import sys;sys.exit(0 if sys.version_info>=(3,12) else (1 if sys.version_info>=(3,9) else 2))" >nul 2>&1
    if errorlevel 2 (
        echo       !PYVER!  -^> TOO OLD
        echo       -^> Install Python 3.12. Old version can stay, they coexist.
        set NEED=1
    ) else (
        if errorlevel 1 (
            echo       !PYVER!  -^> OK  ^(3.12 recommended^)
        ) else (
            echo       !PYVER!  -^> OK
        )
    )
)
echo.

REM ---------- 2. Node.js ----------
echo [2/6] Node.js  (need 18+)
where node >nul 2>&1
if errorlevel 1 (
    echo       NOT FOUND  -^> Install Node.js LTS from nodejs.org
    set NEED=1
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo       !NODEVER!  -^> OK
)
echo.

REM ---------- 3. MySQL ----------
echo [3/6] MySQL service
sc query MySQL80 >nul 2>&1
if errorlevel 1 (
    echo       Service MySQL80 NOT FOUND
    echo       -^> Install MySQL 8.0 from dev.mysql.com
    set NEED=1
) else (
    sc query MySQL80 | find "RUNNING" >nul 2>&1
    if errorlevel 1 (
        echo       Installed but NOT RUNNING
        echo       -^> Win+R, services.msc, find MySQL80, right-click Start
        set NEED=1
    ) else (
        echo       RUNNING  -^> OK
    )
)
echo.

REM ---------- 4. .env ----------
echo [4/6] Config files
if not exist ".env" (
    echo       .env  NOT FOUND
    echo       -^> Copy .env.example to .env, then fill in
    echo          SILICON_API_KEY and MYSQL_PASSWORD
    set NEED=1
) else (
    REM Accept: KEY=sk-xxx or KEY='sk-xxx' or KEY="sk-xxx"
    findstr /R /C:"^SILICON_API_KEY=.*sk-" ".env" >nul 2>&1
    if errorlevel 1 (
        echo       .env  exists, but SILICON_API_KEY not filled
        echo       -^> Get a free key at https://cloud.siliconflow.cn/
        set NEED=1
    ) else (
        echo       .env  OK
    )
    findstr /R /C:"^sessdata=..*" ".env" >nul 2>&1
    if errorlevel 1 (
        echo       .env  bilibili cookie not set  ^(optional^)
        echo          Without it you can search videos but CANNOT fetch comments.
        echo          See install guide section 5.2
    ) else (
        echo       .env  bilibili cookie  OK
    )
)
if not exist "frontend\.env" (
    echo       frontend\.env  NOT FOUND
    echo       -^> Copy frontend\.env.example to frontend\.env
    set NEED=1
) else (
    echo       frontend\.env  OK
)
echo.

REM ---------- 5. Dependencies ----------
echo [5/6] Dependencies
if not exist ".venv\Scripts\python.exe" (
    echo       Backend   NOT INSTALLED
    echo       -^> python -m venv .venv
    echo          .venv\Scripts\python.exe -m pip install -r requirements.txt
    set NEED=1
) else (
    REM Not enough to check the file exists - a venv copied from another
    REM machine has hardcoded paths inside and will fail to run.
    .venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo       Backend   BROKEN
        echo       -^> .venv exists but cannot run. It was probably copied
        echo          from another computer - paths inside are hardcoded.
        echo          Fix: rmdir /s /q .venv
        echo               python -m venv .venv
        echo               .venv\Scripts\python.exe -m pip install -r requirements.txt
        set NEED=1
    ) else (
        .venv\Scripts\python.exe -c "import fastapi,langchain,faiss" >nul 2>&1
        if errorlevel 1 (
            echo       Backend   venv OK but packages missing
            echo       -^> .venv\Scripts\python.exe -m pip install -r requirements.txt
            set NEED=1
        ) else (
            echo       Backend   OK
        )
    )
)
if not exist "frontend\node_modules" (
    echo       Frontend  NOT INSTALLED
    echo       -^> cd frontend
    echo          npm install
    set NEED=1
) else (
    echo       Frontend  OK
)
echo.

REM ---------- 6. Database tables ----------
echo [6/6] Database tables
if not exist ".venv\Scripts\python.exe" (
    echo       SKIPPED  ^(install backend deps first^)
) else (
    .venv\Scripts\python.exe -c "import sys;sys.path.insert(0,'.');from server.db.session import engine;from sqlalchemy import inspect;t=inspect(engine).get_table_names();print('      %d tables found'%len(t));sys.exit(0 if len(t)>=10 else 1)" 2>nul
    if errorlevel 1 (
        echo       Tables missing or cannot connect
        echo       -^> .venv\Scripts\python.exe init_db.py --init
        set NEED=1
    )
)
echo.

echo ============================================================
if "!NEED!"=="1" (
    echo    Some items need attention. See the -^> lines above.
    echo.
    echo    Full step-by-step guide: the install guide markdown
    echo    file in this folder.
) else (
    echo    All checks passed.
    echo.
    echo    Now double-click the two start scripts:
    echo      the one numbered 1  ^(backend,  port 8300^)
    echo      the one numbered 2  ^(frontend, port 5173^)
    echo.
    echo    Then open  http://127.0.0.1:5173
)
echo ============================================================
echo.
pause
