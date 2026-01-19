# Guide de Migration - Nouveaux Modèles Albert API

## 📅 Date limite : 15 février 2026

**Important** : Les anciens alias `albert-*` ne fonctionneront plus après le 15 février 2026.

## 📋 Résumé des changements

Albert API a migré vers une nouvelle gamme de modèles avec des alias plus clairs. Votre projet a été mis à jour pour utiliser les nouveaux alias.

### Correspondance des modèles

| Ancien alias | Nouveau alias | Modèle sous-jacent | Capacités |
|--------------|---------------|-------------------|-----------|
| `albert-large` | `openweight-medium` | mistralai/Mistral-Small-3.2-24B-Instruct-2506 | ✅ Multimodal (vision) |
| `albert-small` | `openweight-small` | mistralai/Ministral-3-8B-Instruct-2512 | Texte uniquement |
| `albert-code` | `openweight-code` | Qwen/Qwen3-Coder-30B-A3B-Instruct | Code |
| N/A | `openweight-large` | openai/gpt-oss-120b | ❌ SANS multimodal |
| `embeddings-small` | `openweight-embeddings` | BAAI/bge-m3 (1024 dim) | Embeddings |
| `rerank-small` | `openweight-rerank` | BAAI/bge-reranker-m3 | Reranking |
| `audio-large` | `openweight-audio` | openai/whisper-large-v3 | Audio (non utilisé) |

## ✅ Choix effectués pour votre projet

**Vous avez choisi : `openweight-medium`** pour remplacer `albert-large`

Raisons :
- ✅ Conserve les capacités multimodales (analyse d'images/tableaux)
- ✅ Compatible avec Albert Vision
- ✅ Meilleur modèle pour votre cas d'usage RAG avec documents visuels

**Alternative non retenue :** `openweight-large` (plus puissant mais perd le multimodal)

## 📝 Fichiers modifiés

### 1. Configuration principale
- ✅ `src/config.py` : ALBERT_LLM_MODEL = `openweight-medium`
- ✅ `.env.example` : Documentation mise à jour

### 2. Adaptateurs d'infrastructure
- ✅ `src/infrastructure/adapters/albert_embedding_adapter.py` : `openweight-embeddings`
- ✅ `src/infrastructure/adapters/albert_llm_adapter.py` :
  - DEFAULT_MODEL = `openweight-medium`
  - AVAILABLE_MODELS = `[openweight-small, openweight-medium, openweight-large, openweight-code]`

### 3. Providers
- ✅ `providers/llm/albert.py` : Modèles LLM mis à jour
- ✅ `providers/embeddings/albert.py` : `openweight-embeddings`
- ✅ `providers/rerank/albert_rerank.py` : `openweight-rerank`
- ✅ `providers/vision/albert_vision.py` : `openweight-medium`

### 4. Applications Streamlit
- ✅ `app.py` : Interface mise à jour avec nouveaux modèles
- ✅ `app_v2.py` : Configuration par défaut mise à jour

### 5. Tests (⚠️ à mettre à jour manuellement si nécessaire)
Les fichiers de tests suivants contiennent encore des références aux anciens modèles :
- `tests/test_vision.py`
- `tests/test_llm.py`
- `tests/test_rerank.py`
- `tests/test_embeddings.py`
- Fichiers de test à la racine : `test_albert*.py`, `test_rag_albert.py`

## 🔧 Actions à effectuer

### Avant de lancer l'application

1. **Mettre à jour votre fichier `.env`** (si vous en avez un) :
   ```bash
   # Ancienne configuration (à supprimer ou commenter)
   # ALBERT_LLM_MODEL=albert-large

   # Nouvelle configuration (recommandé)
   ALBERT_LLM_MODEL=openweight-medium
   ```

2. **Vérifier que vos clés API sont valides** :
   ```bash
   # Vos clés API existantes continueront de fonctionner
   ALBERT_API_KEY=votre_cle_api
   ```

3. **Tester l'application** :
   ```bash
   # Relancer Streamlit
   streamlit run app.py
   # ou
   streamlit run app_v2.py
   ```

### Pendant la période de transition (jusqu'au 15/02/2026)

Les anciens et nouveaux alias cohabiteront. Vous pouvez tester les deux si besoin.

### Après le 15 février 2026

Les anciens alias `albert-*` cesseront de fonctionner. Votre projet est déjà prêt !

## ⚠️ Points d'attention

### 1. Capacités multimodales

- ✅ `openweight-medium` : **supporte la vision** (analyse d'images)
- ❌ `openweight-large` : **ne supporte PAS la vision**

Si vous utilisez l'analyse d'images dans vos documents (PDF, DOCX), restez sur `openweight-medium`.

### 2. Dimensions des embeddings

La dimension reste **1024** pour `openweight-embeddings` (identique à l'ancien `embeddings-small`).
Vos bases de données vectorielles ChromaDB existantes restent compatibles.

### 3. Recherche web

⚠️ La fonctionnalité de recherche web est supprimée à partir du 15/02/2026.
Si vous l'utilisiez, contactez les équipes Albert pour une solution alternative.

## 🚀 Prochaines étapes (optionnel)

1. **Mettre à jour vos tests** : Modifier les fichiers de tests pour utiliser les nouveaux alias
2. **Tester les nouveaux modèles** : Comparer les performances entre `openweight-medium` et `openweight-large`
3. **Mettre à jour votre documentation interne** : Si vous avez des README ou guides mentionnant les anciens modèles

## 📞 Support

- Documentation Albert API : https://albert.api.etalab.gouv.fr
- Questions : Contactez les équipes Albert API

---

✅ **Migration effectuée le** : 2026-01-19
🤖 **Migration automatisée par** : Claude Code
