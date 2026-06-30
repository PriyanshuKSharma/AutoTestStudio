@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo  ================================================================
echo   AutoTest Studio ^| Windows Installer Build
echo  ================================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo          Install Python 3.10+ from https://python.org
    echo          and make sure to tick "Add Python to PATH".
    echo.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [1/6] %PY_VER% found.

:: ── 2. Virtual environment ───────────────────────────────────────────
if not exist .venv (
    echo  [2/6] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 ( echo  [ERROR] venv creation failed. & pause & exit /b 1 )
) else (
    echo  [2/6] Virtual environment already exists — skipping.
)
call .venv\Scripts\activate.bat

:: ── 3. Install dependencies ──────────────────────────────────────────
echo  [3/6] Installing / updating dependencies...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause & exit /b 1
)
echo         Done.

:: ── 4. Clean previous build ──────────────────────────────────────────
echo  [4/6] Cleaning previous build output...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
if exist AutoTestStudio_Setup*.exe del /q AutoTestStudio_Setup*.exe

:: ── 5. PyInstaller — bundle Python app into .exe folder ──────────────
echo  [5/6] Bundling with PyInstaller...
echo.
pyinstaller AutoTestStudio.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo  [ERROR] PyInstaller failed. See output above.
    pause & exit /b 1
)
echo.
echo         Bundled to: dist\AutoTestStudio\AutoTestStudio.exe

:: ── 6. NSIS — wrap into a single installer exe ───────────────────────
echo  [6/6] Building installer with NSIS...
echo.

:: Look for NSIS in standard install locations
set NSIS=""
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set NSIS="C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe"       set NSIS="C:\Program Files\NSIS\makensis.exe"

:: Also check if makensis is on PATH
where makensis >nul 2>&1
if not errorlevel 1 set NSIS=makensis

if %NSIS%=="" (
    echo  [SKIP] NSIS not found — skipping installer creation.
    echo.
    echo         To create a proper installer:
    echo           1. Download NSIS from https://nsis.sourceforge.io
    echo           2. Install it
    echo           3. Re-run this build.bat
    echo.
    echo         The raw application is ready at:
    echo           dist\AutoTestStudio\AutoTestStudio.exe
    goto :done_no_nsis
)

%NSIS% /V2 installer\AutoTestStudio.nsi
if errorlevel 1 (
    echo.
    echo  [ERROR] NSIS failed. See output above.
    pause & exit /b 1
)

:: ── Done ──────────────────────────────────────────────────────────────
echo.
echo  ================================================================
echo   BUILD COMPLETE
echo  ================================================================
echo.
echo   Installer : AutoTestStudio_Setup_v1.1.0.exe
echo   Raw app   : dist\AutoTestStudio\AutoTestStudio.exe
echo.
echo   The installer is a single .exe file.
echo   Double-click it on any Windows machine to install.
echo   No Python required on the target machine.
echo.
pause
exit /b 0

:done_no_nsis
echo  ================================================================
echo   BUILD COMPLETE  (no installer — NSIS not installed)
echo  ================================================================
echo.
echo   Raw app : dist\AutoTestStudio\AutoTestStudio.exe
echo.
pause
exit /b 0
