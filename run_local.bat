@echo off
echo ====================================================================
echo   Starting Virtual CANoe Simulator Platform
echo ====================================================================

echo [1/3] Setting up Python virtual environment...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate
echo Installing backend requirements...
pip install -r requirements.txt
cd ..

echo [2/3] Setting up Node.js frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies (this may take a moment)...
    call npm install
)
cd ..

echo [3/3] Running servers concurrently...
echo Starting backend on http://localhost:8000
start "Canoe Backend Server" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting frontend on http://localhost:3000
start "Canoe Frontend Dev Server" cmd /k "cd frontend && npm run dev"

echo ====================================================================
echo   Startup Complete!
echo   - Backend API: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3000
echo ====================================================================
pause
