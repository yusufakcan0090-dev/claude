@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Once KUR.bat dosyasini calistir.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "app\main.py"
