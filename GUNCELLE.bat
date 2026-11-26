@echo off
chcp 65001 >nul
title Kesit Studyosu - Guncelle
cd /d "%~dp0"
echo Video indirici (yt-dlp) guncelleniyor... Kick/YouTube indirme bozulursa bunu calistir.
".venv\Scripts\python.exe" -m pip install -U "yt-dlp[default]" curl_cffi deno
echo.
echo Tamam.
pause
