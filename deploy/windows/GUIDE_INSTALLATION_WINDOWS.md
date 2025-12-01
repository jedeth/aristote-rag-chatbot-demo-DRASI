# Guide d'Installation Windows

## Aristote RAG Chatbot - Pack Tout-en-Un

Ce guide explique comment créer et distribuer le pack Windows autonome.

---

## Pour le créateur du pack (vous)

### Prérequis machine de build

- Windows 10/11 64 bits
- Connexion Internet
- ~2 Go d'espace disque

### Création du pack

1. **Ouvrir PowerShell** (clic droit sur le menu Démarrer → Terminal)

2. **Aller dans le dossier du projet**
   ```powershell
   cd C:\chemin\vers\aristote-rag-chatbot-demo-DRASI\deploy\windows
   ```

3. **Lancer le build** (nécessite Python installé sur votre machine)
   ```powershell
   python build_windows_pack.py
   ```

4. **Attendre la fin** (5-10 minutes selon la connexion)

5. **Récupérer le pack**
   Le fichier ZIP est créé dans : `dist/ChatBotRAG_Windows_Pack_vX.X.X_YYYYMMDD.zip`

### Distribution

Partagez le fichier ZIP à vos collègues par :
- Email (si taille < limite)
- Partage réseau
- Clé USB
- OneDrive/SharePoint

---

## Pour les utilisateurs finaux

### Installation en 3 clics

#### Étape 1 : Extraire le ZIP

1. Téléchargez le fichier `ChatBotRAG_Windows_Pack_vX.X.X.zip`
2. Clic droit sur le ZIP → **Extraire tout...**
3. Choisissez un emplacement (ex: Bureau ou Documents)
4. Cliquez **Extraire**

#### Étape 2 : Configurer (une seule fois)

1. Ouvrez le dossier `ChatBotRAG`
2. Double-cliquez sur **CONFIGURER.bat**
3. Le Bloc-notes s'ouvre avec le fichier de configuration
4. Remplacez `votre_token_ici` par votre vraie clé API Aristote :
   ```
   ARISTOTE_API_KEY=abc123xyz456...
   ```
5. Sauvegardez (**Ctrl+S**) et fermez

#### Étape 3 : Démarrer

1. Double-cliquez sur **DEMARRER.bat**
2. Une fenêtre noire s'ouvre avec des messages de chargement
3. Votre navigateur s'ouvre automatiquement
4. L'application est prête !

---

## Utilisation quotidienne

### Démarrer l'application
→ Double-cliquez sur **DEMARRER.bat**

### Arrêter l'application
→ Fermez la fenêtre noire (invite de commandes)
→ OU double-cliquez sur **ARRETER.bat**

### Modifier la configuration
→ Double-cliquez sur **CONFIGURER.bat**

---

## Dépannage

### "Windows a protégé votre ordinateur"

C'est normal pour les scripts non signés :
1. Cliquez sur **Informations complémentaires**
2. Cliquez sur **Exécuter quand même**

### L'application ne s'ouvre pas dans le navigateur

Ouvrez manuellement : http://localhost:8501

### "Erreur Ollama" au démarrage

1. Fermez toutes les fenêtres
2. Double-cliquez sur **ARRETER.bat**
3. Attendez 5 secondes
4. Relancez **DEMARRER.bat**

### "Clé API invalide"

1. Double-cliquez sur **CONFIGURER.bat**
2. Vérifiez que la clé est correcte (pas d'espaces avant/après)
3. Sauvegardez et relancez

### Le premier démarrage est très long

C'est normal ! Le premier lancement télécharge le modèle d'embeddings (~270 Mo).
Les démarrages suivants seront beaucoup plus rapides.

---

## Contenu du pack

```
📁 ChatBotRAG/
│
├── 🚀 DEMARRER.bat      ← Lance l'application
├── 🛑 ARRETER.bat       ← Arrête l'application
├── ⚙️ CONFIGURER.bat    ← Modifie la clé API
├── 📖 LISEZ-MOI.txt     ← Guide rapide
│
├── 📁 app/              ← Code de l'application
│   ├── app.py
│   ├── .env             ← Configuration (clé API)
│   ├── data/            ← Documents uploadés
│   └── chroma_db/       ← Base vectorielle
│
├── 📁 python/           ← Python 3.11 embarqué
│   └── (fichiers Python)
│
└── 📁 ollama/           ← Moteur d'embeddings
    └── ollama.exe
```

---

## FAQ

**Q: Dois-je installer Python ?**
R: Non, Python est inclus dans le pack.

**Q: Dois-je installer Ollama ?**
R: Non, Ollama est inclus dans le pack.

**Q: Mes documents restent-ils sur mon PC ?**
R: Oui, tout reste en local dans le dossier `app/data`.

**Q: Puis-je déplacer le dossier ?**
R: Oui, vous pouvez le déplacer où vous voulez.

**Q: Puis-je l'utiliser sans Internet ?**
R: Vous avez besoin d'Internet pour contacter l'API Aristote (le LLM).
Les embeddings (Ollama) fonctionnent hors ligne après le premier démarrage.

---

## Support

En cas de problème, contactez l'équipe DRASI avec :
- Le message d'erreur exact
- Les étapes pour reproduire le problème
