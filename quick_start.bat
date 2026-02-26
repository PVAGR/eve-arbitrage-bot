@echo off
cls
echo.
echo ========================================
echo   EVE Personal Tracker - Quick Start
echo ========================================
echo.
echo Checking if config is set up...

if not exist config.yaml (
    echo Config file not found! Running setup wizard...
    echo.
    python setup_wizard.py
    if errorlevel 1 (
        echo Setup failed. Please check the error above.
        pause
        exit /b 1
    )
)

echo.
echo Starting EVE Personal Tracker...
echo Opening web dashboard at http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py web

pause
