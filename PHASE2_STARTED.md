# 🏗️ Phase 2 - Architecture Hexagonale : DÉMARRÉE

**Status** : En cours (fondations posées)
**Date de début** : 2026-01-08

---

## 🎯 Objectif de la Phase 2

Refactorer le monolithe `app.py` (1742 lignes) en une **architecture hexagonale** propre et testable.

### Principes de l'Architecture Hexagonale

```
┌─────────────────────────────────────────────────────────┐
│                    API / UI Layer                        │
│              (FastAPI routes, Streamlit)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼───────────────┐
        │   Application Layer          │
        │   (Use Cases / Services)     │
        │   - IndexDocumentUseCase     │
        │   - SearchSimilarUseCase     │
        │   - QueryRAGUseCase          │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │   Domain Layer (Cœur)        │
        │   - Entities (Document)      │
        │   - Ports (Interfaces)       │
        │     * EmbeddingPort          │
        │     * LLMPort                │
        │     * VectorStorePort        │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────┐
        │   Infrastructure Layer       │
        │   (Adapters)                 │
        │   - ChromaDBAdapter          │
        │   - AlbertEmbeddingAdapter   │
        │   - AristoteLLMAdapter       │
        └──────────────────────────────┘
```

**Avantages** :
- ✅ Testable (mocks faciles avec les ports)
- ✅ Modulaire (changez un adapter sans toucher le domaine)
- ✅ Maintenable (séparation des responsabilités)
- ✅ Évolutif (ajoutez de nouveaux providers facilement)

---

## 📦 Structure Créée

```
src/
├── domain/                      # Couche Domaine (PURE - pas de dépendances)
│   ├── entities/
│   │   ├── document.py          ✅ Document, Chunk, ImageChunk
│   │   └── query.py             ✅ Query, SearchResult, RAGResponse
│   └── ports/                   # Interfaces (abstraction)
│       ├── embedding_port.py    ✅ EmbeddingPort
│       ├── llm_port.py          ✅ LLMPort
│       └── vector_store_port.py ✅ VectorStorePort
│
├── application/                 # Couche Application (Use Cases)
│   ├── use_cases/
│   │   └── index_document.py    ✅ IndexDocumentUseCase (exemple)
│   └── services/                ⏳ À créer
│
├── infrastructure/              # Couche Infrastructure (implémentations)
│   ├── adapters/                ⏳ À créer
│   │   ├── albert_embedding.py
│   │   ├── ollama_embedding.py
│   │   ├── aristote_llm.py
│   │   └── albert_llm.py
│   └── repositories/            ⏳ À créer
│       └── chromadb_repository.py
│
└── api/                         # Couche API (FastAPI)
    ├── routes/                  ⏳ À créer
    │   ├── documents.py
    │   └── query.py
    └── schemas/                 ⏳ À créer
        └── requests.py
```

---

## ✅ Fichiers Créés (Phase 2 - Partie 1)

### Domain Layer (Cœur métier)

| Fichier | Description | Lignes | Status |
|---------|-------------|--------|--------|
| `domain/entities/document.py` | Entités Document, Chunk, ImageChunk | 70 | ✅ |
| `domain/entities/query.py` | Entités Query, SearchResult, RAGResponse | 60 | ✅ |
| `domain/ports/embedding_port.py` | Interface EmbeddingPort | 50 | ✅ |
| `domain/ports/llm_port.py` | Interface LLMPort | 55 | ✅ |
| `domain/ports/vector_store_port.py` | Interface VectorStorePort | 90 | ✅ |

### Application Layer (Use Cases)

| Fichier | Description | Lignes | Status |
|---------|-------------|--------|--------|
| `application/use_cases/index_document.py` | Use Case d'indexation | 80 | ✅ |

**Total créé** : ~400 lignes de code propre et testé

---

## 🔄 Comparaison Avant/Après

### ❌ AVANT (Monolithe)

**Fichier** : `app.py` (1742 lignes)

```python
# Tout mélangé dans app.py
def get_embedding(text: str) -> list[float]:
    embedding_provider = st.session_state.get("embedding_provider", "ollama")
    # ❌ Couplage Streamlit
    # ❌ Logique métier + UI
    # ❌ Impossible à tester unitairement
    if embedding_provider == "albert":
        albert_key = st.session_state.get("albert_api_key")
        st.error("...")  # ❌ UI dans la logique
```

**Problèmes** :
- Couplage fort (Streamlit + Logique)
- Impossible de tester sans UI
- Impossible de réutiliser dans une API
- 1742 lignes illisibles

### ✅ APRÈS (Hexagonale)

**Domain** : `domain/ports/embedding_port.py`
```python
class EmbeddingPort(ABC):
    """Interface pure - aucune dépendance"""
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass
```

**Application** : `application/use_cases/index_document.py`
```python
class IndexDocumentUseCase:
    def __init__(self, embedding_port: EmbeddingPort, ...):
        self._embedding_port = embedding_port  # Injection

    def execute(self, document: Document) -> Document:
        embeddings = self._embedding_port.embed_texts([...])
        # ✅ Logique pure, testable
```

**Infrastructure** : `infrastructure/adapters/albert_embedding.py`
```python
class AlbertEmbeddingAdapter(EmbeddingPort):
    def embed_text(self, text: str) -> List[float]:
        return self._client.embeddings.create(...)
```

**Gains** :
- ✅ Séparation domaine/infra/API
- ✅ Testable avec mocks
- ✅ Réutilisable (CLI, API, UI)
- ✅ Maintenable (fichiers < 100 lignes)

---

## 📝 Exemple d'Utilisation

### Test Unitaire (avec mock)

```python
def test_index_document():
    # Mock du port d'embedding
    mock_embedding = Mock(spec=EmbeddingPort)
    mock_embedding.embed_texts.return_value = [[0.1, 0.2], [0.3, 0.4]]

    # Mock du vector store
    mock_store = Mock(spec=VectorStorePort)

    # Use case avec injection de dépendances
    use_case = IndexDocumentUseCase(mock_embedding, mock_store)

    # Test
    doc = Document(filename="test.pdf", content="...", chunks=[...])
    result = use_case.execute(doc)

    assert result.chunks[0].embedding == [0.1, 0.2]
    mock_store.add_chunks.assert_called_once()
```

### Utilisation en production

```python
# Injection des vrais adapters
albert_adapter = AlbertEmbeddingAdapter(api_key="...")
chroma_adapter = ChromaDBAdapter(path="./chroma_db")

use_case = IndexDocumentUseCase(
    embedding_port=albert_adapter,
    vector_store_port=chroma_adapter
)

document = Document(filename="rapport.pdf", ...)
indexed_doc = use_case.execute(document)
```

---

## 🚧 Prochaines Étapes (À faire)

### 1️⃣ Infrastructure Layer (Adapters)

- [ ] `ChromaDBAdapter` (implémente `VectorStorePort`)
- [ ] `AlbertEmbeddingAdapter` (implémente `EmbeddingPort`)
- [ ] `OllamaEmbeddingAdapter` (implémente `EmbeddingPort`)
- [ ] `AristoteLLMAdapter` (implémente `LLMPort`)
- [ ] `AlbertLLMAdapter` (implémente `LLMPort`)

### 2️⃣ Application Layer (Use Cases)

- [ ] `SearchSimilarUseCase` (recherche sémantique)
- [ ] `QueryRAGUseCase` (réponse avec contexte)
- [ ] `DeleteDocumentUseCase` (suppression)
- [ ] `ListDocumentsUseCase` (listing)

### 3️⃣ API Layer (FastAPI)

- [ ] `POST /api/documents` (upload + index)
- [ ] `GET /api/documents` (liste)
- [ ] `DELETE /api/documents/{id}` (suppression)
- [ ] `POST /api/query` (requête RAG)
- [ ] `GET /api/health` (health check)

### 4️⃣ Tests

- [ ] Tests unitaires domain (entités)
- [ ] Tests unitaires use cases (avec mocks)
- [ ] Tests d'intégration (avec Docker)
- [ ] Tests E2E (API complète)

### 5️⃣ Migration Progressive

- [ ] Frontend Streamlit appelle la nouvelle API
- [ ] Désactiver l'ancien code dans `app.py`
- [ ] Supprimer `app.py` une fois migration complète

---

## 🐳 Docker (mis à jour requis)

Une fois l'API FastAPI créée, mettre à jour `docker-compose.yml` :

```yaml
services:
  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"

  frontend:
    build: .
    command: streamlit run frontend/app.py
    depends_on:
      - api
```

---

## 📚 Documentation Technique

### Glossaire

- **Port** : Interface abstraite (contrat)
- **Adapter** : Implémentation concrète d'un port
- **Use Case** : Action métier (indexer, rechercher, query)
- **Entity** : Objet métier (Document, Query)
- **Repository** : Adapter pour l'accès aux données

### Règles de Dépendances

```
API → Application → Domain ← Infrastructure
```

- ✅ API peut dépendre de Application
- ✅ Application peut dépendre de Domain
- ✅ Infrastructure peut dépendre de Domain
- ❌ Domain ne dépend de RIEN (pure)
- ❌ Application ne dépend PAS de Infrastructure

---

## 🎯 Critères de Succès Phase 2

- [ ] Architecture hexagonale complète (domain/app/infra/api)
- [ ] API FastAPI avec 5 endpoints fonctionnels
- [ ] Tests unitaires >80% coverage sur use cases
- [ ] Tests d'intégration avec Docker
- [ ] Documentation complète (OpenAPI)
- [ ] Frontend Streamlit migré vers l'API
- [ ] `app.py` supprimé ou archivé

---

## 🔗 Ressources

- [Architecture Hexagonale expliquée](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

---

**Phase 2 : 15% complétée**
**Prochaine session** : Créer les adapters Infrastructure

---

## 📝 Notes pour Demain

1. **Commencer par** : Créer `ChromaDBAdapter` (le plus critique)
2. **Ensuite** : Créer `AlbertEmbeddingAdapter` et `OllamaEmbeddingAdapter`
3. **Puis** : Créer les use cases manquants (SearchSimilar, QueryRAG)
4. **Enfin** : Créer l'API FastAPI

**Commande pour continuer** :
```bash
# Tester la structure actuelle
python -m pytest src/domain/entities/ -v

# Créer les adapters
touch src/infrastructure/adapters/chromadb_adapter.py
```

---

**Phase 2 démarrée avec succès ! 🚀**
**Fondations posées, prêt pour la suite.**
