@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" not found. Install Python 3.11+.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto :fail
)

".venv\Scripts\python.exe" -m pip install -r hyperhdr-receiver-requirements.txt || goto :fail

echo Receiver TCP : 0.0.0.0:32949
echo Browser      : http://127.0.0.1:8000/
echo HyperHDR target must be YOUR_PC_LAN_IP:32949, not 127.0.0.1.
start "" "http://127.0.0.1:8000/"
".venv\Scripts\python.exe" receive-hyperhdr-frames.py --tcp-port 32949 --web-port 8000 --preview-fps 10
goto :eof

:fail
echo Failed.
pause
exit /b 1
