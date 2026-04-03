@echo off
REM Quick Start Guide for RPA Framework
REM This script displays important information about the system

cls
echo.
echo ======================================================================================================
echo  RPA FRAMEWORK - INTELLIGENT MONITORING AND ALERTING SYSTEM
echo ======================================================================================================
echo.
echo  PROJECT: An Intelligent RPA Framework for Real-Time Data Monitoring and Alerting
echo.
echo ======================================================================================================
echo  QUICK START
echo ======================================================================================================
echo.
echo  1. START THE APPLICATION:
echo     - Run: start_dashboard.bat
echo     - Or:  python dashboard/app_new.py
echo.
echo  2. OPEN IN BROWSER:
echo     - Navigate to: http://localhost:5000
echo.
echo  3. LOGIN CREDENTIALS:
echo     - Username: admin
echo     - Password: admin
echo.
echo ======================================================================================================
echo  SYSTEM FEATURES
echo ======================================================================================================
echo.
echo  ✓ Beautiful Login Page with Project Branding
echo  ✓ Secure Session Management (24-hour expiration)
echo  ✓ Standard Dashboard with Real-Time Analytics
echo  ✓ Advanced Dashboard with Market Insights
echo  ✓ On-Demand Data Synchronization
echo  ✓ Interactive Charts and Visualizations
echo  ✓ Intelligent Alert System
echo  ✓ 500+ Records of Sample Cryptocurrency Data
echo.
echo ======================================================================================================
echo  PAGES AVAILABLE
echo ======================================================================================================
echo.
echo  1. LOGIN PAGE
echo     - Modern aesthetic design with project name
echo     - Secure authentication
echo     - Demo credentials display
echo.
echo  2. MENU PAGE
echo     - Dashboard navigation hub
echo     - Links to Standard and Advanced Dashboards
echo     - Manual data sync button
echo     - User logout
echo.
echo  3. STANDARD DASHBOARD
echo     - Real-time cryptocurrency metrics
echo     - Price trend charts
echo     - Alert system
echo     - Auto-refresh every 5 minutes
echo.
echo  4. ADVANCED DASHBOARD
echo     - Deep market analytics
echo     - Top performer identification
echo     - Market cap distribution
echo     - Dark theme with glassmorphism
echo     - Auto-refresh every 10 minutes
echo.
echo ======================================================================================================
echo  REQUIREMENTS
echo ======================================================================================================
echo.
echo  Database: MySQL running locally
echo  Python:   3.8 or higher
echo  Virtual:  .venv environment with dependencies installed
echo.
echo  All dependencies are in: requirements.txt
echo.
echo ======================================================================================================
echo  CONFIGURATION
echo ======================================================================================================
echo.
echo  Database Settings:  config/config.py
echo  Environment:        .env file
echo  Logging:            logs/ directory
echo.
echo ======================================================================================================
echo  TROUBLESHOOTING
echo ======================================================================================================
echo.
echo  Issue: "Module not found" errors
echo  Fix:   pip install -r requirements.txt
echo.
echo  Issue: "Port 5000 already in use"
echo  Fix:   Change port in app_new.py or kill process on port 5000
echo.
echo  Issue: "Database connection error"
echo  Fix:   Check credentials in .env and ensure MySQL is running
echo.
echo ======================================================================================================
echo.
echo  Ready to start? Execute: start_dashboard.bat
echo.
pause
