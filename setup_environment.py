#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Environment - Installation des dépendances et configuration
Script exécuté lors de la première installation ou pour réparer l'environnement
"""

import subprocess
import sys
import os
import venv
import ctypes
from pathlib import Path
import urllib.request
import zipfile
import shutil


def show_message_box(title: str, message: str, style: int = 0):
    """Affiche une boîte de dialogue Windows."""
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)


def get_app_directory() -> Path:
    """Retourne le répertoire de l'application (où se trouve app.py)."""
    if getattr(sys, 'frozen', False):
        # Exécuté depuis un .exe PyInstaller
        exe_dir = Path(sys.executable).parent
    else:
        # Exécuté comme script Python
        exe_dir = Path(__file__).parent

    # Cherche app.py pour identifier le bon répertoire
    # Remonte dans l'arborescence si nécessaire
    current = exe_dir
    for _ in range(10):  # Limite pour éviter boucle infinie
        if (current / "app.py").exists() and (current / "requirements.txt").exists():
            return current
        parent = current.parent
        if parent == current:  # Racine atteinte
            break
        current = parent

    # Si pas trouvé, utilise le répertoire de l'exécutable
    return exe_dir


def create_virtual_environment(app_dir: Path) -> bool:
    """Crée un environnement virtuel Python."""
    venv_dir = app_dir / "venv"

    if venv_dir.exists():
        print("  L'environnement virtuel existe déjà.")
        return True

    print("  Création de l'environnement virtuel...")
    try:
        venv.create(str(venv_dir), with_pip=True)
        print("  Environnement virtuel créé avec succès!")
        return True
    except Exception as e:
        print(f"  ERREUR: {e}")
        return False


def get_venv_python(app_dir: Path) -> str:
    """Retourne le chemin vers Python dans le venv."""
    return str(app_dir / "venv" / "Scripts" / "python.exe")


def get_venv_pip(app_dir: Path) -> str:
    """Retourne le chemin vers pip dans le venv."""
    return str(app_dir / "venv" / "Scripts" / "pip.exe")


def upgrade_pip(app_dir: Path) -> bool:
    """Met à jour pip dans l'environnement virtuel."""
    print("  Mise à jour de pip...")
    python_exe = get_venv_python(app_dir)

    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("  pip mis à jour!")
            return True
        else:
            print(f"  Avertissement: {result.stderr}")
            return True  # Continue même si pip n'a pas pu être mis à jour
    except Exception as e:
        print(f"  Avertissement: {e}")
        return True


def install_requirements(app_dir: Path) -> bool:
    """Installe les dépendances depuis requirements.txt."""
    requirements_file = app_dir / "requirements.txt"

    if not requirements_file.exists():
        print(f"  ERREUR: {requirements_file} non trouvé!")
        return False

    print("  Installation des dépendances...")
    print("  (Cela peut prendre plusieurs minutes)")

    pip_exe = get_venv_pip(app_dir)

    try:
        process = subprocess.Popen(
            [pip_exe, "install", "-r", str(requirements_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            line = line.strip()
            if line and not line.startswith("Using cached"):
                # Simplifie l'affichage
                if "Successfully installed" in line or "Requirement already satisfied" in line:
                    print(f"    {line[:80]}...")
                elif "Installing" in line or "Downloading" in line:
                    print(f"    {line}")

        process.wait()

        if process.returncode == 0:
            print("  Dépendances installées avec succès!")
            return True
        else:
            print(f"  ERREUR: Installation échouée (code: {process.returncode})")
            return False

    except Exception as e:
        print(f"  ERREUR: {e}")
        return False


def verify_installation(app_dir: Path) -> bool:
    """Vérifie que les modules essentiels sont installés."""
    print("  Vérification de l'installation...")

    python_exe = get_venv_python(app_dir)

    modules_to_check = [
        "streamlit",
        "openai",
        "chromadb",
        "ollama",
        "PyMuPDF",  # fitz
        "docx",
    ]

    all_ok = True
    for module in modules_to_check:
        try:
            # Cas spécial pour PyMuPDF qui s'importe comme fitz
            import_name = "fitz" if module == "PyMuPDF" else module

            result = subprocess.run(
                [python_exe, "-c", f"import {import_name}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"    ✓ {module}")
            else:
                print(f"    ✗ {module} - NON INSTALLÉ")
                all_ok = False
        except Exception as e:
            print(f"    ✗ {module} - ERREUR: {e}")
            all_ok = False

    return all_ok


def create_env_file(app_dir: Path):
    """Crée le fichier .env à partir du template si nécessaire."""
    env_file = app_dir / ".env"
    env_example = app_dir / ".env.example"

    if env_file.exists():
        print("  Fichier .env déjà présent.")
        return

    if env_example.exists():
        print("  Création du fichier .env depuis le template...")
        shutil.copy(env_example, env_file)
        print("  Fichier .env créé!")
    else:
        # Crée un fichier .env minimal
        print("  Création d'un fichier .env par défaut...")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# Configuration Aristote Dispatcher\n")
            f.write("ARISTOTE_API_BASE=https://llm.ilaas.fr/v1\n")
            f.write("ARISTOTE_API_KEY=\n")
        print("  Fichier .env créé!")


def create_data_directories(app_dir: Path):
    """Crée les répertoires de données nécessaires."""
    dirs_to_create = [
        app_dir / "data",
        app_dir / "chroma_db",
    ]

    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"    Créé: {dir_path.name}/")


def main():
    """Point d'entrée principal du setup."""
    print("="*60)
    print("   ChatBot RAG - Installation de l'environnement")
    print("="*60)
    print()

    app_dir = get_app_directory()
    print(f"Répertoire d'installation: {app_dir}")
    print()

    # Étape 1: Créer l'environnement virtuel
    print("[1/5] Environnement Python...")
    if not create_virtual_environment(app_dir):
        show_message_box(
            "Erreur d'installation",
            "Impossible de créer l'environnement Python virtuel.\n\n"
            "Vérifiez que Python est correctement installé.",
            0
        )
        return False

    # Étape 2: Mettre à jour pip
    print("\n[2/5] Mise à jour de pip...")
    upgrade_pip(app_dir)

    # Étape 3: Installer les dépendances
    print("\n[3/5] Installation des dépendances Python...")
    if not install_requirements(app_dir):
        show_message_box(
            "Erreur d'installation",
            "Impossible d'installer les dépendances Python.\n\n"
            "Vérifiez votre connexion internet et réessayez.",
            0
        )
        return False

    # Étape 4: Vérifier l'installation
    print("\n[4/5] Vérification de l'installation...")
    if not verify_installation(app_dir):
        response = show_message_box(
            "Avertissement",
            "Certains modules n'ont pas été installés correctement.\n\n"
            "L'application pourrait ne pas fonctionner.\n"
            "Voulez-vous continuer quand même?",
            4  # Yes/No
        )
        if response != 6:  # 6 = Yes
            return False

    # Étape 5: Créer les fichiers/dossiers nécessaires
    print("\n[5/5] Configuration finale...")
    create_env_file(app_dir)
    create_data_directories(app_dir)

    print("\n" + "="*60)
    print("   Installation terminée avec succès!")
    print("="*60)
    print()
    print("Vous pouvez maintenant lancer l'application avec:")
    print("  - ChatBotRAG.exe")
    print("  - ou: python launcher.py")
    print()

    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            show_message_box(
                "Installation réussie",
                "L'environnement a été configuré avec succès!\n\n"
                "Vous pouvez maintenant lancer ChatBotRAG.exe",
                0
            )
        input("\nAppuyez sur Entrée pour fermer...")
    except KeyboardInterrupt:
        print("\n\nInstallation annulée.")
    except Exception as e:
        print(f"\nERREUR FATALE: {e}")
        show_message_box("Erreur", str(e), 0)
        sys.exit(1)
