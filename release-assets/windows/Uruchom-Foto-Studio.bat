@echo off
setlocal
cd /d "%~dp0"
if exist "Foto-Studio\Foto-Studio.exe" (
  start "" "Foto-Studio\Foto-Studio.exe"
) else (
  echo Nie znaleziono Foto-Studio\Foto-Studio.exe
  pause
)
