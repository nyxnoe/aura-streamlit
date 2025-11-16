@echo off
echo Starting AURA Web Frontend Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found.
    echo Please make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Install/update requirements
echo Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found.
    echo Creating template .env file...
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here > .env
    echo SUPABASE_URL=your_supabase_url_here >> .env
    echo SUPABASE_KEY=your_supabase_key_here >> .env
    echo.
    echo Please edit the .env file with your actual API keys.
    echo Press any key to continue anyway...
    pause
)

echo.
echo Starting AURA API Server on http://localhost:5000
echo Close this window to stop the server.
echo.
echo To use the frontend:
echo 1. Open index.html in your web browser
echo 2. Start chatting with AURA!
echo.

REM Start the server
python api_server.py
