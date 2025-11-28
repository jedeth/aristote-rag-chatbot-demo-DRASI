# Notes de Développement - Intégration Albert API

**Date**: 28 novembre 2025
**Projet**: aristote-rag-chatbot-demo-DRASI
**Objectif**: Intégration de l'API Albert (Etalab) comme alternative aux providers existants

---

## Résumé de la session

### Ce qui a été fait

1. **Architecture multi-provider créée** (`providers/`)
   - `embeddings/base.py` : Classe abstraite `EmbeddingProvider`
   - `embeddings/ollama.py` : Provider Ollama local (nomic-embed-text, 768 dim)
   - `embeddings/albert.py` : Provider Albert cloud (embeddings-small, 1024 dim)
   - `llm/base.py` : Classe abstraite `LLMProvider`
   - `llm/aristote.py` : Provider Aristote DRASI
   - `llm/albert.py` : Provider Albert (albert-small, albert-large, albert-code)
   - `rerank/albert_rerank.py` : Reranking avec rerank-small
   - `vision/albert_vision.py` : Vision avec albert-large multimodal
   - `vision/pdf_image_extractor.py` : Extraction d'images des PDFs

2. **Application `app_v2.py` créée**
   - Interface multi-provider avec sélection dans le sidebar
   - Gestion des clés API (Aristote + Albert)
   - Mode RAG exclusif adapté par provider
   - Barre de progression pour l'indexation
   - Mode développement avec `dev_config.json`

3. **Système de configuration dev**
   - Fichier `dev_config.json` pour stocker les clés API localement
   - Pop-up d'alerte "MODE DÉVELOPPEMENT" dans l'UI
   - Bouton pour sauvegarder les clés

---

## Limites de l'API Albert (documentation officielle)

| Modèle | RPM | RPD | TPM | TPD |
|--------|-----|-----|-----|-----|
| albert-code | 50 | 1000 | 128000 | 2460000 |
| albert-large | 50 | 1000 | 128000 | 2460000 |
| albert-small | 50 | 1000 | 128000 | 2460000 |
| audio-large | 50 | 1000 | Unlimited | Unlimited |
| **embeddings-small** | **500** | **50000** | **Unlimited** | **Unlimited** |
| **rerank-small** | **500** | **50000** | **Unlimited** | **Unlimited** |
| web-search | Unlimited | Unlimited | Unlimited | Unlimited |

**URL de base**: `https://albert.api.etalab.gouv.fr/v1`

---

## Problèmes résolus

### 1. Erreur `encoding_format='base64'`
**Symptôme**: `Error code: 422 - Input should be 'float'`
**Cause**: Le client OpenAI Python envoie `encoding_format='base64'` par défaut
**Solution**: Utiliser `requests` directement au lieu du client OpenAI pour les embeddings

```python
# providers/embeddings/albert.py
response = requests.post(
    f"{self._base_url}/embeddings",
    headers={"Authorization": f"Bearer {self._api_key}"},
    json={
        "model": self._model,
        "input": input_data,
        "encoding_format": "float",  # Explicitement float
    },
)
```

### 2. Dimensions d'embeddings incompatibles
**Symptôme**: Erreur ChromaDB quand on change de provider
**Cause**: Ollama (768 dim) vs Albert (1024 dim)
**Solution**: Collections séparées par provider

```python
# Collection nommée avec suffixe du provider
collection_name = f"documents_v2_{embedding_provider}"  # documents_v2_ollama ou documents_v2_albert
```

### 3. Indexation lente des gros documents
**Symptôme**: Timeout ou lenteur avec PDF de 2.5 Mo
**Solution**:
- Traitement par batch (50 textes par requête)
- Utilisation de `embed_documents()` au lieu de boucle sur `embed_query()`
- Barre de progression dans l'UI

### 4. Dimension embeddings Albert incorrecte
**Corrigé**: 1024 (et non 1536 comme initialement supposé)

---

## Problème NON résolu : RAG exclusif avec Albert

### Symptôme
En mode RAG exclusif, Albert répond systématiquement :
> "Cette information n'est pas présente dans les documents fournis."

Même quand les sources sont trouvées avec de bons scores.

### Diagnostic effectué
- Test direct de l'API Albert avec contexte RAG : **FONCTIONNE** (voir `test_albert_rag.py`)
- Le problème est donc dans l'application, pas dans l'API

### Pistes à explorer
1. **Vérifier le contenu des chunks récupérés** - Les sources affichées contiennent-elles vraiment l'information ?
2. **Vérifier que le contexte est bien passé** - Mode debug ajouté (expander "Debug: Contexte envoyé au LLM")
3. **Problème potentiel avec l'historique** - Le code ajoute l'historique des messages, peut-être trop long ?
4. **Reranking qui filtre trop** - Désactiver le reranking pour tester

### Code de test fonctionnel
```python
# test_albert_rag.py - Ce format fonctionne !
messages = [
    {"role": "user", "content": f"""Voici des extraits de documents :

{CONTEXT}

Question : {QUESTION}

Réponds à la question en te basant sur les documents ci-dessus."""}
]
```

---

## Fichiers créés/modifiés

### Nouveaux fichiers
```
providers/
├── __init__.py
├── embeddings/
│   ├── __init__.py
│   ├── base.py
│   ├── ollama.py
│   └── albert.py
├── llm/
│   ├── __init__.py
│   ├── base.py
│   ├── aristote.py
│   └── albert.py
├── rerank/
│   ├── __init__.py
│   └── albert_rerank.py
└── vision/
    ├── __init__.py
    ├── albert_vision.py
    └── pdf_image_extractor.py

app_v2.py                    # Application principale multi-provider
dev_config.json              # Configuration dev avec clés API
test_albert_embeddings.py    # Test API embeddings
test_albert_rag.py           # Test RAG avec Albert
NOTES_DEV_ALBERT_INTEGRATION.md  # Ce fichier
```

### Fichiers existants non modifiés
- `app.py` - Application originale (inchangée, option B choisie)

---

## Configuration dev_config.json

```json
{
    "_comment": "FICHIER DE DEVELOPPEMENT UNIQUEMENT - NE PAS COMMITER EN PRODUCTION",
    "dev_mode": true,
    "api_keys": {
        "aristote_api_key": "drasi-xxx-xxx",
        "aristote_api_url": "https://llm.ilaas.fr/v1",
        "albert_api_key": "sk-eyJhbGci..."
    },
    "default_providers": {
        "embeddings": "ollama",
        "llm": "aristote"
    }
}
```

---

## Pour reprendre le développement

### 1. Lancer l'application
```bash
cd aristote-rag-chatbot-demo-DRASI
.\venv\Scripts\activate
streamlit run app_v2.py
```

### 2. Priorité : Débugger le RAG exclusif avec Albert
- Ouvrir l'expander "Debug: Contexte envoyé au LLM"
- Vérifier que le contexte contient l'information recherchée
- Comparer avec le format qui fonctionne dans `test_albert_rag.py`

### 3. Tests disponibles
```bash
python test_albert_embeddings.py  # Teste l'API embeddings
python test_albert_rag.py         # Teste le RAG (fonctionne !)
```

---

## Remarques importantes

1. **Ne pas utiliser le client OpenAI pour les embeddings Albert** - Utiliser requests directement
2. **Les collections ChromaDB sont séparées par provider** - Réindexer si changement de provider
3. **Albert fonctionne bien pour le RAG** (prouvé par test_albert_rag.py) - Le bug est côté app
4. **Mode dev** : Mettre `"dev_mode": false` avant déploiement

---

## Contact / Ressources

- API Albert : https://albert.api.etalab.gouv.fr
- Documentation Albert : https://albert.api.etalab.gouv.fr/documentation
- Aristote DRASI : https://llm.ilaas.fr
