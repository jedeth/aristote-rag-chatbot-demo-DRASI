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
set SCRIPT_DIR=%~dp0
set BUILD_DIR=%~dp0..\..\build\windows_pack
set DIST_DIR=%~dp0..\..\dist
set PROJECT_ROOT=%~dp0..\..
set TEMPLATES_DIR=%~dp0templates

REM URLs
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set OLLAMA_URL=https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py

REM Verifier que les templates existent
if not exist "%TEMPLATES_DIR%\DEMARRER.bat" (
    echo [ERREUR] Templates non trouves dans: %TEMPLATES_DIR%
    echo Assurez-vous que le dossier 'templates' existe.
    goto :error
)

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
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%BUILD_DIR%\python.zip'" 2>nul
if errorlevel 1 (
    echo [ERREUR] Echec du telechargement de Python
    echo          Verifiez votre connexion Internet.
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
powershell -Command "Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%BUILD_DIR%\get-pip.py'" 2>nul
if errorlevel 1 (
    echo [ERREUR] Echec du telechargement de get-pip.py
    goto :error
)

echo [INFO] Installation de pip...
"%BUILD_DIR%\ChatBotRAG\python\python.exe" "%BUILD_DIR%\get-pip.py" --no-warn-script-location
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation de pip
    goto :error
)
del "%BUILD_DIR%\get-pip.py"

echo.
echo ============================================================
echo   ETAPE 3/5 : Installation des dependances
echo ============================================================
echo.

echo [INFO] Preparation des dependances...
copy "%PROJECT_ROOT%\requirements.txt" "%BUILD_DIR%\requirements.txt" > nul

echo [INFO] Installation des dependances (peut prendre plusieurs minutes)...
"%BUILD_DIR%\ChatBotRAG\python\python.exe" -m pip install -r "%BUILD_DIR%\requirements.txt" --no-warn-script-location
if errorlevel 1 (
    echo [AVERTISSEMENT] Certaines dependances ont peut-etre echoue.
    echo                 Verification...
)
del "%BUILD_DIR%\requirements.txt"

REM Verifier les modules critiques
echo [INFO] Verification des modules critiques...
"%BUILD_DIR%\ChatBotRAG\python\python.exe" -c "import streamlit; print('  Streamlit:', streamlit.__version__)"
if errorlevel 1 (
    echo [ERREUR] Streamlit n'est pas installe correctement!
    goto :error
)
"%BUILD_DIR%\ChatBotRAG\python\python.exe" -c "import chromadb; print('  ChromaDB:', chromadb.__version__)"
"%BUILD_DIR%\ChatBotRAG\python\python.exe" -c "import ollama; print('  Ollama client: OK')"

echo.
echo ============================================================
echo   ETAPE 4/5 : Telechargement d'Ollama
echo ============================================================
echo.

echo [INFO] Telechargement d'Ollama...
powershell -Command "Invoke-WebRequest -Uri '%OLLAMA_URL%' -OutFile '%BUILD_DIR%\ollama.zip'" 2>nul
if errorlevel 1 (
    echo [ERREUR] Echec du telechargement d'Ollama
    goto :error
)

echo [INFO] Extraction d'Ollama...
powershell -Command "Expand-Archive -Path '%BUILD_DIR%\ollama.zip' -DestinationPath '%BUILD_DIR%\ollama_temp' -Force"

REM Trouver et copier ollama.exe
set OLLAMA_FOUND=0
for /r "%BUILD_DIR%\ollama_temp" %%f in (ollama.exe) do (
    copy "%%f" "%BUILD_DIR%\ChatBotRAG\ollama\ollama.exe" > nul
    set OLLAMA_FOUND=1
)
rmdir /s /q "%BUILD_DIR%\ollama_temp"
del "%BUILD_DIR%\ollama.zip"

if "%OLLAMA_FOUND%"=="0" (
    echo [ERREUR] ollama.exe non trouve dans l'archive!
    goto :error
)
echo [INFO] Ollama installe.

echo.
echo ============================================================
echo   ETAPE 5/5 : Creation du pack final
echo ============================================================
echo.

echo [INFO] Copie des fichiers de l'application...
copy "%PROJECT_ROOT%\app.py" "%BUILD_DIR%\ChatBotRAG\app\" > nul
copy "%PROJECT_ROOT%\requirements.txt" "%BUILD_DIR%\ChatBotRAG\app\" > nul
copy "%PROJECT_ROOT%\.env.example" "%BUILD_DIR%\ChatBotRAG\app\.env" > nul

echo [INFO] Copie des scripts de lancement depuis les templates...
copy "%TEMPLATES_DIR%\DEMARRER.bat" "%BUILD_DIR%\ChatBotRAG\" > nul
copy "%TEMPLATES_DIR%\ARRETER.bat" "%BUILD_DIR%\ChatBotRAG\" > nul
copy "%TEMPLATES_DIR%\CONFIGURER.bat" "%BUILD_DIR%\ChatBotRAG\" > nul
copy "%TEMPLATES_DIR%\LISEZ-MOI.txt" "%BUILD_DIR%\ChatBotRAG\" > nul

REM Copier aussi le script de debug
if exist "%SCRIPT_DIR%\DEBUG.bat" (
    copy "%SCRIPT_DIR%\DEBUG.bat" "%BUILD_DIR%\ChatBotRAG\" > nul
    echo [INFO] Script DEBUG.bat inclus.
)

echo [INFO] Creation de l'archive ZIP...
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM Generer le nom du fichier avec la date
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATESTAMP=%datetime:~0,8%

set ZIP_NAME=ChatBotRAG_Windows_Pack_v%VERSION%_%DATESTAMP%.zip
powershell -Command "Compress-Archive -Path '%BUILD_DIR%\ChatBotRAG' -DestinationPath '%DIST_DIR%\%ZIP_NAME%' -Force"

if errorlevel 1 (
    echo [ERREUR] Echec de la creation du ZIP
    goto :error
)

REM Calculer la taille du ZIP
for %%A in ("%DIST_DIR%\%ZIP_NAME%") do set ZIP_SIZE=%%~zA
set /a ZIP_SIZE_MB=%ZIP_SIZE% / 1048576

echo.
echo ============================================================
echo   BUILD TERMINE AVEC SUCCES !
echo ============================================================
echo.
echo   Pack cree : %DIST_DIR%\%ZIP_NAME%
echo   Taille    : environ %ZIP_SIZE_MB% Mo
echo.
echo   Pour distribuer :
echo   1. Partagez le fichier ZIP a vos collegues
echo   2. Ils extraient le ZIP
echo   3. Double-clic sur DEMARRER.bat
echo.
echo ============================================================
echo.

goto :end

:error
echo.
echo ============================================================
echo   ERREUR - Le build a echoue !
echo ============================================================
echo.
echo   Verifiez les messages d'erreur ci-dessus.
echo.

:end
pause
