@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-build.txt
".venv\Scripts\pyinstaller.exe" --noconfirm --name Foto-Studio --add-data "index.html;." --add-data "manifest.json;." --add-data "sw.js;." --add-data "icons;icons" app.py
echo.
echo Gotowe: dist\Foto-Studio\Foto-Studio.exe
