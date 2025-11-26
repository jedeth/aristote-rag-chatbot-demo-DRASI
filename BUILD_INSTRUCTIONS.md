# Instructions de Build - ChatBot RAG

Ce document explique comment générer les packages d'installation pour distribuer l'application.

## Prérequis

### Sur la machine de build

1. **Python 3.9+** avec pip
2. **PyInstaller** (installé automatiquement si absent)
3. **Inno Setup 6** (optionnel, pour l'installateur MSI)
   - Télécharger: https://jrsoftware.org/isdl.php
   - Installer dans le chemin par défaut

### Structure requise

Assurez-vous que tous ces fichiers sont présents :

```
aristote-rag-chatbot-demo-DRASI/
├── app.py                    # Application principale
├── requirements.txt          # Dépendances Python
├── .env.example              # Template de configuration
├── launcher.py               # Script de lancement
├── setup_environment.py      # Script d'installation
├── build_package.py          # Script de build principal
├── build_exe.py              # Build des exécutables seuls
├── ChatBotRAG.spec           # Configuration PyInstaller
├── installer.iss             # Script Inno Setup
└── README.md                 # Documentation
```

## Génération des packages

### Option 1 : Build complet (recommandé)

```bash
python build_package.py
```

Ce script génère :
- `dist/ChatBotRAG.exe` - Lanceur principal
- `dist/Setup.exe` - Installation des dépendances
- `dist/ChatBotRAG_Portable_vX.X.X_YYYYMMDD.zip` - Version portable
- `installer_output/ChatBotRAG_Setup_X.X.X.exe` - Installateur Windows (si Inno Setup disponible)

### Option 2 : Exécutables seulement

```bash
python build_exe.py
```

Génère uniquement les .exe dans `dist/`.

### Option 3 : Installateur seul

Si les exécutables sont déjà construits :

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## Personnalisation

### Modifier la version

Éditez ces fichiers :
- `build_package.py` : Variable `APP_VERSION`
- `installer.iss` : Variable `#define MyAppVersion`

### Ajouter une icône

1. Placez votre icône `icon.ico` dans le dossier
2. Décommentez dans `ChatBotRAG.spec` :
   ```python
   # icon='icon.ico',
   ```
3. Décommentez dans `installer.iss` :
   ```
   ; SetupIconFile=icon.ico
   ```

### Modifier l'identifiant de l'application

Dans `installer.iss`, générez un nouveau GUID pour `AppId` :
- PowerShell : `[guid]::NewGuid()`
- Ou utilisez un générateur en ligne

## Distribution

### Version portable (ZIP)

Idéale pour :
- Tests rapides
- Utilisateurs expérimentés
- Environnements sans droits admin

L'utilisateur doit :
1. Extraire l'archive
2. Lancer `Setup.exe` une fois
3. Utiliser `ChatBotRAG.exe` ensuite

### Version installateur (MSI/EXE)

Idéale pour :
- Déploiement professionnel
- Utilisateurs non techniques
- Installation propre avec désinstallateur

L'installateur :
1. Vérifie Python
2. Copie les fichiers
3. Crée les raccourcis
4. Propose de configurer l'environnement

## Dépannage

### PyInstaller échoue

```bash
pip install --upgrade pyinstaller
```

### Inno Setup non trouvé

Vérifiez le chemin dans `build_package.py` :
```python
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

### Exécutable trop volumineux

Le launcher est conçu pour être léger (~8 MB). Si plus gros :
- Vérifiez les exclusions dans `ChatBotRAG.spec`
- Utilisez UPX pour compresser

### Antivirus bloque l'exécutable

Comportement normal pour les .exe générés par PyInstaller.
Solutions :
- Signer le code avec un certificat
- Ajouter une exception antivirus
- Distribuer le code source

## Notes techniques

### Architecture

```
Utilisateur
    │
    ▼
ChatBotRAG.exe (launcher)
    │
    ├── Vérifie/Installe Ollama
    ├── Démarre Ollama si besoin
    ├── Vérifie/Télécharge le modèle
    │
    ▼
Streamlit (app.py)
    │
    ├── Interface web
    ├── API Aristote
    └── Embeddings Ollama
```

### Flux d'installation

```
Setup.exe
    │
    ├── Crée venv/
    ├── pip install requirements.txt
    ├── Vérifie les modules
    └── Crée .env depuis .env.example
```

### Taille estimée des packages

| Package | Taille |
|---------|--------|
| ChatBotRAG.exe | ~8 MB |
| Setup.exe | ~8 MB |
| ZIP portable | ~15 MB |
| Installateur | ~12 MB |
| venv installé | ~500 MB |
| Modèle Ollama | ~270 MB |
