#!/usr/bin/env python3
"""
=============================================================================
Build Windows Pack - Aristote RAG Chatbot
=============================================================================
Ce script crée un pack Windows autonome contenant :
- Python embarqué (pas besoin d'installer Python)
- Toutes les dépendances
- Ollama intégré
- Scripts de lancement simples

Usage:
    python build_windows_pack.py

Résultat:
    dist/ChatBotRAG_Windows_Pack_vX.X.X.zip
=============================================================================
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

VERSION = "1.0.0"
PYTHON_VERSION = "3.11.9"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
OLLAMA_URL = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# Répertoires
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build" / "windows_pack"
DIST_DIR = PROJECT_ROOT / "dist"

# Fichiers à inclure dans le pack
FILES_TO_COPY = [
    "app.py",
    "requirements.txt",
    ".env.example",
]


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def log(message: str, level: str = "INFO"):
    """Affiche un message formaté."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def download_file(url: str, dest: Path, description: str = ""):
    """Télécharge un fichier avec barre de progression."""
    log(f"Téléchargement: {description or url}")

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, count * block_size * 100 // total_size)
            print(f"\r    Progression: {percent}%", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, dest, reporthook=progress_hook)
        print()  # Nouvelle ligne après la progression
        return True
    except Exception as e:
        log(f"Erreur de téléchargement: {e}", "ERROR")
        return False


def extract_zip(zip_path: Path, dest_dir: Path):
    """Extrait une archive ZIP."""
    log(f"Extraction: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


def clean_build():
    """Nettoie le répertoire de build."""
    if BUILD_DIR.exists():
        log("Nettoyage du répertoire de build...")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# ÉTAPES DE BUILD
# =============================================================================

def step1_download_python():
    """Télécharge et configure Python embarqué."""
    log("=" * 60)
    log("ÉTAPE 1/5 : Téléchargement de Python embarqué")
    log("=" * 60)

    python_dir = BUILD_DIR / "python"
    python_dir.mkdir(exist_ok=True)

    # Télécharger Python embed
    zip_path = BUILD_DIR / "python_embed.zip"
    if not download_file(PYTHON_EMBED_URL, zip_path, f"Python {PYTHON_VERSION} embarqué"):
        raise RuntimeError("Échec du téléchargement de Python")

    extract_zip(zip_path, python_dir)
    zip_path.unlink()

    # Configurer le fichier ._pth pour autoriser pip
    pth_file = list(python_dir.glob("python*._pth"))[0]
    content = pth_file.read_text()
    # Décommenter import site
    content = content.replace("#import site", "import site")
    # Ajouter le répertoire Lib\site-packages
    content += "\nLib\\site-packages\n"
    pth_file.write_text(content)

    log("Python embarqué configuré avec succès")
    return python_dir


def step2_install_pip(python_dir: Path):
    """Installe pip dans Python embarqué."""
    log("=" * 60)
    log("ÉTAPE 2/5 : Installation de pip")
    log("=" * 60)

    get_pip_path = BUILD_DIR / "get-pip.py"
    if not download_file(GET_PIP_URL, get_pip_path, "get-pip.py"):
        raise RuntimeError("Échec du téléchargement de get-pip.py")

    python_exe = python_dir / "python.exe"

    log("Installation de pip...")
    result = subprocess.run(
        [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log(f"Erreur pip: {result.stderr}", "ERROR")
        raise RuntimeError("Échec de l'installation de pip")

    get_pip_path.unlink()
    log("pip installé avec succès")


def step3_install_dependencies(python_dir: Path):
    """Installe les dépendances du projet."""
    log("=" * 60)
    log("ÉTAPE 3/5 : Installation des dépendances")
    log("=" * 60)

    python_exe = python_dir / "python.exe"
    requirements_path = PROJECT_ROOT / "requirements.txt"

    log("Installation des dépendances (cela peut prendre quelques minutes)...")

    # Créer un requirements modifié pour Windows (python-magic-bin)
    temp_req = BUILD_DIR / "requirements_win.txt"
    content = requirements_path.read_text()
    # Remplacer la condition platform
    content = content.replace(
        'python-magic-bin==0.4.14; sys_platform == "win32"',
        'python-magic-bin==0.4.14'
    )
    content = content.replace(
        'python-magic==0.4.27; sys_platform != "win32"',
        '# python-magic non nécessaire sur Windows'
    )
    temp_req.write_text(content)

    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-r", str(temp_req),
         "--no-warn-script-location", "--quiet"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log(f"Erreur installation: {result.stderr}", "ERROR")
        # Continuer quand même, certains warnings ne sont pas fatals

    temp_req.unlink()
    log("Dépendances installées avec succès")


def step4_download_ollama():
    """Télécharge Ollama pour Windows."""
    log("=" * 60)
    log("ÉTAPE 4/5 : Téléchargement d'Ollama")
    log("=" * 60)

    ollama_dir = BUILD_DIR / "ollama"
    ollama_dir.mkdir(exist_ok=True)

    zip_path = BUILD_DIR / "ollama.zip"
    if not download_file(OLLAMA_URL, zip_path, "Ollama pour Windows"):
        raise RuntimeError("Échec du téléchargement d'Ollama")

    extract_zip(zip_path, ollama_dir)
    zip_path.unlink()

    log("Ollama téléchargé avec succès")
    return ollama_dir


def step5_create_pack():
    """Crée le pack final avec tous les fichiers."""
    log("=" * 60)
    log("ÉTAPE 5/5 : Création du pack final")
    log("=" * 60)

    pack_dir = BUILD_DIR / "ChatBotRAG"
    pack_dir.mkdir(exist_ok=True)

    # Copier Python
    log("Copie de Python embarqué...")
    shutil.copytree(BUILD_DIR / "python", pack_dir / "python")

    # Copier Ollama
    log("Copie d'Ollama...")
    ollama_src = BUILD_DIR / "ollama"
    ollama_dest = pack_dir / "ollama"
    ollama_dest.mkdir(exist_ok=True)

    # Trouver ollama.exe (peut être dans un sous-dossier)
    for f in ollama_src.rglob("ollama.exe"):
        shutil.copy2(f, ollama_dest / "ollama.exe")
        break

    # Copier les fichiers de l'application
    log("Copie des fichiers de l'application...")
    app_dir = pack_dir / "app"
    app_dir.mkdir(exist_ok=True)

    for file in FILES_TO_COPY:
        src = PROJECT_ROOT / file
        if src.exists():
            shutil.copy2(src, app_dir / file)

    # Renommer .env.example en .env
    env_example = app_dir / ".env.example"
    env_file = app_dir / ".env"
    if env_example.exists():
        shutil.copy2(env_example, env_file)

    # Créer les répertoires de données
    (app_dir / "data").mkdir(exist_ok=True)
    (app_dir / "chroma_db").mkdir(exist_ok=True)

    # Copier les scripts de lancement depuis les templates
    copy_launcher_scripts(pack_dir)

    # Créer le ZIP final
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    zip_name = f"ChatBotRAG_Windows_Pack_v{VERSION}_{date_str}"
    zip_path = DIST_DIR / f"{zip_name}.zip"

    log(f"Création de l'archive: {zip_path.name}")
    shutil.make_archive(str(DIST_DIR / zip_name), 'zip', BUILD_DIR, "ChatBotRAG")

    log("Pack créé avec succès!")
    return zip_path


def copy_launcher_scripts(pack_dir: Path):
    """Copie les scripts de lancement depuis les templates."""
    templates_dir = SCRIPT_DIR / "templates"

    templates = [
        "DEMARRER.bat",
        "ARRETER.bat",
        "CONFIGURER.bat",
        "LISEZ-MOI.txt"
    ]

    for template in templates:
        src = templates_dir / template
        if src.exists():
            shutil.copy2(src, pack_dir / template)
            log(f"  Copié: {template}")
        else:
            log(f"  ATTENTION: Template manquant: {template}", "WARN")

    # Copier aussi DEBUG.bat s'il existe
    debug_script = SCRIPT_DIR / "DEBUG.bat"
    if debug_script.exists():
        shutil.copy2(debug_script, pack_dir / "DEBUG.bat")
        log("  Copié: DEBUG.bat")

    log("Scripts de lancement copiés")


def create_launcher_scripts_legacy(pack_dir: Path):
    """LEGACY: Crée les scripts de lancement (utilisé si templates absents)."""

    # Script principal de démarrage
    start_script = pack_dir / "DEMARRER.bat"
    start_script.write_text(r'''@echo off
chcp 65001 > nul
title Aristote RAG Chatbot

echo ==========================================
echo   Aristote RAG Chatbot - Démarrage
echo ==========================================
echo.

REM Vérifier si c'est le premier lancement
if not exist "app\.env_configured" (
    echo PREMIER LANCEMENT : Configuration requise
    echo.
    echo Veuillez éditer le fichier de configuration :
    echo   app\.env
    echo.
    echo Remplacez "votre_token_ici" par votre clé API Aristote.
    echo.
    start notepad "app\.env"
    echo.
    echo Après avoir sauvegardé, appuyez sur une touche pour continuer...
    pause > nul
    echo. > "app\.env_configured"
)

echo [1/3] Démarrage d'Ollama...
cd /d "%~dp0"

REM Démarrer Ollama en arrière-plan
start /b "" "ollama\ollama.exe" serve > nul 2>&1

REM Attendre qu'Ollama soit prêt
:wait_ollama
timeout /t 2 /nobreak > nul
"ollama\ollama.exe" list > nul 2>&1
if errorlevel 1 goto wait_ollama

echo [2/3] Vérification du modèle d'embeddings...
"ollama\ollama.exe" list | findstr "nomic-embed-text" > nul
if errorlevel 1 (
    echo     Téléchargement du modèle (environ 270 Mo)...
    "ollama\ollama.exe" pull nomic-embed-text
)

echo [3/3] Lancement de l'application...
echo.
echo ==========================================
echo   L'application va s'ouvrir dans votre
echo   navigateur à l'adresse :
echo   http://localhost:8501
echo ==========================================
echo.
echo Appuyez sur Ctrl+C pour arrêter l'application.
echo.

cd /d "%~dp0app"
"%~dp0python\python.exe" -m streamlit run app.py --server.address=localhost --server.port=8501

echo.
echo Application arrêtée.
pause
''', encoding='utf-8')

    # Script d'arrêt
    stop_script = pack_dir / "ARRETER.bat"
    stop_script.write_text(r'''@echo off
chcp 65001 > nul
echo Arrêt des services...

taskkill /f /im ollama.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

echo Services arrêtés.
timeout /t 2
''', encoding='utf-8')

    # Script de configuration
    config_script = pack_dir / "CONFIGURER.bat"
    config_script.write_text(r'''@echo off
chcp 65001 > nul
echo Ouverture du fichier de configuration...
start notepad "%~dp0app\.env"
''', encoding='utf-8')

    # README simplifié
    readme = pack_dir / "LISEZ-MOI.txt"
    readme.write_text(r'''
╔══════════════════════════════════════════════════════════════╗
║           ARISTOTE RAG CHATBOT - GUIDE RAPIDE               ║
╚══════════════════════════════════════════════════════════════╝

INSTALLATION EN 2 ÉTAPES :

1. CONFIGURER (une seule fois)
   ────────────────────────────
   • Double-cliquez sur CONFIGURER.bat
   • Remplacez "votre_token_ici" par votre clé API Aristote
   • Sauvegardez et fermez le Bloc-notes

2. DÉMARRER
   ─────────
   • Double-cliquez sur DEMARRER.bat
   • L'application s'ouvre dans votre navigateur
   • Adresse : http://localhost:8501


UTILISATION :
─────────────
1. Entrez votre clé API dans la barre latérale (si demandé)
2. Chargez vos documents PDF ou DOCX
3. Posez vos questions !


ARRÊTER L'APPLICATION :
───────────────────────
• Fermez la fenêtre noire (invite de commandes)
• OU double-cliquez sur ARRETER.bat


STRUCTURE DU DOSSIER :
──────────────────────
📁 ChatBotRAG/
   ├── DEMARRER.bat      ← Lance l'application
   ├── ARRETER.bat       ← Arrête l'application
   ├── CONFIGURER.bat    ← Édite la configuration
   ├── LISEZ-MOI.txt     ← Ce fichier
   ├── 📁 app/           ← Application
   ├── 📁 python/        ← Python embarqué
   └── 📁 ollama/        ← Moteur d'embeddings


DÉPANNAGE :
───────────
• "Erreur Ollama" → Relancez DEMARRER.bat
• "Clé API invalide" → Vérifiez votre clé dans CONFIGURER.bat
• L'application ne s'ouvre pas → Ouvrez manuellement
  http://localhost:8501 dans votre navigateur


BESOIN D'AIDE ?
───────────────
Contactez l'équipe DRASI ou consultez la documentation.

''', encoding='utf-8')

    log("Scripts de lancement créés")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal."""
    print()
    print("=" * 60)
    print("  BUILD WINDOWS PACK - ARISTOTE RAG CHATBOT")
    print(f"  Version: {VERSION}")
    print("=" * 60)
    print()

    # Vérifier qu'on est sur Windows
    if sys.platform != "win32":
        log("Ce script doit être exécuté sur Windows.", "ERROR")
        log("Pour créer le pack, exécutez-le sur une machine Windows.")
        sys.exit(1)

    try:
        # Nettoyer
        clean_build()

        # Étapes de build
        python_dir = step1_download_python()
        step2_install_pip(python_dir)
        step3_install_dependencies(python_dir)
        step4_download_ollama()
        zip_path = step5_create_pack()

        print()
        print("=" * 60)
        print("  BUILD TERMINÉ AVEC SUCCÈS!")
        print("=" * 60)
        print()
        print(f"  Pack créé: {zip_path}")
        print(f"  Taille: {zip_path.stat().st_size / 1024 / 1024:.1f} Mo")
        print()
        print("  Pour distribuer:")
        print("  1. Partagez le fichier ZIP")
        print("  2. L'utilisateur extrait le ZIP")
        print("  3. Double-clic sur DEMARRER.bat")
        print()

    except Exception as e:
        log(f"Erreur fatale: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
