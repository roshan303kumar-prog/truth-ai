@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo    TRUTH AI — Production-Grade Fake News & Media Verification Engine
echo    Verify. Analyze. Trust.
echo =====================================================================
echo.

cd /d "%~dp0"

:: Check if virtual environment exists; if not, invoke setup
if not exist ".venv\Scripts\python.exe" (
    echo [*] Virtual environment not found. Running automated setup first...
    call setup.bat
    if not exist ".venv\Scripts\python.exe" (
        echo [!] Setup failed. Cannot proceed with startup.
        pause
        exit /b 1
    )
)

:: Ensure upload directories exist
if not exist "uploads\images" mkdir "uploads\images"
if not exist "uploads\videos\frames" mkdir "uploads\videos\frames"
if not exist "uploads\ela" mkdir "uploads\ela"
if not exist "database" mkdir "database"

:: Check database existence, seed if needed
if not exist "database\truth_ai.db" (
    echo [*] First-time database initialization...
    .venv\Scripts\python.exe seed_db.py
)

echo.
echo [*] Starting TRUTH AI Flask Server...
echo [*] Host: http://127.0.0.1:5000
echo [*] Press CTRL+C in this terminal window to stop the server.
echo.

:: Launch default web browser after 2 seconds in parallel
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000"

:: Start the application
.venv\Scripts\python.exe app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Server exited with an error code.
    pause
)
