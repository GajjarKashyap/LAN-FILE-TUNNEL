@echo off
title LAN File Share Server
echo ---------------------------------------------------
echo [SYSTEM] STARTING FILE TUNNEL (HTTP MODE)...
echo ---------------------------------------------------

taskkill /F /FI "WINDOWTITLE eq LAN File Share Server" >nul 2>&1

echo [1/3] Launching Python Server...
start "LAN File Share Server" python app.py

echo [2/3] Waiting for server to initialize...
timeout /t 2 >nul

echo [3/3] Opening Dashboard...
start http://localhost:5000

echo.
echo [SUCCESS] Server is running!
echo Scan the QR code or type the address.
echo.
pause
