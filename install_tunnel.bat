@echo off
title Cloudflare Tunnel Installer
color 0A
cls
cd /d "%~dp0"

echo ===============================================================================
echo                Cloudflare Tunnel Service Auto-Installer
echo ===============================================================================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrator privileges are required!
    echo.
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"%~dp0\" && install_tunnel.bat' -Verb RunAs"
    exit /b
)

echo [1/2] Installing Cloudflare Windows Service...
echo -------------------------------------------------------------------------------
.\cloudflared.exe service install eyJhIjoiNWZlY2ViNjZlOTA1MmY0YTc1NjE5OTIzZmI5YmE2YTgiLCJ0IjoiMTFkYmE5NTEtMzYxZC00ZGZmLTg3YzItZDVlMmMzOTRhNzEyIiwicHNiIk5USTNZbVJpTWpndE9UYzJOUzAwTkdFeE5qQXdNRFF5TXpKbCJ9

if %errorLevel% neq 0 (
    echo.
    echo Retrying with normalized token syntax...
    .\cloudflared.exe service install eyJhIjoiNWZlY2ViNjZlOTA1MmY0YTc1NjE5OTIzZmI5YmE2YTgiLCJ0IjoiMTFkYmE5NTEtMzYxZC00ZGZmLTg3YzItZDVlMmMzOTRhNzEyIiwicyI6Ik5USTNZbVJpTWpndE9UYzJOUzAwTkdFeE5qQXdNRFF5TXpKbCJ9
)

echo.
echo [2/2] Starting Cloudflare Service...
echo -------------------------------------------------------------------------------
.\cloudflared.exe service start

echo.
echo ===============================================================================
echo  SUCCESS! Check your Cloudflare website dashboard - it should now show GREEN!
echo ===============================================================================
pause
