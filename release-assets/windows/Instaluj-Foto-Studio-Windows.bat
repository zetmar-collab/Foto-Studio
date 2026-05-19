@echo off
setlocal
cd /d "%~dp0"
echo Instalacja Foto-Studio 2.5
echo.
call "%~dp0Utworz-skrot-na-pulpicie-Windows.bat"
echo.
echo Uruchamiam Foto-Studio...
call "%~dp0Uruchom-Foto-Studio.bat"
