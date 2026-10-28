@echo off
cd /d "%~dp0"
set "TEDUHLINK_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%TEDUHLINK_PY%" (
  "%TEDUHLINK_PY%" -m unittest -v test_backend.py
) else (
  py -3 -m unittest -v test_backend.py
)
pause
