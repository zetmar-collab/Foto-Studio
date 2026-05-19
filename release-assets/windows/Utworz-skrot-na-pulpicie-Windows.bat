@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Utworz-skrot-na-pulpicie-Windows.ps1"
pause
