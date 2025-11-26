#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatBot RAG Launcher - Script de lancement principal
Gère le démarrage d'Ollama et lance l'application Streamlit
"""

import subprocess
import sys
import os
import time
import socket
import urllib.request
import json
import ctypes
from pathlib import Path

# Configuration
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
EMBEDDING_MODEL = "nomic-embed-text:latest"
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"


def is_admin():
    """Vérifie si le script s'exécute avec des droits admin."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def show_message_box(title: str, message: str, style: int = 0):
    """
    Affiche une boîte de dialogue Windows.
    Styles: 0=OK, 1=OK/Cancel, 4=Yes/No, 6=Yes/No/Cancel
    Retourne: 1=OK, 2=Cancel, 6=Yes, 7=No
    """
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)


def is_ollama_running() -> bool:
    """Vérifie si Ollama est en cours d'exécution."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((OLLAMA_HOST, OLLAMA_PORT))
        sock.close()
        return result == 0
    except:
        return False


def is_ollama_installed() -> bool:
    """Vérifie si Ollama est installé sur le système."""
    # Chemins possibles pour Ollama sur Windows
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return True

    # Vérifie aussi dans le PATH
    try:
        result = subprocess.run(
            ["where", "ollama"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def get_ollama_exe_path() -> str:
    """Retourne le chemin vers l'exécutable Ollama."""
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Si dans le PATH
    try:
        result = subprocess.run(
            ["where", "ollama"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass

    return "ollama"


def start_ollama():
    """Démarre le service Ollama."""
    print("Démarrage d'Ollama...")
    ollama_path = get_ollama_exe_path()

    # Utilise 'ollama serve' pour démarrer le serveur
    try:
        # Démarre Ollama en arrière-plan sans fenêtre
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.Popen(
            [ollama_path, "serve"],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Attend que Ollama soit prêt
        max_attempts = 30
        for i in range(max_attempts):
            if is_ollama_running():
                print("Ollama démarré avec succès!")
                return True
            time.sleep(1)
            print(f"  Attente du démarrage d'Ollama... ({i+1}/{max_attempts})")

        print("ERREUR: Ollama n'a pas démarré dans le temps imparti.")
        return False

    except Exception as e:
        print(f"ERREUR lors du démarrage d'Ollama: {e}")
        return False


def check_model_installed() -> bool:
    """Vérifie si le modèle d'embedding est installé."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]

            # Vérifie différentes variantes du nom
            model_variants = [
                EMBEDDING_MODEL,
                EMBEDDING_MODEL.replace(":latest", ""),
                "nomic-embed-text",
            ]

            for model in models:
                for variant in model_variants:
                    if variant in model or model in variant:
                        print(f"Modèle trouvé: {model}")
                        return True

            print(f"Modèles installés: {models}")
            return False
    except Exception as e:
        print(f"Erreur lors de la vérification des modèles: {e}")
        return False


def pull_model():
    """Télécharge le modèle d'embedding."""
    print(f"Téléchargement du modèle {EMBEDDING_MODEL}...")
    print("(Cela peut prendre plusieurs minutes selon votre connexion)")

    ollama_path = get_ollama_exe_path()

    try:
        # Exécute ollama pull avec affichage de la progression
        process = subprocess.Popen(
            [ollama_path, "pull", EMBEDDING_MODEL],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Affiche la progression
        for line in process.stdout:
            line = line.strip()
            if line:
                print(f"  {line}")

        process.wait()

        if process.returncode == 0:
            print(f"Modèle {EMBEDDING_MODEL} téléchargé avec succès!")
            return True
        else:
            print(f"ERREUR: Le téléchargement du modèle a échoué (code: {process.returncode})")
            return False

    except Exception as e:
        print(f"ERREUR lors du téléchargement du modèle: {e}")
        return False


def download_ollama_installer():
    """Télécharge l'installateur Ollama."""
    print("Téléchargement de l'installateur Ollama...")

    url = "https://ollama.com/download/OllamaSetup.exe"
    installer_path = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")

    try:
        # Télécharge avec progression
        def reporthook(blocknum, blocksize, totalsize):
            if totalsize > 0:
                percent = min(100, blocknum * blocksize * 100 / totalsize)
                print(f"\r  Progression: {percent:.1f}%", end="", flush=True)

        urllib.request.urlretrieve(url, installer_path, reporthook)
        print()  # Nouvelle ligne après la progression
        return installer_path
    except Exception as e:
        print(f"ERREUR lors du téléchargement: {e}")
        return None


def install_ollama():
    """Installe Ollama avec confirmation utilisateur."""
    response = show_message_box(
        "Installation d'Ollama requise",
        "Ollama n'est pas installé sur ce système.\n\n"
        "Ollama est nécessaire pour générer les embeddings locaux.\n\n"
        "Voulez-vous télécharger et installer Ollama maintenant?",
        4  # Yes/No
    )

    if response != 6:  # 6 = Yes
        print("Installation d'Ollama annulée par l'utilisateur.")
        return False

    installer_path = download_ollama_installer()
    if not installer_path:
        show_message_box(
            "Erreur",
            "Impossible de télécharger l'installateur Ollama.\n"
            "Veuillez l'installer manuellement depuis: https://ollama.com",
            0
        )
        return False

    print("Lancement de l'installateur Ollama...")
    print("Veuillez suivre les instructions de l'installateur.")

    try:
        # Lance l'installateur et attend qu'il se termine
        process = subprocess.run([installer_path], check=False)

        # Vérifie si l'installation a réussi
        time.sleep(2)
        if is_ollama_installed():
            print("Ollama installé avec succès!")

            # Nettoyage de l'installateur
            try:
                os.remove(installer_path)
            except:
                pass

            return True
        else:
            print("L'installation d'Ollama semble avoir échoué.")
            return False

    except Exception as e:
        print(f"ERREUR lors de l'installation: {e}")
        return False


def find_app_directory() -> Path:
    """Trouve le répertoire de l'application (où se trouve app.py)."""
    # Si exécuté depuis un exe PyInstaller
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    # Cherche app.py dans le répertoire courant
    if (base_dir / "app.py").exists():
        return base_dir

    # Remonte dans l'arborescence pour trouver app.py
    current = base_dir
    for _ in range(10):  # Limite pour éviter boucle infinie
        if (current / "app.py").exists() and (current / "requirements.txt").exists():
            return current
        parent = current.parent
        if parent == current:  # Racine atteinte
            break
        current = parent

    # Peut-être dans un sous-dossier
    for subdir in base_dir.iterdir():
        if subdir.is_dir() and (subdir / "app.py").exists():
            return subdir

    return base_dir


def find_python_exe() -> str:
    """Trouve l'exécutable Python à utiliser."""
    app_dir = find_app_directory()

    # Vérifie d'abord le venv local
    venv_python = app_dir / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    # Vérifie un environnement embarqué
    embedded_python = app_dir / "python" / "python.exe"
    if embedded_python.exists():
        return str(embedded_python)

    # Utilise Python du système
    return sys.executable


def launch_streamlit():
    """Lance l'application Streamlit."""
    app_dir = find_app_directory()
    app_path = app_dir / "app.py"

    if not app_path.exists():
        show_message_box(
            "Erreur",
            f"Fichier app.py non trouvé dans:\n{app_dir}\n\n"
            "L'installation semble corrompue.",
            0
        )
        return False

    python_exe = find_python_exe()
    print(f"Utilisation de Python: {python_exe}")
    print(f"Lancement de l'application: {app_path}")

    # Change le répertoire de travail
    os.chdir(app_dir)

    # Lance Streamlit
    try:
        # Essaie d'abord avec le module streamlit
        process = subprocess.Popen(
            [python_exe, "-m", "streamlit", "run", str(app_path),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            cwd=str(app_dir)
        )

        print("\n" + "="*50)
        print("L'application ChatBot RAG démarre...")
        print("Une fenêtre de navigateur va s'ouvrir automatiquement.")
        print("="*50)
        print("\nPour arrêter l'application, fermez cette fenêtre")
        print("ou appuyez sur Ctrl+C\n")

        # Attend que le processus se termine
        process.wait()
        return True

    except Exception as e:
        print(f"ERREUR lors du lancement de Streamlit: {e}")
        show_message_box(
            "Erreur",
            f"Impossible de lancer l'application:\n{e}\n\n"
            "Vérifiez que les dépendances sont installées.",
            0
        )
        return False


def main():
    """Point d'entrée principal."""
    print("="*50)
    print("   ChatBot RAG - Aristote Dispatcher")
    print("="*50)
    print()

    # Étape 1: Vérifier/Installer Ollama
    print("[1/4] Vérification d'Ollama...")
    if not is_ollama_installed():
        print("  Ollama n'est pas installé.")
        if not install_ollama():
            print("\nOllama est requis pour faire fonctionner l'application.")
            print("Veuillez installer Ollama manuellement depuis: https://ollama.com")
            input("\nAppuyez sur Entrée pour quitter...")
            sys.exit(1)
    else:
        print("  Ollama est installé.")

    # Étape 2: Démarrer Ollama si nécessaire
    print("\n[2/4] Vérification du service Ollama...")
    if not is_ollama_running():
        print("  Ollama n'est pas en cours d'exécution.")
        if not start_ollama():
            show_message_box(
                "Erreur",
                "Impossible de démarrer Ollama.\n\n"
                "Essayez de le démarrer manuellement.",
                0
            )
            sys.exit(1)
    else:
        print("  Ollama est déjà en cours d'exécution.")

    # Étape 3: Vérifier/Télécharger le modèle
    print(f"\n[3/4] Vérification du modèle {EMBEDDING_MODEL}...")
    if not check_model_installed():
        print(f"  Le modèle {EMBEDDING_MODEL} n'est pas installé.")
        if not pull_model():
            show_message_box(
                "Erreur",
                f"Impossible de télécharger le modèle {EMBEDDING_MODEL}.\n\n"
                "Vérifiez votre connexion internet et réessayez.",
                0
            )
            sys.exit(1)
    else:
        print(f"  Modèle {EMBEDDING_MODEL} disponible.")

    # Étape 4: Lancer l'application
    print("\n[4/4] Lancement de l'application...")
    launch_streamlit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nArrêt de l'application...")
    except Exception as e:
        print(f"\nERREUR FATALE: {e}")
        show_message_box("Erreur fatale", str(e), 0)
        sys.exit(1)
