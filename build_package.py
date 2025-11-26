#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Package - Genere le package complet (installateur + portable)
Script principal pour creer les distributions
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
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"


def print_header(text: str):
    """Affiche un en-tête formaté."""
    print("\n" + "="*60)
    print(f"   {text}")
    print("="*60 + "\n")


def get_project_dir() -> Path:
    """Retourne le répertoire du projet."""
    return Path(__file__).parent


def clean_build_directories():
    """Nettoie les répertoires de build précédents."""
    print("Nettoyage des builds précédents...")
    project_dir = get_project_dir()

    dirs_to_clean = [
        "build",
        "dist",
        "installer_output",
        "__pycache__",
    ]

    for dir_name in dirs_to_clean:
        dir_path = project_dir / dir_name
        if dir_path.exists():
            print(f"  Suppression de {dir_name}/")
            shutil.rmtree(dir_path)

    # Nettoie aussi les fichiers .pyc
    for pyc_file in project_dir.rglob("*.pyc"):
        pyc_file.unlink()

    print("  Nettoyage terminé!")


def check_requirements():
    """Vérifie que les outils nécessaires sont disponibles."""
    print("Vérification des prérequis...")

    errors = []

    # Vérifie PyInstaller
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  ✗ PyInstaller non installé")
        print("    Installation en cours...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("  ✓ PyInstaller installé")

    # Vérifie Inno Setup (optionnel pour la version portable)
    if os.path.exists(INNO_SETUP_PATH):
        print(f"  ✓ Inno Setup trouvé")
    else:
        print(f"  ⚠ Inno Setup non trouvé à: {INNO_SETUP_PATH}")
        print("    L'installateur MSI ne sera pas généré.")
        print("    Télécharger: https://jrsoftware.org/isdl.php")

    return len(errors) == 0


def build_executables():
    """Construit les exécutables avec PyInstaller."""
    print_header("Construction des exécutables")

    project_dir = get_project_dir()

    # Build ChatBotRAG.exe (launcher)
    print("Construction de ChatBotRAG.exe...")
    spec_file = project_dir / "ChatBotRAG.spec"

    if spec_file.exists():
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean", "-y"]
    else:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--console",
            "--name", "ChatBotRAG",
            "--clean", "-y",
            str(project_dir / "launcher.py")
        ]

    result = subprocess.run(cmd, cwd=str(project_dir))
    if result.returncode != 0:
        print("ERREUR: Construction de ChatBotRAG.exe échouée!")
        return False

    # Build Setup.exe
    print("\nConstruction de Setup.exe...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--console",
        "--name", "Setup",
        "--clean", "-y",
        str(project_dir / "setup_environment.py")
    ]

    result = subprocess.run(cmd, cwd=str(project_dir))
    if result.returncode != 0:
        print("ERREUR: Construction de Setup.exe échouée!")
        return False

    # Vérifie les résultats
    dist_dir = project_dir / "dist"
    launcher_exe = dist_dir / "ChatBotRAG.exe"
    setup_exe = dist_dir / "Setup.exe"

    if launcher_exe.exists() and setup_exe.exists():
        print(f"\n✓ ChatBotRAG.exe ({launcher_exe.stat().st_size / 1024 / 1024:.2f} MB)")
        print(f"✓ Setup.exe ({setup_exe.stat().st_size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print("ERREUR: Les exécutables n'ont pas été créés!")
        return False


def create_portable_package():
    """Crée la version portable (ZIP)."""
    print_header("Création du package portable")

    project_dir = get_project_dir()
    dist_dir = project_dir / "dist"

    # Nom du package
    timestamp = datetime.now().strftime("%Y%m%d")
    package_name = f"{APP_NAME}_Portable_v{APP_VERSION}_{timestamp}"
    package_dir = dist_dir / package_name

    # Crée le répertoire du package
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    print(f"Création du package dans: {package_dir}")

    # Fichiers à inclure
    files_to_copy = [
        # Exécutables
        (dist_dir / "ChatBotRAG.exe", "ChatBotRAG.exe"),
        (dist_dir / "Setup.exe", "Setup.exe"),

        # Sources Python
        (project_dir / "app.py", "app.py"),
        (project_dir / "launcher.py", "launcher.py"),
        (project_dir / "setup_environment.py", "setup_environment.py"),
        (project_dir / "requirements.txt", "requirements.txt"),

        # Configuration
        (project_dir / ".env.example", ".env.example"),

        # Documentation
        (project_dir / "README.md", "README.md"),
    ]

    # Copie les fichiers
    for src, dest in files_to_copy:
        if src.exists():
            dest_path = package_dir / dest
            print(f"  Copie: {dest}")
            shutil.copy2(src, dest_path)
        else:
            print(f"  ⚠ Fichier non trouvé: {src}")

    # Crée les répertoires vides
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "chroma_db").mkdir(exist_ok=True)

    # Crée un fichier README_INSTALLATION.txt
    readme_install = package_dir / "LISEZMOI_INSTALLATION.txt"
    with open(readme_install, "w", encoding="utf-8") as f:
        f.write("""
================================================================================
    ChatBot RAG - Aristote Dispatcher
    Version Portable
================================================================================

INSTALLATION
------------

1. Extraire cette archive dans un dossier de votre choix
   (ex: C:\\ChatBotRAG ou D:\\Apps\\ChatBotRAG)

2. Double-cliquer sur "Setup.exe" pour installer l'environnement Python
   - Cela crée un environnement virtuel local
   - Télécharge les dépendances (~500 MB)
   - Durée estimée: 5-15 minutes selon la connexion

3. Une fois le setup terminé, lancer "ChatBotRAG.exe"


PRÉREQUIS
---------

- Windows 10 ou 11 (64-bit)
- Python 3.9 ou supérieur installé sur le système
  (Télécharger: https://www.python.org/downloads/)
- Connexion Internet (pour le setup initial et Ollama)


PREMIER LANCEMENT
-----------------

Au premier lancement, ChatBotRAG.exe va:

1. Vérifier si Ollama est installé
   - Si non: proposer de l'installer automatiquement

2. Démarrer Ollama si nécessaire

3. Vérifier/télécharger le modèle d'embedding "nomic-embed-text"
   - Téléchargement automatique si absent (~270 MB)

4. Lancer l'interface web dans votre navigateur


UTILISATION
-----------

1. Dans l'interface web, entrez votre clé API Aristote dans la barre latérale

2. Uploadez vos documents (PDF, DOCX)

3. Posez vos questions au chatbot!


STRUCTURE DES DOSSIERS
----------------------

ChatBotRAG/
├── ChatBotRAG.exe      <- Lanceur principal
├── Setup.exe           <- Installation des dépendances
├── app.py              <- Application Streamlit
├── requirements.txt    <- Dépendances Python
├── .env.example        <- Template de configuration
├── data/               <- Vos documents uploadés
├── chroma_db/          <- Base de données vectorielle
└── venv/               <- Environnement Python (créé par Setup.exe)


SUPPORT
-------

En cas de problème:
- Relancer Setup.exe pour réinstaller les dépendances
- Vérifier que Python est dans le PATH système
- Vérifier la connexion Internet

================================================================================
""")

    # Crée l'archive ZIP
    zip_path = dist_dir / f"{package_name}.zip"
    print(f"\nCréation de l'archive: {zip_path.name}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, f"{package_name}/{arcname}")
                print(f"  + {arcname}")

    # Statistiques
    zip_size = zip_path.stat().st_size / 1024 / 1024
    print(f"\n✓ Archive créée: {zip_path.name} ({zip_size:.2f} MB)")

    # Nettoie le dossier temporaire
    shutil.rmtree(package_dir)

    return zip_path


def build_installer():
    """Construit l'installateur avec Inno Setup."""
    print_header("Construction de l'installateur Windows")

    if not os.path.exists(INNO_SETUP_PATH):
        print("⚠ Inno Setup non trouvé, installateur non généré.")
        print(f"  Chemin attendu: {INNO_SETUP_PATH}")
        print("  Télécharger: https://jrsoftware.org/isdl.php")
        return None

    project_dir = get_project_dir()
    iss_file = project_dir / "installer.iss"

    if not iss_file.exists():
        print("⚠ Fichier installer.iss non trouvé!")
        return None

    print(f"Compilation de {iss_file.name}...")

    result = subprocess.run(
        [INNO_SETUP_PATH, str(iss_file)],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Trouve le fichier généré
        output_dir = project_dir / "installer_output"
        installers = list(output_dir.glob("*.exe"))

        if installers:
            installer_path = installers[0]
            installer_size = installer_path.stat().st_size / 1024 / 1024
            print(f"\n✓ Installateur créé: {installer_path.name} ({installer_size:.2f} MB)")
            return installer_path
        else:
            print("⚠ L'installateur n'a pas été trouvé.")
            return None
    else:
        print(f"ERREUR lors de la compilation Inno Setup:")
        print(result.stderr)
        return None


def main():
    """Point d'entrée principal."""
    print_header(f"Build Package - {APP_NAME} v{APP_VERSION}")

    # Étape 1: Vérification des prérequis
    if not check_requirements():
        print("\nDes prérequis sont manquants. Corrigez les erreurs et réessayez.")
        sys.exit(1)

    # Étape 2: Nettoyage
    clean_build_directories()

    # Étape 3: Build des exécutables
    if not build_executables():
        print("\nLa construction des exécutables a échoué.")
        sys.exit(1)

    # Étape 4: Création du package portable
    portable_zip = create_portable_package()

    # Étape 5: Création de l'installateur
    installer_exe = build_installer()

    # Résumé
    print_header("Résumé du build")

    project_dir = get_project_dir()
    dist_dir = project_dir / "dist"

    print(f"Répertoire de sortie: {dist_dir}")
    print()

    if portable_zip and portable_zip.exists():
        print(f"✓ Version portable: {portable_zip.name}")
    else:
        print("✗ Version portable: NON GÉNÉRÉE")

    if installer_exe and installer_exe.exists():
        print(f"✓ Installateur:      {installer_exe.name}")
    else:
        print("⚠ Installateur:      NON GÉNÉRÉ (Inno Setup requis)")

    print()
    print("Build terminé!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild annulé.")
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
