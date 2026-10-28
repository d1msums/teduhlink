@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run 1_SETUP.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" count_people.py --camera 0 --capacity 3 --upload
pause
