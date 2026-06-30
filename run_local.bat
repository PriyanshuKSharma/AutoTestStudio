@echo off
setlocal

cd /d "%~dp0"

echo ================================================================
echo   AutoTest Studio — Run from source
echo ================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause & exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing / verifying dependencies...
python -m pip install -q -r requirements.txt

echo Starting AutoTest Studio...
python app.py

pause
