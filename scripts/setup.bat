@echo off
REM ========================================
REM Setup Script for D&D Combat Simulator
REM ========================================

echo.
echo ========================================
echo   D&D 5e Combat Simulator Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found, installing minimal dependencies...
    pip install Flask==3.0.0 Werkzeug==3.0.1 pytest==7.4.3
)

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file...
    (
        echo # Flask Configuration
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-in-production-%RANDOM%%RANDOM%
        echo FLASK_HOST=127.0.0.1
        echo FLASK_PORT=5000
    ) > .env
    echo [OK] .env file created
) else (
    echo [OK] .env file already exists
)

REM Check templates directory
if not exist "templates" (
    echo.
    echo [WARNING] templates directory not found, creating it...
    mkdir templates
    echo [OK] templates directory created
    echo [!] Please move index.html to the templates directory
) else (
    echo [OK] templates directory exists
)

REM Check if index.html exists in templates
if not exist "templates\index.html" (
    echo.
    echo [WARNING] index.html not found in templates directory
    if exist "index.html" (
        echo Moving index.html to templates...
        move index.html templates\
        echo [OK] index.html moved to templates
    ) else (
        echo [!] Please ensure index.html is in the templates directory
    )
) else (
    echo [OK] index.html found in templates
)

REM Create necessary directories
if not exist "custom_chars" mkdir custom_chars

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Run: run.bat
echo   2. Or manually: venv\Scripts\activate.bat
echo                   python app.py
echo.
echo The app will be available at: http://127.0.0.1:5000
echo.
pause
