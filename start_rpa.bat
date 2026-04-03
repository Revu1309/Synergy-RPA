@echo off
echo 🚀 Starting RPA Framework with Dashboard...
echo 📊 Dashboard: http://localhost:5000
echo 🔄 Auto-syncing crypto data and weather data
echo 📈 All analytics dashboards available
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"

REM Use the new dashboard app with full features
.\venv\Scripts\python.exe -c "from dashboard.app_new import app; app.run(debug=False, host='0.0.0.0', port=5000)"

echo.
echo 🛑 RPA Framework stopped.
pause