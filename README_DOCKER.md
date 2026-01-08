# 🐳 Docker - Aristote RAG Chatbot

Guide complet pour déployer l'application avec Docker et Docker Compose.

---

## 📋 Prérequis

- **Docker** 20.10+ ([installer](https://docs.docker.com/get-docker/))
- **Docker Compose** v2.0+ (inclus dans Docker Desktop)
- **Ports disponibles** : 80, 443, 8501

Vérification :
```bash
docker --version
docker compose version
```

---

## 🚀 Démarrage Rapide (5 minutes)

### 1️⃣ Configuration des secrets

```bash
# Copier le template de configuration
cp .env.docker .env

# Éditer le fichier .env avec vos clés API
nano .env  # ou vim, ou votre éditeur préféré
```

Remplacez `votre_token_aristote_ici` par votre vraie clé API Aristote.

### 2️⃣ Lancer la stack

```bash
# Build et démarrage en mode détaché
docker compose up -d --build

# Voir les logs en temps réel
docker compose logs -f
```

### 3️⃣ Accéder à l'application

Ouvrez votre navigateur :
- **HTTP** : http://localhost
- **HTTPS** : https://localhost (certificat auto-signé en local)

L'application est prête quand vous voyez :
```
aristote-app     | You can now view your Streamlit app in your browser.
aristote-caddy   | [INFO] Serving HTTPS on :443
```

---

## 📚 Commandes Principales

### Gestion du cycle de vie

```bash
# Démarrer la stack
docker compose up -d

# Arrêter la stack (conserve les données)
docker compose down

# Arrêter ET supprimer les volumes (⚠️ perte de données)
docker compose down -v

# Redémarrer un service spécifique
docker compose restart app
```

### Logs et debugging

```bash
# Voir tous les logs
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f app
docker compose logs -f reverse-proxy

# Voir les dernières 100 lignes
docker compose logs --tail=100 app

# Vérifier l'état des services
docker compose ps
```

### Accéder aux conteneurs

```bash
# Ouvrir un shell dans le conteneur app
docker compose exec app sh

# Ouvrir un shell en tant que root (pour debug)
docker compose exec -u root app sh

# Exécuter une commande ponctuelle
docker compose exec app ls -la /app/chroma_db
```

### Build et mise à jour

```bash
# Rebuild après modification du code
docker compose up -d --build

# Rebuild en forçant (sans cache)
docker compose build --no-cache

# Pull des nouvelles images de base
docker compose pull
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     INTERNET                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                 Port 80/443
                       │
        ┌──────────────▼───────────────┐
        │   Caddy Reverse Proxy        │
        │   - TLS automatique          │
        │   - Rate limiting            │
        │   - Headers sécurité         │
        └──────────────┬───────────────┘
                       │
                    Port 8501
                       │
        ┌──────────────▼───────────────┐
        │   Streamlit App              │
        │   - User non-root            │
        │   - Alpine Linux             │
        │   - Health checks            │
        └──────────────┬───────────────┘
                       │
                       │
        ┌──────────────▼───────────────┐
        │   Volumes Persistants        │
        │   - chroma_db/  (base)       │
        │   - data/       (uploads)    │
        │   - caddy_data/ (TLS)        │
        └──────────────────────────────┘
```

### Services

| Service | Image | Rôle | Ports exposés |
|---------|-------|------|---------------|
| `reverse-proxy` | `caddy:2.7-alpine` | Reverse proxy + TLS | 80, 443 |
| `app` | `build: .` | Application Streamlit | 8501 (interne) |

### Volumes

| Volume | Chemin conteneur | Contenu |
|--------|-----------------|---------|
| `chroma_data` | `/app/chroma_db` | Base vectorielle ChromaDB |
| `upload_data` | `/app/data` | Fichiers uploadés (PDF/DOCX) |
| `caddy_data` | `/data` | Certificats TLS, cache Caddy |
| `caddy_config` | `/config` | Configuration Caddy |

---

## 🔧 Configuration Avancée

### Personnaliser le domaine (Production)

Éditez `Caddyfile` :

```caddyfile
# Remplacer
localhost

# Par votre domaine
chatbot.example.com
```

Caddy obtiendra **automatiquement** un certificat Let's Encrypt valide.

### Changer les limites de ressources

Éditez `docker-compose.yml` :

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4.0'      # 4 CPU max
          memory: 8G       # 8 GB RAM max
        reservations:
          cpus: '1.0'      # 1 CPU garanti
          memory: 2G       # 2 GB RAM garanti
```

### Activer le mode debug

```bash
# Lancer en mode interactif (logs visibles)
docker compose up

# Ou modifier docker-compose.yml :
environment:
  - STREAMLIT_LOGGER_LEVEL=debug
```

### Désactiver HTTPS en local

Éditez `Caddyfile`, décommentez la section HTTP :

```caddyfile
:80 {
    reverse_proxy app:8501
    encode gzip
}
```

Puis redémarrez :
```bash
docker compose restart reverse-proxy
```

---

## 🛡️ Sécurité

### Bonnes pratiques appliquées

✅ **User non-root** : Le conteneur tourne avec UID/GID 1000
✅ **TLS automatique** : Certificats Let's Encrypt (en prod)
✅ **Rate limiting** : 20 requêtes/min/IP (configurable)
✅ **Headers de sécurité** : HSTS, CSP, X-Frame-Options, etc.
✅ **Secrets externalisés** : Variables d'environnement (.env)
✅ **Health checks** : Redémarrage automatique si crash
✅ **Réseau isolé** : Bridge privé `aristote-network`

### Vérifier les secrets

```bash
# S'assurer que .env n'est PAS committé
git status .env
# Doit afficher: "nothing to commit"

# Vérifier que les clés ne sont pas dans les logs
docker compose logs app | grep -i "api_key"
# Ne doit rien afficher
```

### Scanner les vulnérabilités

```bash
# Scanner l'image avec Docker Scout
docker scout cves aristote-rag-chatbot-demo-drasi-app:latest

# Ou avec Trivy
trivy image aristote-rag-chatbot-demo-drasi-app:latest
```

---

## 📊 Monitoring

### Health checks

```bash
# Vérifier le statut
docker compose ps

# Tester le health check manuellement
curl http://localhost/_stcore/health
```

### Utilisation des ressources

```bash
# Statistiques en temps réel
docker stats

# Voir les ressources par conteneur
docker compose stats
```

### Backup des données

```bash
# Backup de la base ChromaDB
docker run --rm -v aristote-rag-chatbot-demo-drasi_chroma_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/chroma_backup_$(date +%Y%m%d).tar.gz -C /data .

# Restauration
docker run --rm -v aristote-rag-chatbot-demo-drasi_chroma_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/chroma_backup_YYYYMMDD.tar.gz -C /data
```

---

## 🐛 Troubleshooting

### L'application ne démarre pas

```bash
# Vérifier les logs détaillés
docker compose logs app

# Problème de build ? Rebuild sans cache
docker compose build --no-cache app

# Vérifier la configuration
docker compose config
```

### Erreur "port already in use"

```bash
# Trouver le processus utilisant le port 80
sudo lsof -i :80

# Ou arrêter tous les conteneurs
docker stop $(docker ps -aq)
```

### Certificat TLS non reconnu (localhost)

C'est **normal** en développement local. Options :

1. **Ignorer l'avertissement** : Cliquez sur "Avancé" > "Continuer"
2. **Utiliser HTTP** : Modifiez `Caddyfile` (voir section "Configuration Avancée")
3. **Ajouter le certificat aux autorités de confiance** :
   ```bash
   # Exporter le certificat
   docker compose exec reverse-proxy cat /data/caddy/certificates/local/localhost/localhost.crt > localhost.crt
   # Importer dans votre OS
   ```

### Problème de permissions

```bash
# Vérifier les permissions des volumes
docker compose exec app ls -la /app/chroma_db

# Si erreur, fixer les permissions
docker compose exec -u root app chown -R appuser:appuser /app
```

### Réinitialiser complètement

```bash
# Arrêter et supprimer TOUT (⚠️ perte de données)
docker compose down -v
docker system prune -a --volumes -f

# Puis redémarrer
docker compose up -d --build
```

---

## 🚀 Prochaines Étapes (Phases suivantes)

Cette configuration est la **Phase 1** de la roadmap. Prochainement :

- 🔄 **Phase 2** : Refactoring en architecture hexagonale (API FastAPI)
- ⚡ **Phase 3** : Ajout de Redis cache + PostgreSQL + Load balancing
- 📊 **Phase 4** : Monitoring avec Prometheus + Grafana + Loki

---

## 📞 Support

- **Logs de sécurité** : `docker compose exec app cat /app/logs/app_security.log`
- **Vérifier la config Caddy** : `docker compose exec reverse-proxy caddy validate`
- **Tester l'API Aristote** : `docker compose exec app curl https://llm.ilaas.fr/v1/models`

---

**🎉 Votre application est maintenant conteneurisée et production-ready (Phase 1) !**
