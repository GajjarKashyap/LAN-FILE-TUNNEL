@echo off
title LAN Launcher
color 0b

rem Kill OLD instances only
taskkill /F /FI "WINDOWTITLE eq LAN File Share Server" >nul 2>&1

:start_server
cls
title LAN File Share Server
echo.   
echo 888             d8888 888b    888        8888888888 8888888 888      888888888888888     88888888888 888     888 888b    888 888b    888 8888888888 888      
echo 888           d88P888 88888b  888        888          888   888      888                     888     888     888 88888b  888 88888b  888 888        888      
echo 888          d88P 888 888Y88b 888        8888888      888   888      888                     888     888     888 888Y88b 888 888Y88b 888 8888888    888      
echo 888         d88P  888 888 Y88b888        888          888   888      88888888888             888     888     888 888 Y88b888 888 Y88b888 888        888      
echo 888        d88P   888 888  Y88888 888888 888          888   888      888            888888   888     888     888 888  Y88888 888  Y88888 888        888      
echo 888       d8888888888 888   Y8888        888          888   888      888                     888     Y88b. .d88P 888   Y8888 888   Y8888 888        888      
echo 88888888 d88P     888 888    Y888        888        8888888 88888888 888888888888888         888      "Y88888P"  888    Y888 888    Y888 8888888888 88888888 

echo.
echo                                      [ DEVELOPED BY GAJJARKASHAYAP ]
echo.
echo -----------------------------------------------------------------------------------------------
echo [SYSTEM] STARTING FILE TUNNEL...
echo [SYSTEM] CLOSING BROWSERS (Skipped for safety)...
rem Browsers will not be closed.
echo -----------------------------------------------------------------------------------------------

rem Check if flask is installed, if not, install dependencies
python -c "import flask" 2>NUL
if %errorlevel% neq 0 (
    echo [SYSTEM] Installing Dependencies...
    pip install flask flask-socketio user-agents qrcode pillow
)

echo [1/2] Launching Python Server...
python app.py

if %errorlevel%==5 (
    echo.
    echo [SYSTEM] RESTARTING SERVER...
    timeout /t 2 >nul
    goto start_server
)

echo.
echo [SERVER STOPPED]
pause
