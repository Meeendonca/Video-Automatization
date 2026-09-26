@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute setup.ps1 primeiro. Consulte README.md.
  exit /b 1
)
".venv\Scripts\python.exe" -X utf8 studio.py %*
