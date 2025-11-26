# Aristote RAG Chatbot - Demo DRASI

Chatbot intelligent avec RAG (Retrieval-Augmented Generation) utilisant l'API souveraine Aristote.

## Fonctionnalites

- **Connexion a Aristote Dispatcher** : API OpenAI-compatible, selection dynamique des modeles
- **Import de documents** : Support PDF et DOCX
- **Chunking intelligent** : Decoupe avec chevauchement, coupure aux phrases
- **Embeddings locaux** : Ollama (nomic-embed-text) ou sentence-transformers
- **Base vectorielle** : ChromaDB avec similarite cosinus
- **Recherche semantique** : Retrouve les passages pertinents
- **Chat contextuel** : Historique de conversation + injection RAG
- **Mode RAG exclusif** : Anti-hallucination (reponses uniquement depuis les documents)

---

## Installation Rapide (Windows)

### Option 1 : Version Portable (recommandee)

1. **Telecharger** le fichier `ChatBotRAG_Portable_vX.X.X.zip`
2. **Extraire** l'archive dans un dossier de votre choix (ex: `C:\ChatBotRAG`)
3. **Executer** `Setup.exe` pour installer les dependances Python
4. **Lancer** `ChatBotRAG.exe`

### Option 2 : Installateur Windows

1. **Executer** `ChatBotRAG_Setup_X.X.X.exe`
2. **Suivre** l'assistant d'installation
3. **Lancer** depuis le menu Demarrer ou l'icone Bureau

### Premier lancement

Au premier demarrage, `ChatBotRAG.exe` :

1. Verifie si **Ollama** est installe
   - Si absent : propose de le telecharger et l'installer
2. Demarre le service Ollama automatiquement
3. Verifie/telecharge le modele d'embedding `nomic-embed-text:latest` (~270 MB)
4. Lance l'interface web dans votre navigateur

### Configuration

Dans l'interface web (barre laterale gauche) :
1. Entrez votre **cle API Aristote**
2. Selectionnez le **modele** souhaite
3. Ajustez les **parametres RAG** si necessaire

---

## Prerequis

### Pour l'utilisateur final

- **Windows 10/11** (64-bit)
- **Python 3.9+** installe ([Telecharger Python](https://www.python.org/downloads/))
- **Connexion Internet** (pour le setup initial et les appels API)

### Pour le developpement

- Python 3.9+
- [Ollama](https://ollama.ai) (optionnel mais recommande)
- Git

---

## Installation Developpeur

### Avec Ollama (recommande - plus rapide)

```bash
# 1. Installer et lancer Ollama
# Telecharger depuis https://ollama.ai

# 2. Telecharger le modele d'embeddings
ollama pull nomic-embed-text

# 3. Creer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 4. Installer les dependances
pip install -r requirements.txt

# 5. Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec votre token Aristote
```

### Sans Ollama (sentence-transformers en fallback)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt

cp .env.example .env
# Editer .env avec votre token Aristote
```

### Lancement

```bash
streamlit run app.py
```

---

## Creation du Package de Distribution

### Prerequis pour le build

1. **Python 3.9+** avec pip
2. **PyInstaller** (installe automatiquement si absent)
3. **Inno Setup 6** (optionnel, pour l'installateur MSI) - [Telecharger](https://jrsoftware.org/isdl.php)

### Generer les packages

```bash
# Build complet (portable + installateur)
python build_package.py

# Ou seulement les executables
python build_exe.py
```

### Fichiers generes

| Fichier | Description |
|---------|-------------|
| `dist/ChatBotRAG.exe` | Lanceur principal (~8 MB) |
| `dist/Setup.exe` | Installation des dependances (~9 MB) |
| `dist/ChatBotRAG_Portable_vX.X.X.zip` | Archive portable (~17 MB) |
| `installer_output/ChatBotRAG_Setup_X.X.X.exe` | Installateur Windows (~12 MB) |

Voir `BUILD_INSTRUCTIONS.md` pour plus de details.

---

## Structure du Projet

```
aristote-rag-chatbot-demo-DRASI/
|
|-- app.py                    # Application principale Streamlit
|-- launcher.py               # Script de lancement (gestion Ollama)
|-- setup_environment.py      # Installation des dependances
|
|-- requirements.txt          # Dependances Python (production)
|-- requirements-dev.txt      # Dependances Python (developpement)
|-- .env.example              # Template variables d'environnement
|
|-- build_package.py          # Build complet
|-- build_exe.py              # Build executables seuls
|-- ChatBotRAG.spec           # Configuration PyInstaller
|-- installer.iss             # Script Inno Setup
|
|-- data/                     # Documents uploades (cree au runtime)
|-- chroma_db/                # Base vectorielle (cree au runtime)
|-- venv/                     # Environnement Python (cree par setup)
|
|-- README.md                 # Ce fichier
|-- BUILD_INSTRUCTIONS.md     # Guide de build
```

---

## Architecture Technique

```
Utilisateur
    |
    v
ChatBotRAG.exe (launcher)
    |
    |-- Verifie/Installe Ollama
    |-- Demarre Ollama si besoin
    |-- Verifie/Telecharge le modele
    |
    v
Streamlit (app.py)
    |
    |-- Interface web locale
    |-- API Aristote (LLM)
    +-- Ollama (Embeddings locaux)
            |
            v
        ChromaDB (Base vectorielle)
```

### Flux de donnees RAG

1. **Upload document** -> Extraction texte (PDF/DOCX)
2. **Chunking** -> Decoupe en segments avec chevauchement
3. **Embedding** -> Vectorisation via Ollama
4. **Stockage** -> ChromaDB (similarite cosinus)
5. **Question utilisateur** -> Embedding de la question
6. **Recherche** -> Top-K chunks similaires
7. **Prompt augmente** -> Question + contexte documents
8. **Reponse LLM** -> Via API Aristote

---

## Troubleshooting

### Erreur NumPy 2.0 / ChromaDB

Si vous rencontrez l'erreur :
```
AttributeError: `np.float_` was removed in the NumPy 2.0 release
```

**Solution** :
```bash
pip uninstall numpy chromadb -y
pip install "numpy<2.0.0" chromadb==0.5.0
```

### Ollama ne demarre pas

- Verifiez que Ollama est bien installe
- Essayez de le lancer manuellement : `ollama serve`
- Verifiez qu'aucun autre service n'utilise le port 11434

### Erreur de connexion a Aristote

- Verifiez votre cle API dans la barre laterale
- Verifiez votre connexion Internet
- L'API est accessible a : https://llm.ilaas.fr/v1

### MemoryError lors du chunking

Pour les gros documents, augmentez la memoire ou utilisez des fichiers plus petits.

---

## Concepts Cles (pour la demo)

1. **Vibe Coding** : Developpement conversationnel avec l'IA
2. **RAG** : Augmenter le LLM avec des documents prives
3. **Embeddings** : Representation vectorielle du texte
4. **Similarite cosinus** : Mesure de proximite semantique
5. **API souveraine** : Alternative francaise a OpenAI

---

## Documentation Complementaire

- `BUILD_INSTRUCTIONS.md` - Guide complet de build
- `PROMPTS_VIBE_CODING.md` - Prompts pour Claude Code
- `GUIDE_DEMO_VIBE_CODING.md` - Deroule complet de la demo 3h

---

## Licence

Projet de demonstration - DRASI
