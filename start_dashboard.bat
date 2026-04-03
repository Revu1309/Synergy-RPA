@echo off
REM Start RPA Framework with Authentication and Advanced Dashboards
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  RPA Framework - Intelligent Monitoring
echo ==========================================
echo.
echo Starting Flask application with:
echo  - Authentication System (Login: admin/admin)
echo  - Standard Dashboard
echo  - Advanced Dashboard with Market Insights
echo  - Real-time Data Synchronization
echo.
echo Accessing at: http://localhost:5000
echo.

REM Run the new Flask app
python dashboard/app_new.py

pause
