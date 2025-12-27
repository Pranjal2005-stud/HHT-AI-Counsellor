@echo off
echo ========================================
echo AI Tech Counsellor Setup Script
echo ========================================

echo.
echo 1. Setting up Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo 2. Activating virtual environment...
call venv\Scripts\activate

echo.
echo 3. Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo 4. Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it to add your Gemini API key.
) else (
    echo .env file already exists.
)

echo.
echo 5. Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing Node.js dependencies...
    npm install
    if errorlevel 1 (
        echo Error: Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
) else (
    echo Node.js dependencies already installed.
)
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your Gemini API key (optional)
echo 2. Run start_servers.bat to start both backend and frontend
echo.
pause