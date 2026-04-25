@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  EchoMind ^— Starting System
echo ============================================
echo.

if not exist logs mkdir logs

echo [1/4] WhatsApp server  (port 8000) ...
start "WhatsApp Server" cmd /k "conda activate mp && cd /d "%~dp0backend" && python -m uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000"

echo [2/4] Manual API       (port 8001) ...
start "Manual API" cmd /k "conda activate mp && cd /d "%~dp0backend" && python -m uvicorn app.api.manual_receiver:app --host 127.0.0.1 --port 8001"

echo [3/4] Baileys (Node.js) ...
start "Baileys" cmd /k "cd /d "%~dp0api\whatsapp" && node index.js"

echo [4/4] Scheduler (Gmail + Calendar + Preprocessing) ...
start "EchoMind Scheduler" cmd /k "conda activate mp && cd /d "%~dp0" && python run_scheduler.py"

echo.
echo ============================================
echo  All 4 services started in separate windows.
echo.
echo  Logs:
echo    Scheduler    ^→  logs\scheduler.log
echo    Each service ^→  its own terminal window
echo ============================================
echo.
pause
