@echo off
chcp 65001 > nul
echo Arret des services...

taskkill /f /im ollama.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1
taskkill /f /im streamlit.exe > nul 2>&1

echo.
echo Services arretes.
timeout /t 2 > nul
