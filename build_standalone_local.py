#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Standalone Package - Version locale
Utilise le venv existant du projet pour creer un package autonome
"""

import subprocess
import sys
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Fix encodage console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configuration
APP_NAME = "ChatBotRAG"
APP_VERSION = "1.0.0"


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"   {text}")
    print("=" * 60 + "\n")


def get_project_dir() -> Path:
    return Path(__file__).parent


def main():
    print_header(f"Build Standalone Local - {APP_NAME} v{APP_VERSION}")

    project_dir = get_project_dir()
    venv_dir = project_dir / "venv"
    dist_dir = project_dir / "dist"

    # Verifie que le venv existe
    if not venv_dir.exists():
        print("ERREUR: Le dossier venv/ n'existe pas!")
        print("Creez-le d'abord avec: python -m venv venv")
        print("Puis installez les dependances: venv\\Scripts\\pip install -r requirements.txt")
        sys.exit(1)

    venv_python = venv_dir / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"ERREUR: Python non trouve dans {venv_python}")
        sys.exit(1)

    print(f"Utilisation du venv existant: {venv_dir}")

    # Nettoyage
    if dist_dir.exists():
        print("Nettoyage du dossier dist/...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Nom du package
    timestamp = datetime.now().strftime("%Y%m%d")
    package_name = f"{APP_NAME}_Standalone_v{APP_VERSION}_{timestamp}"
    package_dir = dist_dir / package_name
    package_dir.mkdir()

    print(f"\nCreation du package: {package_name}")

    # 1. Copier le venv
    print_header("Copie de l'environnement Python")
    print("  Copie du venv (cela peut prendre quelques minutes)...")
    venv_dest = package_dir / "venv"
    shutil.copytree(venv_dir, venv_dest, dirs_exist_ok=True)
    print(f"  Venv copie: {venv_dest}")

    # 2. Copier les fichiers sources
    print_header("Copie des fichiers sources")
    files_to_copy = [
        "app.py",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]

    for f in files_to_copy:
        src = project_dir / f
        if src.exists():
            shutil.copy2(src, package_dir / f)
            print(f"  + {f}")

    # Copie .env depuis .env.example
    env_example = package_dir / ".env.example"
    env_file = package_dir / ".env"
    if env_example.exists():
        shutil.copy2(env_example, env_file)
        print("  + .env (depuis .env.example)")

    # 3. Creer les dossiers
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "chroma_db").mkdir(exist_ok=True)
    print("  + data/")
    print("  + chroma_db/")

    # 4. Creer le launcher
    print_header("Creation du launcher")
    launcher_content = '''@echo off
chcp 65001 >nul
title ChatBot RAG - Aristote Dispatcher

echo ============================================================
echo    ChatBot RAG - Aristote Dispatcher
echo ============================================================
echo.

REM Chemin du script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Verification d'Ollama
echo [1/4] Verification d'Ollama...
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe" (
        set "OLLAMA_PATH=%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"
    ) else if exist "%PROGRAMFILES%\\Ollama\\ollama.exe" (
        set "OLLAMA_PATH=%PROGRAMFILES%\\Ollama\\ollama.exe"
    ) else (
        echo   Ollama n'est pas installe!
        echo   Telechargez-le depuis: https://ollama.com
        echo.
        echo   Appuyez sur une touche pour ouvrir le site de telechargement...
        pause >nul
        start https://ollama.com/download
        exit /b 1
    )
) else (
    set "OLLAMA_PATH=ollama"
)
echo   Ollama trouve.

REM Verification si Ollama tourne
echo.
echo [2/4] Demarrage d'Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   Demarrage d'Ollama en arriere-plan...
    start /min "" "%OLLAMA_PATH%" serve
    timeout /t 5 /nobreak >nul
)
echo   Ollama en cours d'execution.

REM Verification du modele
echo.
echo [3/4] Verification du modele nomic-embed-text...
curl -s http://localhost:11434/api/tags 2>nul | findstr /i "nomic-embed-text" >nul
if %ERRORLEVEL% NEQ 0 (
    echo   Telechargement du modele nomic-embed-text...
    "%OLLAMA_PATH%" pull nomic-embed-text
)
echo   Modele disponible.

REM Lancement de l'application
echo.
echo [4/4] Lancement de l'application...
echo.
echo ============================================================
echo   L'application demarre...
echo   Une fenetre de navigateur va s'ouvrir.
echo ============================================================
echo.
echo   Pour arreter: fermez cette fenetre ou appuyez sur Ctrl+C
echo.

"%SCRIPT_DIR%venv\\Scripts\\python.exe" -m streamlit run "%SCRIPT_DIR%app.py" --server.headless true --browser.gatherUsageStats false

pause
'''
    launcher_bat = package_dir / "ChatBotRAG.bat"
    launcher_bat.write_text(launcher_content, encoding='utf-8')
    print(f"  + ChatBotRAG.bat")

    # 5. Creer le README d'installation
    readme_content = '''
================================================================================
    ChatBot RAG - Aristote Dispatcher
    Version Standalone (Autonome)
================================================================================

UTILISATION
-----------

1. Double-cliquez sur "ChatBotRAG.bat"

2. Au premier lancement:
   - Si Ollama n'est pas installe, le site de telechargement s'ouvrira
   - Le modele d'embedding sera telecharge si necessaire (~270 MB)

3. L'interface web s'ouvrira dans votre navigateur

4. Entrez votre cle API Aristote dans la barre laterale


CONTENU DU PACKAGE
------------------

ChatBotRAG/
+-- ChatBotRAG.bat      <- Double-cliquez ici pour lancer
+-- venv/               <- Environnement Python (ne pas modifier)
+-- app.py              <- Application
+-- data/               <- Vos documents
+-- chroma_db/          <- Base de donnees


PREREQUIS
---------

- Windows 10/11 (64-bit)
- Connexion Internet (pour API Aristote)
- Ollama (sera propose au premier lancement si absent)
  Telecharger: https://ollama.com


EN CAS DE PROBLEME
------------------

1. Verifiez qu'Ollama est installe et fonctionne
   - Icone Ollama dans la barre des taches
   - Ou lancez: ollama serve

2. Verifiez votre connexion Internet

3. Verifiez votre cle API Aristote

================================================================================
'''
    (package_dir / "LISEZMOI.txt").write_text(readme_content, encoding='utf-8')
    print("  + LISEZMOI.txt")

    # 6. Creer l'archive ZIP
    print_header("Creation de l'archive ZIP")
    zip_path = dist_dir / f"{package_name}.zip"
    print(f"  Creation de {zip_path.name}...")

    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, f"{package_name}/{arcname}")
                file_count += 1
                if file_count % 100 == 0:
                    print(f"    {file_count} fichiers...")

    zip_size = zip_path.stat().st_size / 1024 / 1024
    print(f"\n  Archive creee: {zip_path.name}")
    print(f"  Taille: {zip_size:.1f} MB")
    print(f"  Fichiers: {file_count}")

    # Resume
    print_header("Build termine!")
    print(f"Package: {zip_path}")
    print(f"\nContenu:")
    print(f"  - Environnement Python complet avec toutes les dependances")
    print(f"  - Launcher ChatBotRAG.bat")
    print(f"  - Application app.py")
    print(f"\nL'utilisateur n'a besoin que d'Ollama!")
    print(f"\nPour distribuer: partagez le fichier {zip_path.name}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild annule.")
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
