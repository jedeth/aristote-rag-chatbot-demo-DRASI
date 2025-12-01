@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

title Build Windows Pack - Aristote RAG Chatbot

echo.
echo ============================================================
echo   BUILD WINDOWS PACK - ARISTOTE RAG CHATBOT
echo   (Version sans Python pre-installe)
echo ============================================================
echo.

REM Configuration
set VERSION=1.0.0
set PYTHON_VERSION=3.11.9
set BUILD_DIR=%~dp0..\..\build\windows_pack
set DIST_DIR=%~dp0..\..\dist
set PROJECT_ROOT=%~dp0..\..

REM URLs
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set OLLAMA_URL=https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py

echo [INFO] Nettoyage du repertoire de build...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
mkdir "%BUILD_DIR%\ChatBotRAG"
mkdir "%BUILD_DIR%\ChatBotRAG\python"
mkdir "%BUILD_DIR%\ChatBotRAG\ollama"
mkdir "%BUILD_DIR%\ChatBotRAG\app"
mkdir "%BUILD_DIR%\ChatBotRAG\app\data"
mkdir "%BUILD_DIR%\ChatBotRAG\app\chroma_db"

echo.
echo ============================================================
echo   ETAPE 1/5 : Telechargement de Python %PYTHON_VERSION%
echo ============================================================
echo.

echo [INFO] Telechargement de Python embarque...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%BUILD_DIR%\python.zip'"
if errorlevel 1 (
    echo [ERREUR] Echec du telechargement de Python
    goto :error
)

echo [INFO] Extraction de Python...
powershell -Command "Expand-Archive -Path '%BUILD_DIR%\python.zip' -DestinationPath '%BUILD_DIR%\ChatBotRAG\python' -Force"
del "%BUILD_DIR%\python.zip"

REM Configurer le fichier ._pth
echo [INFO] Configuration de Python...
for %%f in ("%BUILD_DIR%\ChatBotRAG\python\python*._pth") do (
    powershell -Command "(Get-Content '%%f') -replace '#import site', 'import site' | Set-Content '%%f'"
    echo Lib\site-packages>> "%%f"
)

echo.
echo ============================================================
echo   ETAPE 2/5 : Installation de pip
echo ============================================================
echo.

echo [INFO] Telechargement de get-pip.py...
powershell -Command "Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%BUILD_DIR%\get-pip.py'"

echo [INFO] Installation de pip...
"%BUILD_DIR%\ChatBotRAG\python\python.exe" "%BUILD_DIR%\get-pip.py" --no-warn-script-location
del "%BUILD_DIR%\get-pip.py"

echo.
echo ============================================================
echo   ETAPE 3/5 : Installation des dependances
echo ============================================================
echo.

REM Creer un requirements modifie pour Windows
echo [INFO] Preparation des dependances...
copy "%PROJECT_ROOT%\requirements.txt" "%BUILD_DIR%\requirements.txt" > nul

echo [INFO] Installation des dependances (peut prendre plusieurs minutes)...
"%BUILD_DIR%\ChatBotRAG\python\python.exe" -m pip install -r "%BUILD_DIR%\requirements.txt" --no-warn-script-location -q
del "%BUILD_DIR%\requirements.txt"

echo.
echo ============================================================
echo   ETAPE 4/5 : Telechargement d'Ollama
echo ============================================================
echo.

echo [INFO] Telechargement d'Ollama...
powershell -Command "Invoke-WebRequest -Uri '%OLLAMA_URL%' -OutFile '%BUILD_DIR%\ollama.zip'"

echo [INFO] Extraction d'Ollama...
powershell -Command "Expand-Archive -Path '%BUILD_DIR%\ollama.zip' -DestinationPath '%BUILD_DIR%\ollama_temp' -Force"

REM Trouver et copier ollama.exe
for /r "%BUILD_DIR%\ollama_temp" %%f in (ollama.exe) do (
    copy "%%f" "%BUILD_DIR%\ChatBotRAG\ollama\ollama.exe" > nul
)
rmdir /s /q "%BUILD_DIR%\ollama_temp"
del "%BUILD_DIR%\ollama.zip"

echo.
echo ============================================================
echo   ETAPE 5/5 : Creation du pack final
echo ============================================================
echo.

echo [INFO] Copie des fichiers de l'application...
copy "%PROJECT_ROOT%\app.py" "%BUILD_DIR%\ChatBotRAG\app\" > nul
copy "%PROJECT_ROOT%\requirements.txt" "%BUILD_DIR%\ChatBotRAG\app\" > nul
copy "%PROJECT_ROOT%\.env.example" "%BUILD_DIR%\ChatBotRAG\app\.env" > nul

echo [INFO] Creation des scripts de lancement...

REM Script DEMARRER.bat
(
echo @echo off
echo chcp 65001 ^> nul
echo title Aristote RAG Chatbot
echo.
echo echo ==========================================
echo echo   Aristote RAG Chatbot - Demarrage
echo echo ==========================================
echo echo.
echo.
echo REM Verifier si c'est le premier lancement
echo if not exist "app\.env_configured" ^(
echo     echo PREMIER LANCEMENT : Configuration requise
echo     echo.
echo     echo Veuillez editer le fichier de configuration :
echo     echo   app\.env
echo     echo.
echo     echo Remplacez "votre_token_ici" par votre cle API Aristote.
echo     echo.
echo     start notepad "app\.env"
echo     echo.
echo     echo Apres avoir sauvegarde, appuyez sur une touche pour continuer...
echo     pause ^> nul
echo     echo. ^> "app\.env_configured"
echo ^)
echo.
echo echo [1/3] Demarrage d'Ollama...
echo cd /d "%%~dp0"
echo.
echo REM Demarrer Ollama en arriere-plan
echo start /b "" "ollama\ollama.exe" serve ^> nul 2^>^&1
echo.
echo REM Attendre qu'Ollama soit pret
echo :wait_ollama
echo timeout /t 2 /nobreak ^> nul
echo "ollama\ollama.exe" list ^> nul 2^>^&1
echo if errorlevel 1 goto wait_ollama
echo.
echo echo [2/3] Verification du modele d'embeddings...
echo "ollama\ollama.exe" list ^| findstr "nomic-embed-text" ^> nul
echo if errorlevel 1 ^(
echo     echo     Telechargement du modele ^(environ 270 Mo^)...
echo     "ollama\ollama.exe" pull nomic-embed-text
echo ^)
echo.
echo echo [3/3] Lancement de l'application...
echo echo.
echo echo ==========================================
echo echo   L'application va s'ouvrir dans votre
echo echo   navigateur a l'adresse :
echo echo   http://localhost:8501
echo echo ==========================================
echo echo.
echo echo Appuyez sur Ctrl+C pour arreter l'application.
echo echo.
echo.
echo cd /d "%%~dp0app"
echo "%%~dp0python\python.exe" -m streamlit run app.py --server.address=localhost --server.port=8501
echo.
echo echo.
echo echo Application arretee.
echo pause
) > "%BUILD_DIR%\ChatBotRAG\DEMARRER.bat"

REM Script ARRETER.bat
(
echo @echo off
echo chcp 65001 ^> nul
echo echo Arret des services...
echo taskkill /f /im ollama.exe ^> nul 2^>^&1
echo taskkill /f /im python.exe ^> nul 2^>^&1
echo echo Services arretes.
echo timeout /t 2
) > "%BUILD_DIR%\ChatBotRAG\ARRETER.bat"

REM Script CONFIGURER.bat
(
echo @echo off
echo chcp 65001 ^> nul
echo echo Ouverture du fichier de configuration...
echo start notepad "%%~dp0app\.env"
) > "%BUILD_DIR%\ChatBotRAG\CONFIGURER.bat"

REM Fichier LISEZ-MOI.txt
(
echo.
echo ================================================================
echo           ARISTOTE RAG CHATBOT - GUIDE RAPIDE
echo ================================================================
echo.
echo INSTALLATION EN 2 ETAPES :
echo.
echo 1. CONFIGURER ^(une seule fois^)
echo    - Double-cliquez sur CONFIGURER.bat
echo    - Remplacez "votre_token_ici" par votre cle API Aristote
echo    - Sauvegardez et fermez le Bloc-notes
echo.
echo 2. DEMARRER
echo    - Double-cliquez sur DEMARRER.bat
echo    - L'application s'ouvre dans votre navigateur
echo    - Adresse : http://localhost:8501
echo.
echo ARRETER L'APPLICATION :
echo    - Fermez la fenetre noire ^(invite de commandes^)
echo    - OU double-cliquez sur ARRETER.bat
echo.
echo BESOIN D'AIDE ?
echo    Contactez l'equipe DRASI ou consultez la documentation.
echo.
) > "%BUILD_DIR%\ChatBotRAG\LISEZ-MOI.txt"

echo [INFO] Creation de l'archive ZIP...
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM Generer le nom du fichier avec la date
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATESTAMP=%datetime:~0,8%

set ZIP_NAME=ChatBotRAG_Windows_Pack_v%VERSION%_%DATESTAMP%.zip
powershell -Command "Compress-Archive -Path '%BUILD_DIR%\ChatBotRAG' -DestinationPath '%DIST_DIR%\%ZIP_NAME%' -Force"

echo.
echo ============================================================
echo   BUILD TERMINE AVEC SUCCES !
echo ============================================================
echo.
echo   Pack cree : %DIST_DIR%\%ZIP_NAME%
echo.
echo   Pour distribuer :
echo   1. Partagez le fichier ZIP
echo   2. L'utilisateur extrait le ZIP
echo   3. Double-clic sur DEMARRER.bat
echo.
echo ============================================================
echo.

goto :end

:error
echo.
echo [ERREUR] Le build a echoue.
echo.

:end
pause
