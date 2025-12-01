@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
title Aristote RAG Chatbot

echo ==========================================
echo   Aristote RAG Chatbot - Demarrage
echo ==========================================
echo.

cd /d "%~dp0"

REM Verifier si c'est le premier lancement
if not exist "app\.env_configured" (
    echo PREMIER LANCEMENT : Configuration requise
    echo.
    echo Veuillez editer le fichier de configuration :
    echo   app\.env
    echo.
    echo Remplacez "votre_token_ici" par votre cle API Aristote.
    echo.
    start notepad "app\.env"
    echo.
    echo Apres avoir sauvegarde, appuyez sur une touche pour continuer...
    pause > nul
    echo OK > "app\.env_configured"
)

echo [1/3] Demarrage d'Ollama...

REM Verifier si Ollama tourne deja
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" > nul
if errorlevel 1 (
    REM Ollama ne tourne pas, le demarrer
    start "" /b "%~dp0ollama\ollama.exe" serve
)

REM Attendre qu'Ollama soit pret (max 60 secondes)
echo     Attente d'Ollama...
set OLLAMA_READY=0
for /l %%i in (1,1,30) do (
    if !OLLAMA_READY!==0 (
        "%~dp0ollama\ollama.exe" list > nul 2>&1
        if not errorlevel 1 (
            set OLLAMA_READY=1
        ) else (
            timeout /t 2 /nobreak > nul
        )
    )
)

REM Verifier si Ollama a demarre
"%~dp0ollama\ollama.exe" list > nul 2>&1
if errorlevel 1 (
    echo.
    echo ERREUR: Ollama ne repond pas apres 60 secondes.
    echo Essayez de relancer le script.
    pause
    exit /b 1
)
echo     Ollama est pret!

echo [2/3] Verification du modele d'embeddings...
"%~dp0ollama\ollama.exe" list 2>nul | findstr /i "nomic-embed-text" > nul
if errorlevel 1 (
    echo     Telechargement du modele - environ 270 Mo...
    echo     Cela peut prendre quelques minutes...
    "%~dp0ollama\ollama.exe" pull nomic-embed-text
    if errorlevel 1 (
        echo ERREUR: Impossible de telecharger le modele.
        echo Verifiez votre connexion Internet.
        pause
        exit /b 1
    )
)
echo     Modele OK!

echo [3/3] Lancement de l'application...
echo.
echo ==========================================
echo   L'application demarre...
echo
echo   Si le navigateur ne s'ouvre pas,
echo   allez sur: http://localhost:8501
echo.
echo   Appuyez sur Ctrl+C pour arreter.
echo ==========================================
echo.

cd /d "%~dp0app"
"%~dp0python\python.exe" -m streamlit run app.py --server.address=localhost --server.port=8501 --server.headless=true --browser.gatherUsageStats=false

echo.
echo Application arretee.
pause
