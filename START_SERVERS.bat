@echo off
title MAARS Lens - Unified Dev Server Launcher
color 0b

echo ======================================================================
echo           MAARS Lens: Legal Metrology Digital Verification System
echo ======================================================================
echo.

:: Detect Local IPv4 Address
for /f "tokens=4" %%a in ('route print 0.0.0.0 2^>nul ^| findstr 0.0.0.0 ^| findstr /v "Default" ^| findstr /v "Persistent"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
if "%LOCAL_IP%"=="" set LOCAL_IP=192.168.1.40

echo [*] Local Machine IP: %LOCAL_IP%
echo [*] Mobile / LAN Access URL: http://%LOCAL_IP%:5173
echo [*] Desktop Browser URL:    http://localhost:5173
echo [*] Backend API URL:        http://localhost:8001
echo.
echo ----------------------------------------------------------------------
echo Starting FastAPI Backend Server (0.0.0.0:8001)...
start "MAARS Lens - Backend Server (Port 8001)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo Starting Vite Frontend Server (0.0.0.0:5173)...
start "MAARS Lens - Frontend Server (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ======================================================================
echo  Both Servers are now running!
echo  - Press Ctrl+C in either server terminal window to stop it.
echo  - You can close this launcher window at any time.
echo ======================================================================
echo.
pause
