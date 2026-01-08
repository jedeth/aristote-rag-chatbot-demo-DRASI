# 🔄 V1 (Monolithe) vs V2 (Hexagonale) - Guide d'Utilisation

## 📦 Deux Versions Disponibles

| Version | Architecture | Port | Fichier Docker Compose | Status |
|---------|--------------|------|------------------------|--------|
| **V1** | Monolithe (app.py) | 8501 | `docker-compose.yml` | ✅ Production (pour démo) |
| **V2** | Hexagonale (API + Frontend) | 8000 + 8502 | `docker-compose-v2.yml` | 🧪 Développement |

---

## 🚀 V1 - Application Monolithique (DÉMO)

### Description
- Application **tout-en-un** (Streamlit + logique métier)
- 1742 lignes dans `app.py`
- **Stable et testée** pour ta démo

### Lancer V1

```bash
# Utiliser le docker-compose classique
docker compose up -d

# Ou avec le script
./docker-manage.sh start
```

### Accès
- **Interface** : http://localhost:8501
- **Reverse Proxy** : http://localhost (Caddy)

### Arrêter V1

```bash
docker compose down
# OU
./docker-manage.sh stop
```

---

## 🏗️ V2 - Architecture Hexagonale (DÉVELOPPEMENT)

### Description
- **Backend** : API FastAPI (port 8000)
- **Frontend** : Streamlit découplé (port 8502)
- Architecture en couches (domain/application/infrastructure/api)
- Frontend appelle l'API via HTTP

### Lancer V2

```bash
# Utiliser le docker-compose v2
docker compose -f docker-compose-v2.yml up -d --build

# Voir les logs
docker compose -f docker-compose-v2.yml logs -f
```

### Accès
- **API** : http://localhost:8000
- **API Documentation** : http://localhost:8000/docs (Swagger)
- **Frontend** : http://localhost:8502
- **Reverse Proxy** : http://localhost:8080 (Caddy)

### Arrêter V2

```bash
docker compose -f docker-compose-v2.yml down
```

---

## 📊 Comparaison Détaillée

### Architecture

```
V1 (Monolithe)                    V2 (Hexagonale)
──────────────                    ───────────────

┌─────────────────┐              ┌─────────────────┐
│  Streamlit UI   │              │  Streamlit UI   │
│                 │              │  (port 8502)    │
│  + Logique      │              └────────┬────────┘
│  + ChromaDB     │                       │ HTTP
│  + LLM          │                       ▼
│                 │              ┌─────────────────┐
│  (port 8501)    │              │  API FastAPI    │
└─────────────────┘              │  (port 8000)    │
                                 ├─────────────────┤
                                 │ • Use Cases     │
                                 │ • Domain        │
                                 │ • Infrastructure│
                                 └─────────────────┘
```

### Avantages/Inconvénients

| Critère | V1 (Monolithe) | V2 (Hexagonale) |
|---------|----------------|-----------------|
| **Complexité** | ✅ Simple | ⚠️ Plus complexe |
| **Testabilité** | ❌ Difficile | ✅ Facile (mocks) |
| **Maintenance** | ❌ Couplage fort | ✅ Modulaire |
| **Performance** | ✅ Directe | ⚠️ Latence HTTP |
| **Scalabilité** | ❌ Monolithe | ✅ Services séparés |
| **Démo** | ✅ **Stable** | ⚠️ En développement |

---

## 🎯 Cas d'Usage

### Utilise V1 si :
- ✅ Tu veux une démo stable **pour demain**
- ✅ Tu n'as pas besoin de tests unitaires
- ✅ Tu préfères la simplicité
- ✅ Tu veux déployer rapidement

### Utilise V2 si :
- ✅ Tu veux tester l'architecture hexagonale
- ✅ Tu prévois d'écrire des tests
- ✅ Tu veux séparer backend/frontend
- ✅ Tu veux scaler l'API indépendamment

---

## 🔧 Coexistence des Deux Versions

### Les deux peuvent tourner ensemble !

```bash
# Terminal 1 : Lancer V1 (démo)
docker compose up -d

# Terminal 2 : Lancer V2 (dev)
docker compose -f docker-compose-v2.yml up -d
```

**Ports utilisés** :
- V1 : 8501 (Streamlit), 80/443 (Caddy)
- V2 : 8000 (API), 8502 (Frontend), 8080/8443 (Caddy)

**Aucun conflit !** Les deux versions utilisent des réseaux séparés.

---

## 📁 Structure des Fichiers

```
aristote-rag-chatbot-demo-DRASI/
│
├── app.py                        # V1 - Monolithe (1742 lignes)
├── docker-compose.yml            # V1 - Compose
├── Dockerfile                    # V1 - Build
│
├── src/                          # V2 - Architecture hexagonale
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── api/
│
├── frontend/
│   └── app_v2.py                 # V2 - Frontend découplé
│
├── docker-compose-v2.yml         # V2 - Compose
├── Dockerfile.api                # V2 - Build API
└── Caddyfile.v2                  # V2 - Config Caddy
```

---

## 🧪 Tests de la V2

### Test de l'API seule

```bash
# Démarrer seulement l'API
docker compose -f docker-compose-v2.yml up api -d

# Tester avec curl
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Requête RAG
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "n_results": 5
  }'
```

### Test du Frontend seul (avec API locale)

```bash
# Terminal 1 : API en local
cd /home/iarag/ChatBot_multiProvider/aristote-rag-chatbot-demo-DRASI
export ARISTOTE_API_KEY="drasi-idf-1-84e20c68-c43f-4a71-b655-a5af1426eb02"
export CHROMA_DB_PATH="./chroma_db"
python -m uvicorn src.api.main:app --reload

# Terminal 2 : Frontend Streamlit
export API_URL="http://localhost:8000"
streamlit run frontend/app_v2.py
```

---

## 🗄️ Partage de Données

**ChromaDB** : Les deux versions partagent la même base vectorielle !

```yaml
# docker-compose-v2.yml
volumes:
  chroma_data:
    external: true
    name: aristote-rag-chatbot-demo-drasi_chroma_data
```

**Bénéfice** : Les documents indexés dans V1 sont accessibles dans V2.

---

## 🐛 Troubleshooting

### V2 ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker-compose-v2.yml logs api
docker compose -f docker-compose-v2.yml logs frontend

# Rebuild sans cache
docker compose -f docker-compose-v2.yml build --no-cache
docker compose -f docker-compose-v2.yml up -d
```

### Frontend V2 ne se connecte pas à l'API

```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Vérifier les logs du frontend
docker compose -f docker-compose-v2.yml logs frontend

# Vérifier la variable API_URL
docker compose -f docker-compose-v2.yml exec frontend env | grep API_URL
```

### Conflit de ports

Si tu as déjà V1 qui tourne :
- V1 : 8501, 80, 443
- V2 : 8000, 8502, 8080, 8443

**Aucun conflit normalement !** Sinon, arrête V1 avant de lancer V2.

---

## 📝 Checklist Avant Démo (Demain)

### Pour ta démo, utilise V1 :

- [ ] Tester V1 : `docker compose up -d`
- [ ] Vérifier http://localhost:8501
- [ ] Indexer quelques documents
- [ ] Tester quelques requêtes
- [ ] Vérifier que tout fonctionne
- [ ] Arrêter V2 si elle tourne : `docker compose -f docker-compose-v2.yml down`

### Pour tester V2 (après la démo) :

- [ ] Lancer V2 : `docker compose -f docker-compose-v2.yml up -d --build`
- [ ] Tester l'API : http://localhost:8000/docs
- [ ] Tester le frontend : http://localhost:8502
- [ ] Comparer les performances avec V1

---

## 🎯 Recommandation

**POUR DEMAIN** : Utilise **V1** (monolithe)
- ✅ Stable
- ✅ Testée
- ✅ Simple à expliquer
- ✅ Fonctionne parfaitement

**APRÈS LA DÉMO** : Explore **V2** (hexagonale)
- Migration progressive
- Tests unitaires
- Scalabilité

---

## 🚀 Commandes Rapides

```bash
# V1 (Démo - Stable)
docker compose up -d                    # Démarrer
docker compose logs -f                  # Logs
docker compose down                     # Arrêter
# Accès: http://localhost:8501

# V2 (Dev - Hexagonale)
docker compose -f docker-compose-v2.yml up -d --build    # Démarrer
docker compose -f docker-compose-v2.yml logs -f          # Logs
docker compose -f docker-compose-v2.yml down             # Arrêter
# Accès: http://localhost:8502 (Frontend)
# Accès: http://localhost:8000/docs (API)
```

---

**Ta V1 est intacte et prête pour la démo ! 🎉**
**Tu peux explorer V2 après, sans risque ! 🚀**
