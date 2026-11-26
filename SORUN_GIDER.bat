@echo off
chcp 65001 >nul
title Kesit Studyosu - Sorun Giderme
cd /d "%~dp0"
echo Program konsol acik sekilde baslatiliyor. Hata olursa burada yazar.
echo Bu pencereyi kapatma.
echo.
".venv\Scripts\python.exe" "app\main.py"
pause
