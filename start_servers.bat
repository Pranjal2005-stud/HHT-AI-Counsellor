@echo off
echo ========================================
echo Starting AI Tech Counsellor
echo ========================================

echo.
echo Starting backend server...
start "Backend Server" cmd /k "venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting frontend server...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Servers Starting!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause > nul