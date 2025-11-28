# Prompt Claude Code — Intégration API Albert dans le RAG Chatbot

## Contexte du projet

Tu travailles sur le projet `aristote-rag-chatbot-demo-DRASI`, un chatbot RAG existant qui utilise actuellement :
- **ChromaDB** pour le stockage vectoriel
- **Ollama** pour les embeddings locaux
- **Aristote Dispatcher** (CentraleSupélec) comme LLM

L'objectif est d'intégrer l'**API Albert d'Etalab** comme provider supplémentaire, en exploitant ses capacités spécifiques.

---

## API Albert — Informations techniques

### Endpoint de base
```
https://albert.api.etalab.gouv.fr/v1
```

### Authentification
```
Authorization: Bearer sk-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5MjY0LCJ0b2tlbl9pZCI6NTc1NywiZXhwaXJlc19hdCI6MTc5NTg3MzIyMH0.ksHtaXrlkDpZRirmCxh7BmrjCQnKebEDpQpWCoAnvDs
```

### Modèles disponibles

| Modèle | ID API | Type | Contexte | Cas d'usage |
|--------|--------|------|----------|-------------|
| Albert Small | `albert-small` | text-generation | 64k | Chat rapide, questions simples |
| Albert Large | `albert-large` | image-text-to-text | 128k | Raisonnement complexe, **analyse d'images** |
| Albert Code | `albert-code` | text-generation | 131k | Génération de code |
| Embeddings | `embeddings-small` | text-embeddings | 8k | Vectorisation pour RAG |
| Reranker | `rerank-small` | text-classification | 8k | Reranking des résultats |
| Audio | `audio-large` | speech-recognition | - | Transcription audio |

### Compatibilité
L'API est **100% compatible OpenAI**. Tu peux utiliser le client `openai` Python :

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://albert.api.etalab.gouv.fr/v1",
    api_key="sk-eyJhbGci..."
)
```

---

## Tâches à réaliser

### 1. Abstraction multi-provider pour les embeddings

Créer une classe/module qui permet de basculer entre :
- **Ollama** (local) — comportement actuel
- **Albert embeddings-small** (distant) — nouveau

```python
# Interface souhaitée
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

class OllamaEmbeddings(EmbeddingProvider): ...
class AlbertEmbeddings(EmbeddingProvider): ...
```

**Endpoint Albert pour embeddings :**
```
POST /v1/embeddings
{
    "model": "embeddings-small",
    "input": ["texte 1", "texte 2", ...]
}
```

### 2. Abstraction multi-provider pour le LLM

Permettre le choix entre :
- **Aristote Dispatcher** (existant)
- **Albert** (nouveau) avec sélection du modèle :
  - `albert-small` — rapide
  - `albert-large` — meilleur raisonnement + vision
  - `albert-code` — optimisé code

### 3. Intégration de la vision pour documents complexes

Ajouter une étape optionnelle de pré-traitement des documents :
- Détecter les pages contenant tableaux/graphiques/schémas
- Utiliser `albert-large` en mode vision pour extraire le contenu
- Enrichir le texte avant vectorisation

**Format d'appel vision :**
```python
{
    "model": "albert-large",
    "messages": [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,{base64_encoded_image}"
                }
            },
            {
                "type": "text", 
                "text": "Analyse ce document. Extrais le contenu des tableaux en format structuré et décris les graphiques."
            }
        ]
    }]
}
```

### 4. Reranking optionnel des résultats RAG

Après la recherche ChromaDB, utiliser `rerank-small` pour améliorer la pertinence :

**Endpoint rerank :**
```
POST /v1/rerank  (ou utiliser le format HuggingFace TEI)
{
    "model": "rerank-small",
    "query": "question de l'utilisateur",
    "documents": ["doc1", "doc2", ...]
}
```

### 5. Interface utilisateur

Ajouter dans l'UI (Streamlit ou autre) :
- Sélecteur de provider d'embeddings (Ollama / Albert)
- Sélecteur de LLM (Aristote / Albert-small / Albert-large / Albert-code)
- Toggle pour activer l'analyse vision des documents
- Toggle pour activer le reranking

---

## Architecture cible

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Document (PDF, DOCX, images)                                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Vision Analysis │ ← albert-large (optionnel)                 │
│  │ (tableaux, etc.)│                                            │
│  └────────┬────────┘                                            │
│           ▼                                                     │
│     Texte enrichi                                               │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │   Embeddings    │ ← Ollama (local) OU Albert embeddings-small│
│  └────────┬────────┘                                            │
│           ▼                                                     │
│      ChromaDB                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         QUERY                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Question utilisateur                                           │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │   Embeddings    │ ← même provider que l'ingestion            │
│  └────────┬────────┘                                            │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ ChromaDB Search │                                            │
│  └────────┬────────┘                                            │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │    Reranking    │ ← rerank-small (optionnel)                 │
│  └────────┬────────┘                                            │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │   LLM Response  │ ← Aristote OU Albert (small/large/code)    │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Contraintes et bonnes pratiques

1. **Configuration** : Stocker les clés API et URLs dans un fichier `.env` ou `config.yaml`
2. **Gestion d'erreurs** : Fallback vers le provider local si Albert est indisponible
3. **Cohérence** : Utiliser le MÊME provider d'embeddings pour l'ingestion et la recherche
4. **Logging** : Logger les appels API pour debug et suivi des coûts (même si gratuit)
5. **Tests** : Créer des tests unitaires pour chaque provider
6. **Documentation** : Mettre à jour le README avec les nouvelles options

---

## Fichiers à créer/modifier (suggestions)

```
├── providers/
│   ├── __init__.py
│   ├── embeddings/
│   │   ├── base.py          # Interface abstraite
│   │   ├── ollama.py        # Provider Ollama existant
│   │   └── albert.py        # Nouveau provider Albert
│   ├── llm/
│   │   ├── base.py          # Interface abstraite
│   │   ├── aristote.py      # Provider Aristote existant
│   │   └── albert.py        # Nouveau provider Albert
│   ├── vision/
│   │   └── albert_vision.py # Analyse de documents
│   └── rerank/
│       └── albert_rerank.py # Reranking
├── config.py                 # Configuration centralisée
└── .env                      # Variables d'environnement
```

---

## Pour commencer

1. Analyse d'abord la structure actuelle du projet pour comprendre l'architecture existante
2. Propose un plan d'implémentation par étapes
3. Commence par l'intégration des embeddings Albert (impact minimal sur l'existant)
4. Puis ajoute le provider LLM Albert
5. Ensuite la vision pour documents complexes
6. Enfin le reranking

Demande-moi des clarifications si nécessaire avant de commencer l'implémentation.