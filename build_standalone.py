#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Standalone Package - Package autonome avec Python et dependances embarques
Cree un package pret a l'emploi sans installation requise (sauf Ollama)
"""

import subprocess
import sys
import os
import shutil
import zipfile
import urllib.request
from pathlib import Path
from datetime import datetime

# Fix encodage console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configuration
APP_NAME = "ChatBotRAG"
APP_VERSION = "1.0.0"
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def print_header(text: str):
    """Affiche un en-tete formate."""
    print("\n" + "=" * 60)
    print(f"   {text}")
    print("=" * 60 + "\n")


def get_project_dir() -> Path:
    """Retourne le repertoire du projet."""
    return Path(__file__).parent


def clean_build_directories():
    """Nettoie les repertoires de build precedents."""
    print("Nettoyage des builds precedents...")
    project_dir = get_project_dir()

    dirs_to_clean = ["build", "dist", "standalone_build", "__pycache__"]

    for dir_name in dirs_to_clean:
        dir_path = project_dir / dir_name
        if dir_path.exists():
            print(f"  Suppression de {dir_name}/")
            shutil.rmtree(dir_path)

    print("  Nettoyage termine!")


def download_file(url: str, dest: Path, description: str = ""):
    """Telecharge un fichier avec progression."""
    print(f"  Telechargement de {description or url}...")

    def reporthook(blocknum, blocksize, totalsize):
        if totalsize > 0:
            percent = min(100, blocknum * blocksize * 100 / totalsize)
            mb_down = blocknum * blocksize / 1024 / 1024
            mb_total = totalsize / 1024 / 1024
            print(f"\r    {percent:.1f}% ({mb_down:.1f}/{mb_total:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook)
    print()  # Nouvelle ligne


def setup_embedded_python(build_dir: Path) -> Path:
    """Telecharge et configure Python embarque."""
    print_header("Configuration de Python embarque")

    python_dir = build_dir / "python"
    python_dir.mkdir(parents=True, exist_ok=True)

    # Telecharge Python embed
    zip_path = build_dir / "python_embed.zip"
    download_file(PYTHON_EMBED_URL, zip_path, "Python 3.11.9 embedded")

    # Extrait
    print("  Extraction de Python...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(python_dir)
    zip_path.unlink()

    # Modifie python311._pth pour activer les imports
    pth_file = python_dir / "python311._pth"
    if pth_file.exists():
        print("  Configuration des chemins Python...")
        content = pth_file.read_text()
        # Decommenter import site
        content = content.replace("#import site", "import site")
        # Ajouter le chemin des packages
        content += "\nLib\\site-packages\n"
        pth_file.write_text(content)

    # Telecharge get-pip.py
    get_pip_path = build_dir / "get-pip.py"
    download_file(GET_PIP_URL, get_pip_path, "get-pip.py")

    # Installe pip
    print("  Installation de pip...")
    python_exe = python_dir / "python.exe"
    result = subprocess.run(
        [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
        capture_output=True,
        text=True,
        cwd=str(python_dir)
    )

    if result.returncode != 0:
        print(f"  ERREUR pip: {result.stderr}")
        # Essai alternatif
        print("  Tentative alternative...")
        result = subprocess.run(
            [str(python_exe), "-m", "ensurepip", "--upgrade"],
            capture_output=True,
            text=True
        )

    get_pip_path.unlink(missing_ok=True)

    print("  Python embarque configure!")
    return python_dir


def install_dependencies(python_dir: Path, project_dir: Path):
    """Installe les dependances dans le Python embarque."""
    print_header("Installation des dependances")

    python_exe = python_dir / "python.exe"
    requirements_file = project_dir / "requirements.txt"

    # Cree le dossier site-packages si necessaire
    site_packages = python_dir / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    # Upgrade pip d'abord
    print("  Mise a jour de pip...")
    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "--no-warn-script-location"],
        capture_output=True
    )

    # Installe les dependances
    print("  Installation des packages (cela peut prendre plusieurs minutes)...")
    print(f"  Fichier requirements: {requirements_file}")

    process = subprocess.Popen(
        [str(python_exe), "-m", "pip", "install", "-r", str(requirements_file),
         "--no-warn-script-location", "--disable-pip-version-check"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            # Filtre les lignes interessantes
            if any(x in line.lower() for x in ["installing", "collecting", "downloading", "successfully"]):
                print(f"    {line[:80]}")
            elif "error" in line.lower():
                print(f"    ERREUR: {line}")

    process.wait()

    if process.returncode == 0:
        print("  Dependances installees avec succes!")
        return True
    else:
        print(f"  ERREUR: Installation echouee (code: {process.returncode})")
        return False


def create_launcher_standalone(build_dir: Path, project_dir: Path):
    """Cree un launcher adapte au package standalone."""
    print("  Creation du launcher standalone...")

    launcher_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatBot RAG Launcher - Version Standalone
Lance l'application avec le Python embarque
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


def show_message_box(title: str, message: str, style: int = 0):
    """Affiche une boite de dialogue Windows."""
    try:
        return ctypes.windll.user32.MessageBoxW(0, message, title, style)
    except:
        print(f"[{title}] {message}")
        return 1


def get_app_directory() -> Path:
    """Retourne le repertoire de l'application."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_python_exe() -> Path:
    """Retourne le chemin vers Python embarque."""
    app_dir = get_app_directory()
    return app_dir / "python" / "python.exe"


def is_ollama_running() -> bool:
    """Verifie si Ollama est en cours d'execution."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((OLLAMA_HOST, OLLAMA_PORT))
        sock.close()
        return result == 0
    except:
        return False


def is_ollama_installed() -> bool:
    """Verifie si Ollama est installe."""
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\\Ollama\\ollama.exe"),
        r"C:\\Program Files\\Ollama\\ollama.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return True
    try:
        result = subprocess.run(["where", "ollama"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def get_ollama_exe_path() -> str:
    """Retourne le chemin vers Ollama."""
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\\Programs\\Ollama\\ollama.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\\Ollama\\ollama.exe"),
        r"C:\\Program Files\\Ollama\\ollama.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return "ollama"


def start_ollama():
    """Demarre Ollama."""
    print("Demarrage d'Ollama...")
    ollama_path = get_ollama_exe_path()

    try:
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

        for i in range(30):
            if is_ollama_running():
                print("  Ollama demarre!")
                return True
            time.sleep(1)
            print(f"  Attente... ({i+1}/30)")

        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False


def check_model_installed() -> bool:
    """Verifie si le modele d'embedding est installe."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            for model in models:
                if "nomic-embed-text" in model:
                    return True
            return False
    except:
        return False


def pull_model():
    """Telecharge le modele d'embedding."""
    print(f"Telechargement du modele {EMBEDDING_MODEL}...")
    ollama_path = get_ollama_exe_path()

    try:
        process = subprocess.Popen(
            [ollama_path, "pull", EMBEDDING_MODEL],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            if line.strip():
                print(f"  {line.strip()}")
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"ERREUR: {e}")
        return False


def download_ollama():
    """Telecharge et lance l'installateur Ollama."""
    response = show_message_box(
        "Ollama requis",
        "Ollama n'est pas installe.\\n\\n"
        "Ollama est necessaire pour les embeddings locaux.\\n\\n"
        "Voulez-vous le telecharger et l'installer?",
        4  # Yes/No
    )

    if response != 6:
        return False

    print("Telechargement d'Ollama...")
    url = "https://ollama.com/download/OllamaSetup.exe"
    installer = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")

    try:
        urllib.request.urlretrieve(url, installer)
        print("Lancement de l'installateur...")
        subprocess.run([installer], check=False)
        time.sleep(2)
        return is_ollama_installed()
    except Exception as e:
        print(f"ERREUR: {e}")
        return False


def launch_streamlit():
    """Lance l'application Streamlit."""
    app_dir = get_app_directory()
    python_exe = get_python_exe()
    app_path = app_dir / "app.py"

    if not python_exe.exists():
        show_message_box("Erreur", f"Python non trouve: {python_exe}", 0)
        return False

    if not app_path.exists():
        show_message_box("Erreur", f"Application non trouvee: {app_path}", 0)
        return False

    print(f"Lancement de l'application...")
    print(f"  Python: {python_exe}")
    print(f"  App: {app_path}")

    os.chdir(app_dir)

    try:
        process = subprocess.Popen(
            [str(python_exe), "-m", "streamlit", "run", str(app_path),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            cwd=str(app_dir)
        )

        print("\\n" + "=" * 50)
        print("L'application demarre...")
        print("Une fenetre de navigateur va s'ouvrir.")
        print("=" * 50)
        print("\\nPour arreter: fermez cette fenetre ou Ctrl+C\\n")

        process.wait()
        return True
    except Exception as e:
        print(f"ERREUR: {e}")
        show_message_box("Erreur", str(e), 0)
        return False


def main():
    print("=" * 50)
    print("   ChatBot RAG - Aristote Dispatcher")
    print("=" * 50)
    print()

    # 1. Verifier Ollama
    print("[1/4] Verification d'Ollama...")
    if not is_ollama_installed():
        if not download_ollama():
            print("\\nOllama est requis. Installez-le depuis: https://ollama.com")
            input("\\nAppuyez sur Entree pour quitter...")
            sys.exit(1)
    print("  Ollama installe.")

    # 2. Demarrer Ollama
    print("\\n[2/4] Demarrage d'Ollama...")
    if not is_ollama_running():
        if not start_ollama():
            show_message_box("Erreur", "Impossible de demarrer Ollama.", 0)
            sys.exit(1)
    print("  Ollama en cours d'execution.")

    # 3. Verifier le modele
    print(f"\\n[3/4] Verification du modele {EMBEDDING_MODEL}...")
    if not check_model_installed():
        if not pull_model():
            show_message_box("Erreur", f"Impossible de telecharger {EMBEDDING_MODEL}", 0)
            sys.exit(1)
    print("  Modele disponible.")

    # 4. Lancer l'app
    print("\\n[4/4] Lancement de l'application...")
    launch_streamlit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\nArret...")
    except Exception as e:
        print(f"\\nERREUR: {e}")
        show_message_box("Erreur", str(e), 0)
        sys.exit(1)
'''

    launcher_path = build_dir / "launcher_standalone.py"
    launcher_path.write_text(launcher_content, encoding='utf-8')
    return launcher_path


def build_exe(build_dir: Path, launcher_path: Path):
    """Construit l'executable du launcher."""
    print_header("Construction de l'executable")

    # Verifie PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("  Installation de PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    print("  Construction de ChatBotRAG.exe...")

    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "ChatBotRAG",
        "--clean", "-y",
        "--distpath", str(build_dir),
        "--workpath", str(build_dir / "pyinstaller_build"),
        "--specpath", str(build_dir / "pyinstaller_build"),
        str(launcher_path)
    ], capture_output=True, text=True)

    exe_path = build_dir / "ChatBotRAG.exe"
    if exe_path.exists():
        print(f"  ChatBotRAG.exe cree ({exe_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return exe_path
    else:
        print(f"  ERREUR: {result.stderr}")
        return None


def create_package(build_dir: Path, project_dir: Path):
    """Cree le package final."""
    print_header("Creation du package final")

    timestamp = datetime.now().strftime("%Y%m%d")
    package_name = f"{APP_NAME}_Standalone_v{APP_VERSION}_{timestamp}"

    dist_dir = project_dir / "dist"
    dist_dir.mkdir(exist_ok=True)

    package_dir = dist_dir / package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()

    print(f"  Package: {package_dir}")

    # Copie Python embarque
    print("  Copie de Python embarque...")
    shutil.copytree(build_dir / "python", package_dir / "python")

    # Copie l'executable
    print("  Copie de l'executable...")
    shutil.copy2(build_dir / "ChatBotRAG.exe", package_dir / "ChatBotRAG.exe")

    # Copie les fichiers sources
    print("  Copie des fichiers sources...")
    files_to_copy = ["app.py", "requirements.txt", ".env.example", "README.md"]
    for f in files_to_copy:
        src = project_dir / f
        if src.exists():
            shutil.copy2(src, package_dir / f)

    # Cree les dossiers
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "chroma_db").mkdir(exist_ok=True)

    # Cree .env depuis template
    env_example = package_dir / ".env.example"
    env_file = package_dir / ".env"
    if env_example.exists() and not env_file.exists():
        shutil.copy2(env_example, env_file)

    # Cree le README d'installation
    readme_install = package_dir / "LISEZMOI.txt"
    readme_install.write_text('''
================================================================================
    ChatBot RAG - Aristote Dispatcher
    Version Standalone (Autonome)
================================================================================

UTILISATION
-----------

1. Double-cliquez sur "ChatBotRAG.exe"

2. Au premier lancement:
   - Si Ollama n'est pas installe, on vous proposera de l'installer
   - Le modele d'embedding sera telecharge si necessaire (~270 MB)

3. L'interface web s'ouvrira dans votre navigateur

4. Entrez votre cle API Aristote dans la barre laterale


CONTENU DU PACKAGE
------------------

ChatBotRAG/
├── ChatBotRAG.exe      <- Double-cliquez ici pour lancer
├── python/             <- Python embarque (ne pas modifier)
├── app.py              <- Application
├── data/               <- Vos documents
└── chroma_db/          <- Base de donnees


PREREQUIS
---------

- Windows 10/11 (64-bit)
- Connexion Internet (pour API Aristote et Ollama)
- Ollama sera installe automatiquement si absent


SUPPORT
-------

En cas de probleme:
- Verifiez votre connexion Internet
- Verifiez qu'Ollama fonctionne (icone dans la barre des taches)
- Relancez ChatBotRAG.exe

================================================================================
''', encoding='utf-8')

    # Cree l'archive ZIP
    print("  Creation de l'archive ZIP...")
    zip_path = dist_dir / f"{package_name}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, f"{package_name}/{arcname}")

    zip_size = zip_path.stat().st_size / 1024 / 1024
    print(f"\n  Archive creee: {zip_path.name} ({zip_size:.1f} MB)")

    return zip_path, package_dir


def main():
    print_header(f"Build Standalone - {APP_NAME} v{APP_VERSION}")

    project_dir = get_project_dir()
    build_dir = project_dir / "standalone_build"
    build_dir.mkdir(exist_ok=True)

    # Nettoyage
    clean_build_directories()
    build_dir.mkdir(exist_ok=True)

    # 1. Python embarque
    python_dir = setup_embedded_python(build_dir)

    # 2. Dependances
    if not install_dependencies(python_dir, project_dir):
        print("\nERREUR: Installation des dependances echouee")
        sys.exit(1)

    # 3. Launcher
    print_header("Preparation du launcher")
    launcher_path = create_launcher_standalone(build_dir, project_dir)

    # 4. Executable
    exe_path = build_exe(build_dir, launcher_path)
    if not exe_path:
        print("\nERREUR: Construction de l'executable echouee")
        sys.exit(1)

    # 5. Package
    zip_path, package_dir = create_package(build_dir, project_dir)

    # Resume
    print_header("Build termine!")
    print(f"Package standalone: {zip_path}")
    print(f"Dossier: {package_dir}")
    print(f"\nTaille: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("\nCe package contient:")
    print("  - Python 3.11 embarque")
    print("  - Toutes les dependances pre-installees")
    print("  - Executable ChatBotRAG.exe")
    print("\nL'utilisateur n'a besoin que d'Ollama!")


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
