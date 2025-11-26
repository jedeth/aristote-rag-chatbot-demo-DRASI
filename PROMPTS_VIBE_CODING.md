# 💬 Prompts Vibe Coding - Aristote RAG Chatbot

Ce fichier contient les prompts à utiliser avec **Claude Code** (CLI) entre chaque étape.

> **Mode d'emploi** : Lancez Claude Code depuis la racine du projet, puis copiez-collez les prompts.
> Les commits existants servent de **backup** si le code généré a des problèmes.

---

## ⚠️ Prérequis Ollama (à vérifier AVANT la démo)

```bash
# 1. Vérifier qu'Ollama tourne
curl http://localhost:11434/api/tags

# 2. Installer le modèle d'embedding si pas fait
ollama pull nomic-embed-text

# 3. Tester un embedding
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Test"
}'
```

---

## 🚀 Lancer Claude Code

```bash
cd aristote-rag-chatbot-demo-DRASI
claude
```

Ensuite, copiez-collez les prompts ci-dessous dans le terminal Claude Code.

---

## 📦 Étape 1 → 2 : Interface Streamlit

**Backup commit** : `189e823`

```
Crée une interface de chatbot avec Streamlit dans app.py.

L'interface doit avoir :
- Configuration de page avec titre "Aristote RAG Chatbot" et icône 🤖
- Un titre principal et un sous-titre "Démo DRASI"
- L'historique des messages stocké dans st.session_state.messages
- Affichage des messages avec st.chat_message
- Un champ de saisie avec st.chat_input
- Pour l'instant une réponse placeholder "Connexion en cours..."
```

**Tester** : `streamlit run app.py`

---

## 🖥️ Étape 2 → 3 : Connexion Aristote

**Backup commit** : `393a206`

```
Ajoute la connexion à l'API Aristote Dispatcher.

L'API est à https://llm.ilaas.fr/v1 et est compatible OpenAI.

Dans la sidebar ajoute :
- Un st.text_input type password pour la clé API (valeur par défaut depuis os.getenv)
- Une fonction get_client() avec @st.cache_resource qui crée le client OpenAI
- Une fonction get_available_models() avec @st.cache_data qui appelle client.models.list()
- Un selectbox pour choisir le modèle parmi ceux disponibles
- Un message de succès quand la connexion fonctionne

Stocke le modèle sélectionné dans st.session_state.selected_model
```

**Tester** : Entrer le token API et voir les modèles apparaître

---

## 🔌 Étape 3 → 4 : Chat fonctionnel

**Backup commit** : `a9ad6b4`

```
Rends le chat fonctionnel.

Quand l'utilisateur envoie un message :
1. Vérifie qu'un modèle est sélectionné
2. Affiche le message utilisateur
3. Ajoute-le à l'historique
4. Appelle client.chat.completions.create avec :
   - Le modèle sélectionné
   - Un system prompt "Tu es un assistant helpful et réponds en français."
   - Tout l'historique des messages
5. Affiche la réponse avec un spinner pendant l'attente
6. Ajoute la réponse à l'historique

Ajoute un bouton "Effacer la conversation" dans la sidebar.
```

**Tester** : Poser quelques questions au chatbot

---

## 💬 Étape 4 → 5 : Upload documents

**Backup commit** : `bf9e480`

```
Ajoute l'upload de documents pour le RAG.

Dans la sidebar, crée une section "Base de connaissances" avec :
- st.header("📚 Base de connaissances")
- st.file_uploader pour PDF et DOCX avec accept_multiple_files=True
- Affichage du nombre de fichiers chargés
- Liste des noms de fichiers
```

---

## 📄 Étape 5 → 6 : Extraction texte

**Backup commit** : `3bfbdf4`

```
Ajoute l'extraction de texte des documents.

Crée ces fonctions :
- extract_text_from_pdf(file_bytes) : utilise fitz (PyMuPDF) pour extraire le texte page par page
- extract_text_from_docx(file_bytes) : utilise python-docx et io.BytesIO
- extract_text(uploaded_file) : dispatch selon l'extension du fichier

Pour chaque fichier uploadé :
- Extraire le texte seulement s'il n'est pas déjà dans session_state.documents_text
- Afficher un aperçu (300 caractères) dans un st.expander
- Afficher le nombre de caractères
```

**Tester** : Charger un PDF et voir le texte extrait

---

## 📝 Étape 6 → 7 : Chunking

**Backup commit** : `ba88d3a`

```
Ajoute le découpage du texte en chunks.

Crée une fonction chunk_text(text, chunk_size=500, overlap=50) qui :
- Découpe le texte en morceaux de chunk_size caractères maximum
- Ajoute un overlap entre les chunks pour la continuité
- Essaie de couper aux fins de phrases (". ", "? ", "! ", "\n")
- Retourne une liste de dicts avec : id, text, start, end

Modifie le traitement pour :
- Créer les chunks après l'extraction
- Stocker text ET chunks dans session_state.documents_text[filename]
- Afficher le nombre de chunks dans l'expander

IMPORTANT - Éviter boucle infinie :
À la fin de la boucle while, s'assurer que start progresse toujours :
  next_start = end - overlap
  if next_start <= start:
      start = start + 1  # Garantir progression
  else:
      start = next_start
```

**⚠️ Bug potentiel** : Sans la vérification ci-dessus, si `overlap >= taille réelle du chunk`, on peut avoir une boucle infinie causant un MemoryError.

---

## ✂️ Étape 7 → 8 : Embeddings avec Ollama 🦙

**Backup commit** : `0faee37` (version sentence-transformers)

```
Ajoute les embeddings avec Ollama.

J'ai Ollama installé localement avec le modèle nomic-embed-text.
La librairie ollama est déjà dans requirements.txt.

Crée ces fonctions :
- get_embedding(text) : 
  import ollama
  response = ollama.embeddings(model="nomic-embed-text", prompt=text)
  return response["embedding"]
  
- create_embeddings(chunks) : pour chaque chunk, génère l'embedding 
  avec get_embedding(chunk["text"]) et l'ajoute dans chunk["embedding"]
  Retourne les chunks enrichis

Après le chunking, appelle create_embeddings avec un spinner "Création des embeddings..."
```

**🔄 Alternative sentence-transformers** (si Ollama pose problème) :

```
Ajoute les embeddings avec sentence-transformers à la place.

Utilise le modèle "paraphrase-multilingual-MiniLM-L12-v2".

Crée :
- get_embedding_model() avec @st.cache_resource qui charge SentenceTransformer
- get_embedding(text) qui utilise model.encode()
- create_embeddings(chunks) qui encode tous les textes et ajoute les embeddings

Affiche un spinner pendant la création.
```

---

## 🧮 Étape 8 → 9 : ChromaDB

**Backup commit** : `bd894e1`

```
Ajoute ChromaDB comme base vectorielle.

Crée :
- get_chroma_collection() avec @st.cache_resource :
  - Client en mémoire avec Settings(anonymized_telemetry=False, allow_reset=True)
  - Collection "documents" avec metadata={"hnsw:space": "cosine"}

- add_to_vectorstore(chunks, filename) :
  - IDs : f"{filename}_{chunk['id']}"
  - Documents : le texte de chaque chunk
  - Embeddings : chunk["embedding"]
  - Metadatas : {"filename": filename, "chunk_id": chunk["id"]}

- search_similar(query, n_results=3) :
  - Crée l'embedding de la query avec get_embedding()
  - Appelle collection.query()
  - Retourne les chunks avec text, metadata, distance

Après create_embeddings, appelle add_to_vectorstore.
Affiche le total de chunks indexés dans la sidebar avec st.success.
```

---

## 🗄️ Étape 9 → 10 : RAG complet

**Backup commit** : `d33aafe`

```
Connecte le RAG au chat.

Avant d'appeler Aristote :
1. Appelle search_similar(prompt, n_results=3)
2. Si des résultats, formate le contexte :
   - Pour chaque chunk : "[Source: {filename}]\n{texte}"
   - Sépare par "\n\n---\n\n"

3. Enrichis le system prompt avec le contexte :
   "Tu es un assistant helpful et réponds en français.
   
   Tu as accès aux documents suivants pour répondre.
   Utilise ces informations et cite tes sources.
   Si l'info n'est pas dans les documents, dis-le clairement.
   
   === DOCUMENTS ===
   {contexte}
   === FIN DES DOCUMENTS ==="

4. Affiche les sources consultées dans un st.expander("📚 Sources consultées") avec :
   - Nom du fichier en gras
   - Score de similarité : 1 - distance (formaté .2f)
   - Aperçu du texte (200 caractères + "...")
```

**Tester** : Charger un document et poser une question sur son contenu

---

## 🧠 Étape 10 → 11 : Polish final

**Backup commit** : `f55f9bd`

```
Ajoute les finitions UX.

Dans un st.expander("⚙️ Paramètres RAG") dans la sidebar :
- st.toggle "Activer le RAG" (défaut True)
- st.slider taille des chunks (200-1000, défaut 500, step 50)
- st.slider chevauchement (0-200, défaut 50, step 10)
- st.slider nombre de sources (1-10, défaut 3)
- Stocke tout dans st.session_state.rag_params

En haut de la page principale, après le titre :
- Si RAG actif et collection.count() > 0 : st.info avec le nombre de chunks
- Si RAG actif et count == 0 : st.warning "Aucun document chargé"
- Si RAG désactivé : st.caption "Mode conversation simple"

Dans la sidebar, après l'affichage des documents :
- Bouton "🔄 Réinitialiser la base" qui :
  - Appelle client.reset() sur ChromaDB
  - Vide session_state.documents_text
  - Appelle st.cache_resource.clear()
  - Appelle st.rerun()

Modifie search_similar pour respecter rag_params["enabled"].
Mets à jour le README avec les fonctionnalités et prérequis Ollama.
```

---

## 🔒 Étape 11 → 12 : Mode RAG exclusif (anti-hallucination)

**Backup commit** : `06e5a4f`

```
Ajoute un mode "RAG exclusif" pour éviter les hallucinations.

Dans les paramètres RAG, ajoute un toggle "🔒 Mode exclusif" :
- Désactivé si RAG désactivé (disabled=not rag_enabled)
- Help : "Si activé, le chatbot ne répond QU'avec les documents"

Stocke rag_params["exclusive"] dans session_state.

Quand ce mode est actif, modifie le system prompt pour être STRICT :
- "Tu ne dois utiliser QUE les informations des documents ci-dessous"
- "Tu ne dois JAMAIS inventer ou utiliser tes connaissances générales"
- "Si l'info n'est pas présente, réponds : 'Cette information n'est pas présente dans les documents'"
- "Cite toujours la source (nom du document)"

Si mode exclusif mais aucun contexte trouvé :
- Affiche st.warning avec message explicatif
- Ajoute un message à l'historique disant qu'aucune info n'a été trouvée
- Ne PAS appeler le LLM

Mets à jour l'indicateur en haut de page :
- Mode exclusif actif : st.warning "🔒 Mode RAG EXCLUSIF - X chunks (réponses uniquement depuis les documents)"
```

**💡 Intérêt pédagogique** : 

Ce mode montre la différence entre :
- **RAG augmenté** : le LLM utilise documents + connaissances générales
- **RAG exclusif** : le LLM utilise UNIQUEMENT les documents (zéro hallucination)

**Démonstration suggérée** :
1. Charger un document sur un sujet précis
2. Poser une question sur le contenu → réponse avec source
3. Poser une question hors sujet → "Information non trouvée"
4. Désactiver le mode exclusif → le LLM répond avec ses connaissances

---

## 🦙 Étape 12 → 14 : Migration vers Ollama (embeddings optimisés)

**Backup commit** : `2b6bf6f`

```
Migre les embeddings de sentence-transformers vers Ollama pour plus de performance.

Prérequis : Ollama doit être lancé avec le modèle nomic-embed-text :
  ollama pull nomic-embed-text
  ollama serve

Modifications à faire :

1. Remplace l'import :
   - Commente : from sentence_transformers import SentenceTransformer
   - Ajoute : import ollama

2. Change le modèle :
   EMBEDDING_MODEL = "nomic-embed-text"

3. Crée une nouvelle fonction get_embedding(text) :
   - response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
   - return response["embedding"]
   - Ajoute gestion d'erreur avec message clair

4. Supprime ou commente get_embedding_model()

5. Modifie create_embeddings(chunks) :
   - Boucle sur chaque chunk
   - chunk["embedding"] = get_embedding(chunk["text"])

6. Modifie search_similar(query) :
   - query_embedding = get_embedding(query)
   - Supprime l'appel à get_embedding_model()

Garde l'ancienne version en commentaire pour référence.
```

**💡 Intérêt pédagogique** :

Cette migration montre comment optimiser progressivement :
- **Avant** (sentence-transformers) : télécharge ~500 Mo, plus lent
- **Après** (Ollama) : instantané, local, même modèle réutilisable

**Avantages Ollama** :
- ⚡ **Performance** : Embeddings instantanés
- 🔒 **Souveraineté** : 100% local, aucun appel externe
- 🎯 **Simplicité** : Un seul modèle partagé pour tous les projets
- 💾 **Économie** : Pas de duplication des modèles Python

**Démonstration suggérée** :
1. Montrer la vitesse avant/après avec un document de test
2. Expliquer que c'est la même qualité d'embeddings
3. Montrer `ollama list` pour voir les modèles disponibles

---

## 🎯 Workflow de la démo

```
┌─────────────────────────────────────────────────────────────┐
│  1. git checkout eb97b5f     ← Point de départ              │
│  2. claude                   ← Lancer Claude Code           │
│  3. [Coller le prompt]       ← Expliquer puis exécuter      │
│  4. streamlit run app.py     ← Tester le résultat           │
│  5. [Expliquer le code]      ← Montrer ce qui a été généré  │
│  6. Passer à l'étape suivante...                            │
└─────────────────────────────────────────────────────────────┘
```

### ⚡ Si le code généré a un bug

```bash
# Option 1 : Demander une correction
claude "J'ai cette erreur : [coller l'erreur]. Corrige le code."

# Option 2 : Utiliser le commit backup
git checkout -- app.py
git checkout <hash_backup>
```

---

## 💡 Commandes Claude Code utiles

| Action | Commande |
|--------|----------|
| Corriger une erreur | `claude "Erreur: [message]. Corrige."` |
| Expliquer le code | `claude "Explique la fonction search_similar"` |
| Voir les fichiers modifiés | `git status` |
| Voir le diff | `git diff app.py` |
| Annuler tout | `git checkout -- .` |
| Committer | `git add -A && git commit -m "message"` |

---

## 📋 Phrases de transition (à dire pendant la démo)

| Étape | Phrase |
|-------|--------|
| 1→2 | "Demandons à Claude de créer l'interface..." |
| 2→3 | "L'interface est prête, connectons-nous à Aristote..." |
| 3→4 | "On est connecté ! Faisons fonctionner le chat..." |
| 4→5 | "Le chatbot marche ! Passons au RAG. Première étape : l'upload..." |
| 5→6 | "On peut charger des fichiers, extrayons le texte..." |
| 6→7 | "Le texte est extrait, découpons-le en chunks..." |
| 7→8 | "Les chunks sont prêts, vectorisons-les avec Ollama..." |
| 8→9 | "On a les embeddings, stockons-les dans ChromaDB..." |
| 9→10 | "La base vectorielle est prête, connectons le RAG au chat..." |
| 10→11 | "Le RAG fonctionne ! Ajoutons les finitions..." |
| 11→12 | "Maintenant, sécurisons les réponses avec le mode exclusif..." |
| 12→14 | "Pour finir, optimisons les performances avec Ollama..." |

---

## 📊 Référence des commits backup

| # | Hash | Étape | Fonctionnalité |
|---|------|-------|----------------|
| 1 | `eb97b5f` | Initial | Structure projet |
| 2 | `189e823` | Interface | Streamlit de base |
| 3 | `393a206` | Connexion | API Aristote |
| 4 | `a9ad6b4` | Chat | Conversation fonctionnelle |
| 5 | `bf9e480` | Upload | Chargement fichiers |
| 6 | `3bfbdf4` | Extraction | PDF/DOCX → texte |
| 7 | `ba88d3a` | Chunking | Découpage en morceaux |
| 8 | `0faee37` | Embeddings | Vectorisation *(sentence-transformers)* |
| 9 | `bd894e1` | ChromaDB | Base vectorielle |
| 10 | `d33aafe` | RAG | Recherche + injection |
| 11 | `f55f9bd` | Polish | Finitions UX |
| 12 | `06e5a4f` | **RAG exclusif** | Anti-hallucination |
| 13 | `dca52ac` | Fix | Compatibilité NumPy < 2.0 |
| 14 | `2b6bf6f` | **Ollama** | Migration embeddings optimisés 🦙 |
| 15 | `07281ce` | **Fix chunking** | Correction boucle infinie ⚠️ |

---

## ⚠️ Bugs connus et correctifs

### Bug 1 : MemoryError dans chunking (Commit 15)

**Symptôme** : `MemoryError` lors du traitement d'un document, l'app freeze

**Cause** : Boucle infinie dans `chunk_text()` si `overlap >= taille réelle du chunk`

**Solution** : Appliquer le commit `07281ce` ou utiliser le code corrigé :
```python
# À la fin de la boucle while dans chunk_text()
next_start = end - overlap
if next_start <= start:
    start = start + 1  # Garantir progression
else:
    start = next_start
```

**Quand l'appliquer** : Dès l'étape 7 si vous rencontrez le problème, ou à la fin de la démo

---

## 🦙 Progression embeddings : sentence-transformers → Ollama

La démo montre une **migration progressive** :
- **Commit 8** : embeddings avec `sentence-transformers` (fonctionne partout)
- **Commit 14** : migration vers `Ollama` (optimisation locale)

| Aspect | sentence-transformers (Commit 8) | Ollama (Commit 14) |
|--------|----------------------------------|---------------------|
| Installation | Télécharge ~500 Mo | Déjà sur ta machine |
| Vitesse premier run | Lent (téléchargement) | Instantané |
| Performance runtime | Bon | Excellent |
| Modèle | paraphrase-multilingual-MiniLM | nomic-embed-text |
| Souveraineté | Local (après download) | 100% local |
| Réutilisation | 1 modèle par projet Python | 1 modèle partagé |

**Intérêt pédagogique** : Montrer qu'on peut optimiser progressivement sans tout refaire !

---

## ✅ Checklist avant la démo

- [ ] Ollama lancé (`ollama serve` ou app desktop)
- [ ] Modèle installé (`ollama pull nomic-embed-text`)
- [ ] Vérification : `curl http://localhost:11434/api/tags`
- [ ] Token Aristote prêt dans `.env`
- [ ] Documents de test (2-3 PDF/DOCX courts)
- [ ] Projet cloné et au commit initial (`git checkout eb97b5f`)
- [ ] Claude Code installé (`npm install -g @anthropic-ai/claude-code`)
- [ ] Ce fichier accessible sur un 2ème écran
