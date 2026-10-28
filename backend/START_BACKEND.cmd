@echo off
cd /d "%~dp0"
set "TEDUHLINK_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%TEDUHLINK_PY%" (
  "%TEDUHLINK_PY%" server.py --host 0.0.0.0 --port 8000
) else (
  py -3 server.py --host 0.0.0.0 --port 8000
)
pause
