@echo off
cd /d "%~dp0"
set "TEDUHLINK_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist ".venv\Scripts\python.exe" goto install
if exist "%TEDUHLINK_PY%" (
  "%TEDUHLINK_PY%" -m venv .venv
) else (
  py -3 -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip freeze > installed-versions.txt
echo Setup finished. Run 2_START_CAMERA.cmd next.
pause
exit /b 0
:failed
echo Setup failed. Copy the last error message for troubleshooting.
pause
exit /b 1
