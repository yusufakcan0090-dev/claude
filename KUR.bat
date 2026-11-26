@echo off
chcp 65001 >nul
title Kesit Studyosu - Kurulum
cd /d "%~dp0"
echo.
echo   ==========================================
echo      KESIT STUDYOSU - KURULUM
echo   ==========================================
echo   Bu islem internet hizina gore 10-30 dk surebilir.
echo.

if not exist "%~dp0requirements.txt" goto :zipte
if not exist "%~dp0app\main.py" goto :zipte
goto :devam
:zipte
echo   ------------------------------------------------------------
echo   DIKKAT: Program dosyalari bulunamadi.
echo   KUR.bat'i zip'in ICINDEN actin. Once zip'i klasore cikarman lazim:
echo.
echo     1) KesitStudyosu.zip'e SAG TIKLA ^> "Tumunu ayikla"
echo     2) Cikan "KesitStudyosu" klasorunu ac
echo     3) Icindeki KUR.bat'a cift tikla
echo   ------------------------------------------------------------
pause
exit /b 1
:devam

set "PY="
for %%V in (3.12 3.11 3.13) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY (
  echo   Python bulunamadi, kuruluyor...
  winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
  py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
  if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
)
if not defined PY (
  echo.
  echo   HATA: Python kurulamadi.
  echo   https://www.python.org/downloads/ adresinden Python 3.12 indir,
  echo   kurarken "Add python.exe to PATH" kutusunu isaretle, sonra bu dosyayi tekrar calistir.
  pause
  exit /b 1
)
echo   Python: %PY%

if not exist ".venv\Scripts\python.exe" (
  echo   Sanal ortam olusturuluyor...
  %PY% -m venv .venv || (echo HATA: venv olusturulamadi & pause & exit /b 1)
)
set "VPY=%~dp0.venv\Scripts\python.exe"

echo.
echo   Paketler kuruluyor (ekran karti dosyalari buyuk, biraz surer)...
"%VPY%" -m pip install --upgrade pip >nul
"%VPY%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo   HATA: Paketler kurulamadi. Yukaridaki kirmizi yaziyi bana gonder.
  pause
  exit /b 1
)

"%VPY%" "%~dp0kurulum.py"

echo.
echo   Masaustune kisayol olusturuluyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Kesit Studyosu.lnk');$s.TargetPath='%~dp0.venv\Scripts\pythonw.exe';$s.Arguments='\"%~dp0app\main.py\"';$s.WorkingDirectory='%~dp0';$s.IconLocation='%~dp0app\ui\icon.ico';$s.Save()"

echo.
echo   ==========================================
echo     BITTI! Masaustundeki "Kesit Studyosu"
echo     simgesine cift tikla ya da BASLAT.bat'i calistir.
echo   ==========================================
pause
