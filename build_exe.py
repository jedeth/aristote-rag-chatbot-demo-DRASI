#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script - Génère les exécutables avec PyInstaller
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil


def check_pyinstaller():
    """Vérifie que PyInstaller est installé."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller n'est pas installé.")
        print("Installation en cours...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True


def build_launcher():
    """Construit l'exécutable du launcher."""
    print("\n" + "="*50)
    print("Construction de ChatBotRAG.exe...")
    print("="*50)

    script_dir = Path(__file__).parent
    spec_file = script_dir / "ChatBotRAG.spec"

    # Nettoie les builds précédents
    for dir_name in ["build", "dist"]:
        dir_path = script_dir / dir_name
        if dir_path.exists():
            print(f"Nettoyage de {dir_name}/...")
            shutil.rmtree(dir_path)

    # Construit avec le fichier spec
    if spec_file.exists():
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]
    else:
        # Construction directe si pas de fichier spec
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--console",
            "--name", "ChatBotRAG",
            "--clean",
            str(script_dir / "launcher.py")
        ]

    print(f"Commande: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(script_dir))

    if result.returncode == 0:
        exe_path = script_dir / "dist" / "ChatBotRAG.exe"
        if exe_path.exists():
            print(f"\nSuccès! Exécutable créé: {exe_path}")
            print(f"Taille: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
            return exe_path
        else:
            print("ERREUR: L'exécutable n'a pas été créé.")
            return None
    else:
        print(f"ERREUR: PyInstaller a échoué (code: {result.returncode})")
        return None


def build_setup():
    """Construit l'exécutable du setup."""
    print("\n" + "="*50)
    print("Construction de Setup.exe...")
    print("="*50)

    script_dir = Path(__file__).parent

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "Setup",
        "--clean",
        str(script_dir / "setup_environment.py")
    ]

    result = subprocess.run(cmd, cwd=str(script_dir))

    if result.returncode == 0:
        exe_path = script_dir / "dist" / "Setup.exe"
        if exe_path.exists():
            print(f"\nSuccès! Exécutable créé: {exe_path}")
            return exe_path
        else:
            print("ERREUR: L'exécutable n'a pas été créé.")
            return None
    else:
        print(f"ERREUR: PyInstaller a échoué (code: {result.returncode})")
        return None


def main():
    print("="*60)
    print("   Build des exécutables ChatBot RAG")
    print("="*60)

    # Vérifie PyInstaller
    if not check_pyinstaller():
        print("Impossible d'installer PyInstaller.")
        sys.exit(1)

    # Construit le launcher
    launcher_exe = build_launcher()

    # Construit le setup
    setup_exe = build_setup()

    print("\n" + "="*60)
    print("   Résumé du build")
    print("="*60)

    if launcher_exe:
        print(f"✓ ChatBotRAG.exe: {launcher_exe}")
    else:
        print("✗ ChatBotRAG.exe: ÉCHEC")

    if setup_exe:
        print(f"✓ Setup.exe: {setup_exe}")
    else:
        print("✗ Setup.exe: ÉCHEC")

    print()
    if launcher_exe and setup_exe:
        print("Build terminé avec succès!")
        print(f"\nLes exécutables sont dans: {Path(__file__).parent / 'dist'}")
    else:
        print("Le build a rencontré des erreurs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
