@echo off
echo ========================================
echo    AURA - Intelligent Research Assistant
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "C:\Users\nihal\OneDrive\Desktop\aura-streamlit\backend\api_server.py" (
    echo ERROR: backend\api_server.py not found.
    echo Please make sure you're in the correct directory.
    echo.
    pause
    exit /b 1
)

if not exist "C:\Users\nihal\OneDrive\Desktop\aura-streamlit\frontend\index.html" (
    echo ERROR: frontend\index.html not found.
    echo Please make sure you're in the correct directory.
    echo.
    pause
    exit /b 1
)

REM Install/update requirements
echo Installing/updating dependencies...
pip install streamlit flask flask-cors openai reportlab supabase python-dotenv >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not install dependencies automatically.
    echo Please run: pip install streamlit flask flask-cors openai reportlab supabase python-dotenv
    echo.
)

REM Check for .env file
if not exist "C:\Users\nihal\OneDrive\Desktop\aura-streamlit\config\.env" (
    echo Creating template .env file...
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here > config\.env
    echo SUPABASE_URL=your_supabase_url_here >> config\.env
    echo SUPABASE_KEY=your_supabase_key_here >> config\.env
    echo.
    echo IMPORTANT: Please edit the config\.env file with your actual API keys!
    echo The application will still work but AI features will be limited.
    echo.
    timeout /t 5 >nul
)

echo Starting AURA Backend Server...
echo.
echo Server will be available at: http://localhost:5000
echo.
echo Opening AURA Frontend in your browser...
echo.
echo ========================================
echo    INSTRUCTIONS:
echo ========================================
echo 1. Backend server is starting...
echo 2. Frontend will open automatically
echo 3. Start chatting with AURA!
echo.
echo To stop: Close this command window
echo ========================================
echo.

REM Start the server in background and open frontend
start /B python backend\api_server.py
timeout /t 3 >nul
start frontend\index.html

echo AURA is now running!
echo.
echo If the browser doesn't open automatically:
echo - Open frontend\index.html manually in your browser
echo.
pause
