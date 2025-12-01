@echo off
chcp 65001 > nul
title Aristote RAG Chatbot - DEBUG

echo ==========================================
echo   MODE DEBUG - Aristote RAG Chatbot
echo ==========================================
echo.

cd /d "%~dp0"
echo [DEBUG] Repertoire courant: %CD%
echo.

echo [DEBUG] Verification de la structure...
echo   - python\python.exe existe?
if exist "python\python.exe" (echo     OUI) else (echo     NON - ERREUR!)
echo   - ollama\ollama.exe existe?
if exist "ollama\ollama.exe" (echo     OUI) else (echo     NON - ERREUR!)
echo   - app\app.py existe?
if exist "app\app.py" (echo     OUI) else (echo     NON - ERREUR!)
echo   - app\.env existe?
if exist "app\.env" (echo     OUI) else (echo     NON - Creez-le avec CONFIGURER.bat)
echo.

echo [DEBUG] Test Python...
"python\python.exe" --version
if errorlevel 1 (
    echo     ERREUR: Python ne fonctionne pas!
    pause
    exit /b 1
)
echo.

echo [DEBUG] Test des modules Python...
"python\python.exe" -c "import streamlit; print('Streamlit OK:', streamlit.__version__)"
if errorlevel 1 (
    echo     ERREUR: Streamlit non installe!
    pause
    exit /b 1
)
echo.

echo [DEBUG] Demarrage d'Ollama...
start /b "" "ollama\ollama.exe" serve
echo     Ollama demarre en arriere-plan...
echo.

echo [DEBUG] Attente d'Ollama (max 60 secondes)...
set /a COUNT=0
:wait_loop
timeout /t 2 /nobreak > nul
set /a COUNT+=2
echo     Attente... %COUNT%s

REM Tester si Ollama repond
"ollama\ollama.exe" list > nul 2>&1
if errorlevel 1 (
    if %COUNT% GEQ 60 (
        echo     TIMEOUT - Ollama ne repond pas!
        echo.
        echo     Essayez de lancer Ollama manuellement:
        echo     ollama\ollama.exe serve
        pause
        exit /b 1
    )
    goto wait_loop
)

echo     Ollama est pret!
echo.

echo [DEBUG] Verification du modele nomic-embed-text...
"ollama\ollama.exe" list | findstr /i "nomic-embed-text" > nul
if errorlevel 1 (
    echo     Modele non trouve, telechargement...
    "ollama\ollama.exe" pull nomic-embed-text
    if errorlevel 1 (
        echo     ERREUR: Impossible de telecharger le modele!
        pause
        exit /b 1
    )
) else (
    echo     Modele present!
)
echo.

echo [DEBUG] Lancement de Streamlit...
echo     URL: http://localhost:8501
echo.
echo ==========================================
echo   Si l'application ne s'ouvre pas,
echo   ouvrez manuellement: http://localhost:8501
echo ==========================================
echo.

cd /d "%~dp0app"
"%~dp0python\python.exe" -m streamlit run app.py --server.address=localhost --server.port=8501 --server.headless=true

echo.
echo [DEBUG] Streamlit s'est arrete.
echo Code de sortie: %errorlevel%
pause
