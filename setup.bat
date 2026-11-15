@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo    TRUTH AI — Automated Windows Setup & Installation Script
echo    Verify. Analyze. Trust.
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python or py launcher
echo [*] Checking for Python installation...
set "PYTHON_EXE="

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py -3.12"
    %PYTHON_EXE% --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        set "PYTHON_EXE=py -3"
    )
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [!] ERROR: Python 3 was not detected on your system.
    echo [!] Please install Python 3.12 from https://www.python.org/downloads/
    echo [!] Ensure you check the box: "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Python detected: %PYTHON_EXE%
%PYTHON_EXE% --version

:: 2. Create Virtual Environment
echo.
echo [*] Checking virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment in .venv...
    %PYTHON_EXE% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [!] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Virtual environment created successfully.
) else (
    echo [*] Existing virtual environment detected.
)

:: 3. Create required directories
echo.
echo [*] Creating upload and storage directories...
if not exist "uploads\images" mkdir "uploads\images"
if not exist "uploads\videos\frames" mkdir "uploads\videos\frames"
if not exist "uploads\ela" mkdir "uploads\ela"
if not exist "database" mkdir "database"

:: 4. Environment configuration
echo.
echo [*] Checking environment file (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [*] Copied .env.example to .env
    )
) else (
    echo [*] .env file present.
)

:: 5. Install dependencies
echo.
echo [*] Installing required dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Some packages had installation warnings. Retrying core dependencies...
    .venv\Scripts\python.exe -m pip install flask "flask-sqlalchemy<3.1" "sqlalchemy<2.0" flask-login flask-cors pillow opencv-python-headless requests beautifulsoup4 pytest
)

:: 6. Initialize database and seed demo data
echo.
echo [*] Initializing database and demo data...
.venv\Scripts\python.exe seed_db.py
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Seed script encountered an issue. Initializing database schema directly...
    .venv\Scripts\python.exe -c "from app import create_app; from database import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database tables ready.')"
)

echo.
echo =====================================================================
echo    TRUTH AI Setup Complete!
echo    You can now run start.bat to launch the application.
echo =====================================================================
echo.
pause
