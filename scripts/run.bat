@echo off
REM ========================================
REM Run Script for D&D Combat Simulator
REM ========================================

echo.
echo ========================================
echo   Starting D&D 5e Combat Simulator
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if app.py exists
if not exist "app.py" (
    echo [ERROR] app.py not found!
    echo Please ensure all files are in the correct location
    pause
    exit /b 1
)

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development

REM Load .env file if it exists (manual parsing since Windows doesn't have source)
if exist ".env" (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
)

echo.
echo Starting Flask application...
echo Server will be available at: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python app.py

pause
