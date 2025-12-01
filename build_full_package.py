#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Full Package - Package COMPLET autonome
Inclut: Python embarqué + Dépendances + Ollama + Modèle d'embedding

Ce package n'a AUCUNE dépendance externe - tout est inclus.
"""

import subprocess
import sys
import os
import shutil
import zipfile
import urllib.request
import json
from pathlib import Path
from datetime import datetime

# Fix encodage console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configuration
APP_NAME = "ChatBotRAG"
APP_VERSION = "2.0.0"
PYTHON_VERSION = "3.12.7"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
OLLAMA_VERSION = "0.4.6"
OLLAMA_URL = f"https://github.com/ollama/ollama/releases/download/v{OLLAMA_VERSION}/ollama-windows-amd64.zip"
EMBEDDING_MODEL = "nomic-embed-text"


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"   {text}")
    print("=" * 70 + "\n")


def print_step(step: int, total: int, text: str):
    print(f"\n[{step}/{total}] {text}")
    print("-" * 50)


def download_file(url: str, dest: Path, desc: str = None):
    """Télécharge un fichier avec barre de progression."""
    if desc:
        print(f"  Téléchargement: {desc}")
    print(f"  URL: {url}")

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, count * block_size * 100 // total_size)
            mb_done = count * block_size / 1024 / 1024
            mb_total = total_size / 1024 / 1024
            print(f"\r  Progression: {percent}% ({mb_done:.1f}/{mb_total:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(url, dest, progress_hook)
    print()  # Nouvelle ligne après la progression


def extract_zip(zip_path: Path, dest: Path):
    """Extrait un fichier ZIP."""
    print(f"  Extraction vers: {dest}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest)


def get_project_dir() -> Path:
    return Path(__file__).parent


def main():
    print_header(f"Build FULL Package - {APP_NAME} v{APP_VERSION}")
    print("Ce package sera TOTALEMENT autonome (Python + Ollama + Modèle)")

    project_dir = get_project_dir()
    dist_dir = project_dir / "dist"
    temp_dir = project_dir / "temp_build"

    # Nettoyage
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if dist_dir.exists():
        print("Nettoyage du dossier dist/...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Nom du package
    timestamp = datetime.now().strftime("%Y%m%d")
    package_name = f"{APP_NAME}_Full_v{APP_VERSION}_{timestamp}"
    package_dir = dist_dir / package_name
    package_dir.mkdir()

    total_steps = 8

    # =========================================================================
    # ÉTAPE 1: Télécharger Python Embedded
    # =========================================================================
    print_step(1, total_steps, "Téléchargement de Python Embedded")

    python_zip = temp_dir / "python_embed.zip"
    download_file(PYTHON_EMBED_URL, python_zip, f"Python {PYTHON_VERSION} Embedded")

    python_dir = package_dir / "python"
    python_dir.mkdir()
    extract_zip(python_zip, python_dir)
    print(f"  Python installé dans: {python_dir}")

    # =========================================================================
    # ÉTAPE 2: Configurer Python Embedded pour pip
    # =========================================================================
    print_step(2, total_steps, "Configuration de Python pour pip")

    # Modifier le fichier ._pth pour activer site-packages
    pth_file = list(python_dir.glob("python*._pth"))[0]
    pth_content = pth_file.read_text()
    # Décommenter import site
    pth_content = pth_content.replace("#import site", "import site")
    # Ajouter Lib/site-packages
    if "Lib/site-packages" not in pth_content:
        pth_content += "\nLib/site-packages\n"
    pth_file.write_text(pth_content)
    print(f"  Modifié: {pth_file.name}")

    # Créer le dossier site-packages
    site_packages = python_dir / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    print(f"  Créé: Lib/site-packages")

    # =========================================================================
    # ÉTAPE 3: Installer pip
    # =========================================================================
    print_step(3, total_steps, "Installation de pip")

    get_pip = temp_dir / "get-pip.py"
    download_file(GET_PIP_URL, get_pip, "get-pip.py")

    python_exe = python_dir / "python.exe"
    print("  Exécution de get-pip.py...")
    result = subprocess.run(
        [str(python_exe), str(get_pip), "--no-warn-script-location"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"  ERREUR: {result.stderr}")
        sys.exit(1)
    print("  pip installé avec succès")

    # =========================================================================
    # ÉTAPE 4: Installer les dépendances Python
    # =========================================================================
    print_step(4, total_steps, "Installation des dépendances Python")

    # Créer un requirements.txt simplifié (sans sentence-transformers pour réduire la taille)
    requirements_content = """# Interface utilisateur
streamlit==1.40.0

# Client API OpenAI-compatible
openai==1.54.0

# Extraction de documents
PyMuPDF==1.24.0
python-docx==1.1.0

# Embeddings via Ollama (pas besoin de sentence-transformers)
ollama==0.4.4

# Base vectorielle
chromadb==0.5.0
numpy<2.0.0

# Utilitaires
python-dotenv==1.0.0

# Validation fichiers Windows
python-magic-bin==0.4.14
"""

    req_file = temp_dir / "requirements_minimal.txt"
    req_file.write_text(requirements_content)

    pip_exe = python_dir / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        pip_exe = python_dir / "Scripts" / "pip3.exe"

    print("  Installation des packages (cela peut prendre plusieurs minutes)...")
    print("  Packages: streamlit, openai, PyMuPDF, python-docx, ollama, chromadb...")

    result = subprocess.run(
        [str(pip_exe), "install", "-r", str(req_file), "--no-warn-script-location", "-q"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"  ATTENTION: Certains packages ont eu des warnings")
        print(f"  {result.stderr[:500] if result.stderr else 'OK'}")

    print("  Dépendances installées")

    # =========================================================================
    # ÉTAPE 5: Télécharger Ollama
    # =========================================================================
    print_step(5, total_steps, "Téléchargement d'Ollama")

    ollama_zip = temp_dir / "ollama.zip"
    download_file(OLLAMA_URL, ollama_zip, f"Ollama v{OLLAMA_VERSION}")

    ollama_dir = package_dir / "ollama"
    ollama_dir.mkdir()
    extract_zip(ollama_zip, ollama_dir)
    print(f"  Ollama installé dans: {ollama_dir}")

    # =========================================================================
    # ÉTAPE 6: Pré-télécharger le modèle d'embedding
    # =========================================================================
    print_step(6, total_steps, f"Pré-téléchargement du modèle {EMBEDDING_MODEL}")

    # Créer le dossier pour les modèles Ollama
    models_dir = package_dir / "ollama_models"
    models_dir.mkdir()

    # On va créer un script qui téléchargera le modèle au premier lancement
    # car Ollama nécessite d'être en cours d'exécution pour pull
    print("  Le modèle sera téléchargé au premier lancement (~270 MB)")
    print("  (Ollama doit être en cours d'exécution pour télécharger)")

    # =========================================================================
    # ÉTAPE 7: Copier les fichiers de l'application
    # =========================================================================
    print_step(7, total_steps, "Copie des fichiers de l'application")

    # Copier app.py et autres fichiers
    files_to_copy = [
        "app.py",
        ".env.example",
        "README.md",
    ]

    for f in files_to_copy:
        src = project_dir / f
        if src.exists():
            shutil.copy2(src, package_dir / f)
            print(f"  + {f}")

    # Créer .env depuis .env.example
    env_example = package_dir / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, package_dir / ".env")
        print("  + .env (copié depuis .env.example)")

    # Créer les dossiers de données
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "chroma_db").mkdir(exist_ok=True)
    print("  + data/")
    print("  + chroma_db/")

    # =========================================================================
    # ÉTAPE 8: Créer les scripts de lancement
    # =========================================================================
    print_step(8, total_steps, "Création des scripts de lancement")

    # Launcher principal
    launcher_content = r'''@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title ChatBot RAG - Package Autonome

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║           ChatBot RAG - Aristote Dispatcher                      ║
echo ║                 Package Autonome Complet                         ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM Chemins
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_EXE=%SCRIPT_DIR%python\python.exe"
set "OLLAMA_EXE=%SCRIPT_DIR%ollama\ollama.exe"
set "OLLAMA_MODELS=%SCRIPT_DIR%ollama_models"

REM Définir où Ollama stocke ses modèles (dans le package)
set "OLLAMA_MODELS=%SCRIPT_DIR%ollama_models"

echo [1/5] Vérification de Python embarqué...
if not exist "%PYTHON_EXE%" (
    echo   ERREUR: Python non trouvé dans le package!
    echo   Le fichier %PYTHON_EXE% est manquant.
    pause
    exit /b 1
)
echo   Python OK

echo.
echo [2/5] Vérification d'Ollama embarqué...
if not exist "%OLLAMA_EXE%" (
    echo   ERREUR: Ollama non trouvé dans le package!
    echo   Le fichier %OLLAMA_EXE% est manquant.
    pause
    exit /b 1
)
echo   Ollama OK

echo.
echo [3/5] Démarrage d'Ollama...
REM Vérifier si Ollama tourne déjà
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   Lancement d'Ollama en arrière-plan...
    start /min "Ollama Server" "%OLLAMA_EXE%" serve
    echo   Attente du démarrage...
    timeout /t 5 /nobreak >nul

    REM Vérifier que c'est bien démarré
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo   Attente supplémentaire...
        timeout /t 5 /nobreak >nul
    )
)
echo   Ollama en cours d'exécution

echo.
echo [4/5] Vérification du modèle d'embedding (nomic-embed-text)...
curl -s http://localhost:11434/api/tags 2>nul | findstr /i "nomic-embed-text" >nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   ┌─────────────────────────────────────────────────────────────┐
    echo   │  Premier lancement: téléchargement du modèle d'embedding   │
    echo   │  Taille: ~270 MB - Cela peut prendre quelques minutes      │
    echo   └─────────────────────────────────────────────────────────────┘
    echo.
    "%OLLAMA_EXE%" pull nomic-embed-text
    if !ERRORLEVEL! NEQ 0 (
        echo   ERREUR: Impossible de télécharger le modèle
        echo   Vérifiez votre connexion Internet
        pause
        exit /b 1
    )
)
echo   Modèle nomic-embed-text disponible

echo.
echo [5/5] Lancement de l'application...
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  L'application démarre...                                        ║
echo ║  Une fenêtre de navigateur va s'ouvrir automatiquement.         ║
echo ║                                                                  ║
echo ║  Pour arrêter: fermez cette fenêtre ou appuyez sur Ctrl+C       ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

"%PYTHON_EXE%" -m streamlit run "%SCRIPT_DIR%app.py" --server.headless true --browser.gatherUsageStats false

echo.
echo Application fermée.
pause
'''

    launcher_bat = package_dir / "LANCER_CHATBOT.bat"
    launcher_bat.write_text(launcher_content, encoding='utf-8')
    print("  + LANCER_CHATBOT.bat")

    # Script d'arrêt
    stop_content = r'''@echo off
echo Arrêt d'Ollama...
taskkill /F /IM ollama.exe >nul 2>&1
echo Ollama arrêté.
timeout /t 2 /nobreak >nul
'''
    stop_bat = package_dir / "ARRETER_OLLAMA.bat"
    stop_bat.write_text(stop_content, encoding='utf-8')
    print("  + ARRETER_OLLAMA.bat")

    # README
    readme_content = '''
================================================================================
          ChatBot RAG - Aristote Dispatcher
          PACKAGE AUTONOME COMPLET v2.0
================================================================================

Ce package contient TOUT ce dont vous avez besoin:
  ✓ Python embarqué (pas besoin d'installer Python)
  ✓ Ollama embarqué (pas besoin d'installer Ollama)
  ✓ Toutes les dépendances Python
  ✓ Le modèle d'embedding sera téléchargé au 1er lancement (~270 MB)

================================================================================
                         UTILISATION
================================================================================

1. Double-cliquez sur "LANCER_CHATBOT.bat"

2. Au PREMIER lancement uniquement:
   - Le modèle d'embedding sera téléchargé (~270 MB)
   - Cela peut prendre quelques minutes selon votre connexion

3. L'interface web s'ouvrira dans votre navigateur

4. Entrez votre clé API Aristote dans la barre latérale

5. Chargez vos documents PDF/DOCX et posez vos questions!

================================================================================
                         CONTENU DU PACKAGE
================================================================================

ChatBotRAG_Full/
├── LANCER_CHATBOT.bat    <- Double-cliquez ici!
├── ARRETER_OLLAMA.bat    <- Pour arrêter Ollama manuellement
├── python/               <- Python embarqué (ne pas modifier)
├── ollama/               <- Ollama embarqué (ne pas modifier)
├── ollama_models/        <- Modèles Ollama (créé au 1er lancement)
├── app.py                <- Application principale
├── data/                 <- Vos documents
├── chroma_db/            <- Base de données vectorielle
└── .env                  <- Configuration (clé API)

================================================================================
                         PRÉREQUIS
================================================================================

- Windows 10/11 (64-bit)
- Connexion Internet:
  * Au premier lancement (téléchargement modèle ~270 MB)
  * Pour utiliser l'API Aristote

================================================================================
                         EN CAS DE PROBLÈME
================================================================================

1. "Ollama ne démarre pas"
   → Vérifiez qu'aucun autre Ollama ne tourne déjà
   → Exécutez ARRETER_OLLAMA.bat puis relancez

2. "Le modèle ne se télécharge pas"
   → Vérifiez votre connexion Internet
   → Vérifiez votre pare-feu/proxy

3. "L'application ne trouve pas mes documents"
   → Vérifiez que les fichiers sont bien en PDF ou DOCX
   → Rechargez les documents après un redémarrage

4. "Erreur de clé API"
   → Vérifiez votre clé API Aristote dans la barre latérale
   → La clé doit être valide et active

================================================================================
                         SUPPORT
================================================================================

Ce package a été créé pour l'atelier Vibe Coding - DRASI
Date de création: ''' + datetime.now().strftime("%d/%m/%Y") + '''

================================================================================
'''

    (package_dir / "LISEZMOI.txt").write_text(readme_content, encoding='utf-8')
    print("  + LISEZMOI.txt")

    # =========================================================================
    # Création de l'archive ZIP
    # =========================================================================
    print_header("Création de l'archive ZIP")

    zip_path = dist_dir / f"{package_name}.zip"
    print(f"  Création de {zip_path.name}...")
    print("  (Cela peut prendre plusieurs minutes)")

    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                # Exclure les fichiers __pycache__ et .pyc pour réduire la taille
                if "__pycache__" in str(file_path) or file_path.suffix == ".pyc":
                    continue
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, f"{package_name}/{arcname}")
                file_count += 1
                if file_count % 500 == 0:
                    print(f"    {file_count} fichiers compressés...")

    zip_size = zip_path.stat().st_size / 1024 / 1024
    print(f"\n  Archive créée: {zip_path.name}")
    print(f"  Taille: {zip_size:.1f} MB")
    print(f"  Fichiers: {file_count}")

    # Nettoyage
    print("\nNettoyage des fichiers temporaires...")
    shutil.rmtree(temp_dir)

    # Résumé final
    print_header("BUILD TERMINÉ AVEC SUCCÈS!")
    print(f"Package créé: {zip_path}")
    print(f"Taille totale: {zip_size:.1f} MB")
    print()
    print("Ce package contient:")
    print(f"  ✓ Python {PYTHON_VERSION} embarqué")
    print(f"  ✓ Ollama v{OLLAMA_VERSION} embarqué")
    print(f"  ✓ Toutes les dépendances Python (streamlit, chromadb, etc.)")
    print(f"  ✓ Scripts de lancement automatiques")
    print()
    print("L'utilisateur final n'a RIEN à installer!")
    print("(Le modèle d'embedding sera téléchargé au premier lancement)")
    print()
    print(f"Pour distribuer: partagez le fichier {zip_path.name}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild annulé par l'utilisateur.")
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
