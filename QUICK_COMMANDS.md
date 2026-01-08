# ⚡ Commandes Rapides

## 🐳 Docker (Phase 1)

```bash
# Démarrer
./docker-manage.sh start

# Voir les logs
docker compose logs -f

# Arrêter
./docker-manage.sh stop

# Status
docker compose ps

# Rebuild
docker compose up -d --build
```

## 🏗️ Architecture (Phase 2)

```bash
# Structure créée
tree src/

# Tester le code existant
python -m pytest src/ -v

# Prochains fichiers à créer
touch src/infrastructure/adapters/chromadb_adapter.py
touch src/infrastructure/adapters/albert_embedding_adapter.py
touch src/application/use_cases/search_similar.py
touch src/api/main.py
```

## 📖 Documentation

```bash
# Phase 1 complète
cat PHASE1_COMPLETED.md

# Phase 2 en cours
cat PHASE2_STARTED.md

# Récap session
cat SESSION_RECAP.md

# Guide Docker rapide
cat QUICKSTART_DOCKER.md
```

## 🔧 Debug

```bash
# Logs Docker
docker compose logs -f app

# Shell dans le conteneur
docker compose exec app sh

# Vérifier ChromaDB
docker compose exec app ls -la /app/chroma_db

# Reset complet
docker compose down -v
docker compose up -d --build
```

## ✅ Vérifications

```bash
# Docker fonctionne ?
docker --version
docker compose version

# Build OK ?
docker images | grep aristote

# Services OK ?
docker compose ps

# App accessible ?
curl http://localhost/_stcore/health
```
