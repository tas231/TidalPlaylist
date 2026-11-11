@echo off
rem ==============================================================================
rem TIDAL Playlist Manager - Windows Launcher Script
rem ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

rem Check for python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 was not found in your PATH.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check the box "Add Python to PATH" during installation.
    pause
    exit /b 1
)

rem Create .venv if missing
if not exist ".venv" (
    echo [SETUP] Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [SETUP] Installing dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

rem Launch the app
python main.py %*
pause
