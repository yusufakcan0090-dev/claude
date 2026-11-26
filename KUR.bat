@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0requirements.txt" goto :zipte
if not exist "%~dp0app\main.py" goto :zipte
if not exist "%~dp0kur\arayuz.ps1" goto :zipte
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0kur\arayuz.ps1"
exit /b 0
:zipte
echo.
echo   DIKKAT: Program dosyalari bulunamadi.
echo   KUR.bat'i zip'in ICINDEN actin. Once zip'i klasore cikar:
echo     1) Zip'e SAG TIKLA ^> "Tumunu ayikla"
echo     2) Cikan klasoru ac, icindeki KUR.bat'a cift tikla
echo.
pause
