@echo off
echo Opening AURA Frontend in default browser...
echo.

REM Check if index.html exists
if not exist "index.html" (
    echo ERROR: index.html not found.
    echo Please make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Open the frontend in default browser
start index.html

echo Frontend opened successfully!
echo.
echo If the page doesn't load properly:
echo 1. Make sure the backend server is running (run start_server.bat first)
echo 2. Check that your browser allows local file access
echo 3. Try refreshing the page
echo.
pause
