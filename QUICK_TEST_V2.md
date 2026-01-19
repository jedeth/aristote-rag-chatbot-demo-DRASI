# 🚀 Guide Rapide : Tester la V2 (Architecture Hexagonale)

**Date** : 2026-01-12
**Objectif** : Tester rapidement la nouvelle architecture hexagonale

---

## ⚡ Test Rapide (5 minutes)

### Prérequis

```bash
# S'assurer que V1 tourne (pour ta démo)
docker compose ps | grep aristote

# Si V1 tourne, tu peux lancer V2 en parallèle
# V1 : port 8501
# V2 : ports 8000 + 8502
```

### Option 1 : Lancer V2 en Docker (Recommandé)

```bash
# 1. Configurer les variables d'environnement
cp .env.docker .env.v2
nano .env.v2  # Vérifier les clés API

# 2. Lancer V2
./docker-manage-v2.sh start

# 3. Vérifier les services
docker compose -f docker-compose-v2.yml ps

# Expected output:
# NAME              STATUS    PORTS
# aristote-api-v2   running   0.0.0.0:8000->8000/tcp
# aristote-ui-v2    running   0.0.0.0:8502->8502/tcp
# aristote-caddy-v2 running   0.0.0.0:80->80/tcp
```

### Option 2 : Lancer V2 en Local (Plus Rapide)

```bash
# 1. Créer un environnement virtuel (si pas fait)
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements-api.txt

# 3. Configurer les variables
export ARISTOTE_API_KEY="drasi-idf-1-xxx"
export ALBERT_API_KEY="sk-xxx"
export CHROMA_DB_PATH="./chroma_db"

# 4. Lancer l'API (Terminal 1)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Lancer le Frontend (Terminal 2)
streamlit run frontend/app_v2.py --server.port 8502
```

---

## 🧪 Tests à Effectuer

### Test 1 : Health Check API ✅

```bash
# Test API disponible
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   "architecture": "hexagonal"
# }
```

### Test 2 : Documentation Interactive ✅

```bash
# Ouvrir Swagger UI dans le navigateur
xdg-open http://localhost:8000/docs

# Ou ReDoc
xdg-open http://localhost:8000/redoc
```

### Test 3 : Upload d'un Document ✅

```bash
# Créer un fichier test
echo "Ceci est un document de test pour l'architecture hexagonale." > test_doc.txt

# Upload via API
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test_doc.txt"

# Expected output:
# {
#   "document_id": "xxx",
#   "filename": "test_doc.txt",
#   "chunks_count": 1,
#   "message": "Document 'test_doc.txt' indexé avec succès"
# }
```

### Test 4 : Lister les Documents ✅

```bash
# Liste tous les documents
curl http://localhost:8000/documents

# Expected output:
# {
#   "documents": [
#     {
#       "document_id": "xxx",
#       "filename": "test_doc.txt",
#       "chunks_count": 1,
#       "indexed_at": "2026-01-12T..."
#     }
#   ],
#   "total_count": 1
# }
```

### Test 5 : Requête RAG ✅

```bash
# Poser une question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Que contient le document ?",
    "n_results": 3,
    "temperature": 0.7,
    "llm_provider": "aristote",
    "embedding_provider": "ollama"
  }'

# Expected output:
# {
#   "query_id": "xxx",
#   "query_text": "Que contient le document ?",
#   "response_text": "Le document contient...",
#   "sources": [...],
#   "model_name": "meta-llama/Llama-3.3-70B-Instruct",
#   "created_at": "2026-01-12T..."
# }
```

### Test 6 : Frontend Streamlit ✅

```bash
# Ouvrir le frontend V2
xdg-open http://localhost:8502

# Actions à tester dans l'interface :
# 1. Uploader un document PDF/DOCX/TXT
# 2. Voir la liste des documents dans la sidebar
# 3. Changer le provider LLM (aristote/albert)
# 4. Changer le provider embeddings (ollama/albert)
# 5. Poser une question dans le chat
# 6. Vérifier les sources affichées
# 7. Tester le bouton "Vider la base"
```

### Test 7 : Suppression de Documents ✅

```bash
# Supprimer tous les documents
curl -X DELETE http://localhost:8000/documents

# Expected output:
# {
#   "message": "Tous les documents ont été supprimés",
#   "deleted_count": 1
# }
```

---

## 🔍 Logs et Débogage

### Voir les Logs Docker

```bash
# Logs API
docker compose -f docker-compose-v2.yml logs -f api

# Logs Frontend
docker compose -f docker-compose-v2.yml logs -f frontend

# Logs tous services
docker compose -f docker-compose-v2.yml logs -f
```

### Voir les Logs Local

```bash
# Les logs s'affichent directement dans le terminal où tu as lancé
# uvicorn (API) et streamlit (Frontend)
```

---

## ⚠️ Problèmes Courants

### Problème 1 : ChromaDB - SQLite Version

**Symptôme** :
```
RuntimeError: Your system has an unsupported version of sqlite3
```

**Solution** :
```bash
# En local : Utilise Docker (sqlite3 à jour)
./docker-manage-v2.sh start

# Ou installe pysqlite3-binary
pip install pysqlite3-binary
```

### Problème 2 : Ollama Embeddings Non Disponible

**Symptôme** :
```json
{
  "error": "Ollama n'est pas disponible"
}
```

**Solution** :
```bash
# Option A : Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# Option B : Utiliser Albert Embeddings
# Dans l'UI, sélectionner "albert" dans le dropdown
# Ou via API :
curl -X POST http://localhost:8000/query \
  -d '{"query": "test", "embedding_provider": "albert"}'
```

### Problème 3 : Port 8000 Déjà Utilisé

**Symptôme** :
```
ERROR: port is already allocated
```

**Solution** :
```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>

# Ou changer le port dans docker-compose-v2.yml
```

### Problème 4 : Clés API Manquantes

**Symptôme** :
```json
{
  "error": "ARISTOTE_API_KEY est requis"
}
```

**Solution** :
```bash
# Vérifier les variables d'environnement
echo $ARISTOTE_API_KEY
echo $ALBERT_API_KEY

# Si vides, les exporter
export ARISTOTE_API_KEY="drasi-idf-1-xxx"
export ALBERT_API_KEY="sk-xxx"

# Ou mettre dans .env
nano .env
```

---

## 📊 Checklist de Test

Utilise cette checklist pour vérifier que tout fonctionne :

- [ ] API démarre sans erreur
- [ ] Health check `/health` retourne `healthy`
- [ ] Documentation Swagger accessible sur `/docs`
- [ ] Upload d'un fichier TXT fonctionne
- [ ] Upload d'un fichier PDF fonctionne
- [ ] Liste des documents affiche les documents uploadés
- [ ] Requête RAG retourne une réponse cohérente
- [ ] Sources sont pertinentes
- [ ] Changement de provider LLM fonctionne (aristote → albert)
- [ ] Changement de provider embeddings fonctionne (ollama → albert)
- [ ] Frontend V2 s'affiche correctement
- [ ] Chat dans le frontend fonctionne
- [ ] Upload dans le frontend fonctionne
- [ ] Suppression de documents fonctionne
- [ ] Logs sont propres (pas d'erreurs)

---

## 🎯 Résultat Attendu

Si tous les tests passent ✅, cela signifie que :

1. **Architecture Hexagonale** : Fonctionne correctement
2. **Multi-Providers** : Aristote, Albert, Ollama opérationnels
3. **API REST** : Endpoints complets et documentés
4. **Frontend Découplé** : Streamlit communique avec l'API
5. **Docker V2** : Stack complète déployable

**Status** : ✅ **Phase 2 validée, prête pour Phase 3**

---

## 🚀 Après les Tests

### Si Tout Fonctionne ✅

Tu peux maintenant :

1. **Garder V1 pour ta démo** (port 8501)
2. **Utiliser V2 pour le développement** (ports 8000 + 8502)
3. **Passer à la Phase 3** : Performance & Scalabilité
   - Redis cache
   - Load balancing
   - PostgreSQL
   - Monitoring

### Si Problèmes ❌

1. Vérifier les logs : `docker compose -f docker-compose-v2.yml logs -f`
2. Vérifier les variables d'environnement : `.env.v2`
3. Consulter `PHASE2_STATUS.md` section "Problèmes Courants"
4. Documenter l'erreur et demander de l'aide

---

## 📚 Ressources

| Fichier | Usage |
|---------|-------|
| `PHASE2_STATUS.md` | État détaillé Phase 2 |
| `README_V1_VS_V2.md` | Comparaison V1/V2 |
| `V2_SETUP_COMPLETE.md` | Setup complet V2 |
| `docker-manage-v2.sh` | Script de gestion V2 |

---

**Date** : 2026-01-12
**Durée estimée** : 5-10 minutes
**Difficulté** : Facile

Bon test ! 🚀
