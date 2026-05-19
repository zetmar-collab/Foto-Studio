@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
set FOTO_STUDIO_NO_BROWSER=1
start "" http://localhost:3000
".venv\Scripts\python.exe" app.py
