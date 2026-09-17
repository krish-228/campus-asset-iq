@echo off
title CampusAssetIQ - Physical Campus Server
color 0B
cls
cd /d "%~dp0"

echo ===============================================================================
echo                CampusAssetIQ - Physical Campus Server
echo                Academic ^& Hospital Hardware Asset Tracking System
echo ===============================================================================
echo.
echo [1/3] Detecting Server Local IP Address...
echo -------------------------------------------------------------------------------
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "0.0.0.0.*0.0.0.0"') do (
    set SERVER_IP=%%a
)
if "%SERVER_IP%"=="" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
        set SERVER_IP=%%a
    )
)
echo Server IP Detected: %SERVER_IP%
echo.
echo [2/3] Access URLs on Campus Network (Wi-Fi / LAN):
echo -------------------------------------------------------------------------------
echo   * Your Laptop Link:  http://127.0.0.1:8000/   or   http://localhost:8000/
echo   * Friend's Wi-Fi Link: http://%SERVER_IP%:8000/
echo   * Admin Sign In:     http://%SERVER_IP%:8000/admin-login/
echo   * Staff Portal:      http://%SERVER_IP%:8000/portal/login/
echo.
echo   -------------------------------------------------------------------------------
echo   [!] IMPORTANT:
echo   1. Make sure to use HTTP (not HTTPS). Do NOT put 's' in http://
echo   2. If your browser auto-adds 'https://', open an Incognito Tab (Ctrl+Shift+N)
echo   -------------------------------------------------------------------------------
echo.
echo [3/3] Opening site in your browser and starting server...
echo       (Press Ctrl + C in this window to stop the server)
echo ===============================================================================
echo.

:: Automatically open website in default browser
start "" "http://127.0.0.1:8000/"

if exist ".\venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
) else (
    python manage.py runserver 0.0.0.0:8000
)
pause
