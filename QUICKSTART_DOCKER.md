# 🚀 Démarrage Rapide - Docker

Guide ultra-rapide pour lancer l'application conteneurisée en **moins de 5 minutes**.

---

## ⚡ Prérequis

- Docker installé ([installer](https://docs.docker.com/get-docker/))
- Clé API Aristote (ou Albert)

Vérification :
```bash
docker --version
# Doit afficher: Docker version 20.10+ ou supérieur
```

---

## 🏃 Démarrage Express (3 commandes)

```bash
# 1️⃣ Configuration
cp .env.docker .env
nano .env  # Remplacez "votre_token_aristote_ici" par votre vraie clé

# 2️⃣ Lancement
./docker-manage.sh start

# 3️⃣ Accès
# Ouvrez http://localhost dans votre navigateur
```

C'est tout ! ✅

---

## 🐳 Méthode Alternative (Docker Compose direct)

Si vous préférez les commandes Docker natives :

```bash
# Configuration
cp .env.docker .env
nano .env

# Build + Démarrage
docker compose up -d --build

# Voir les logs
docker compose logs -f

# Arrêt
docker compose down
```

---

## 🎯 Vérifications

### L'application est-elle démarrée ?

```bash
# Voir le statut des services
docker compose ps

# Doit afficher:
# NAME            STATE     STATUS
# aristote-app    running   healthy
# aristote-caddy  running   healthy
```

### Voir les logs en temps réel

```bash
docker compose logs -f app
# Cherchez: "You can now view your Streamlit app"
```

### Tester l'accès

```bash
# Test HTTP
curl http://localhost

# Test health check
curl http://localhost/_stcore/health
```

---

## 🛠️ Commandes Utiles

### Gestion avec le script

```bash
./docker-manage.sh start     # Démarrer
./docker-manage.sh stop      # Arrêter
./docker-manage.sh restart   # Redémarrer
./docker-manage.sh logs      # Voir les logs
./docker-manage.sh status    # État des services
./docker-manage.sh shell     # Ouvrir un shell dans le conteneur
./docker-manage.sh backup    # Backup de la base ChromaDB
./docker-manage.sh help      # Aide complète
```

### Commandes Docker Compose

```bash
docker compose up -d         # Démarrer en arrière-plan
docker compose down          # Arrêter
docker compose restart       # Redémarrer
docker compose logs -f       # Logs en temps réel
docker compose ps            # État des services
docker compose exec app sh   # Shell dans le conteneur app
```

---

## 🐛 Problèmes Fréquents

### "Port 80 already in use"

Un autre service utilise le port 80 (Apache, Nginx, etc.)

**Solution 1** : Arrêter l'autre service
```bash
sudo systemctl stop apache2  # ou nginx
```

**Solution 2** : Changer le port dans `docker-compose.yml`
```yaml
services:
  reverse-proxy:
    ports:
      - "8080:80"  # Utilisez le port 8080
```

### "ARISTOTE_API_KEY est requis"

Vous n'avez pas configuré le fichier `.env`

**Solution** :
```bash
cp .env.docker .env
nano .env
# Ajoutez votre clé API puis relancez
./docker-manage.sh restart
```

### Certificat SSL non reconnu (localhost)

C'est **normal** en développement local (certificat auto-signé)

**Solution** : Cliquez sur "Avancé" > "Continuer" dans votre navigateur

**Alternative** : Utilisez HTTP en modifiant `Caddyfile` :
```caddyfile
:80 {
    reverse_proxy app:8501
}
```

### L'application ne charge pas

**Étape 1** : Vérifier les logs
```bash
docker compose logs app
```

**Étape 2** : Vérifier que le conteneur tourne
```bash
docker compose ps
```

**Étape 3** : Reconstruire sans cache
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 🔥 Reset Complet

Si rien ne fonctionne, repartez de zéro :

```bash
# ⚠️ ATTENTION : Supprime TOUTES les données
docker compose down -v
docker system prune -a --volumes -f

# Puis redémarrez
./docker-manage.sh start
```

---

## 📊 Accès aux Données

### Base vectorielle ChromaDB

```bash
# Voir le contenu
docker compose exec app ls -la /app/chroma_db

# Backup manuel
docker run --rm \
  -v aristote-rag-chatbot-demo-drasi_chroma_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/chroma_$(date +%Y%m%d).tar.gz -C /data .
```

### Fichiers uploadés

```bash
# Voir les fichiers uploadés
docker compose exec app ls -la /app/data
```

### Logs de sécurité

```bash
# Voir les logs de sécurité de l'application
docker compose exec app cat /app/logs/app_security.log
```

---

## 🎨 Personnalisation

### Changer le domaine (Production)

Éditez `Caddyfile` :
```caddyfile
# Remplacez
localhost

# Par votre domaine
chatbot.example.com
```

Caddy obtiendra automatiquement un certificat Let's Encrypt valide.

### Limiter les ressources

Éditez `docker-compose.yml` :
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4.0'     # Max 4 CPU
          memory: 8G      # Max 8 GB RAM
```

---

## 📖 Documentation Complète

- **README_DOCKER.md** : Guide complet (40+ pages)
- **PHASE1_COMPLETED.md** : Rapport technique de la Phase 1
- **docker-manage.sh --help** : Aide du script de gestion

---

## 🆘 Support

Si vous rencontrez un problème :

1. **Vérifiez les logs** : `docker compose logs -f`
2. **Consultez README_DOCKER.md** : Section "Troubleshooting"
3. **Réinitialisez** : `docker compose down -v && docker compose up -d --build`

---

## ✅ Checklist de Démarrage

- [ ] Docker installé et fonctionnel
- [ ] Fichier `.env` créé et configuré avec votre clé API
- [ ] `./docker-manage.sh start` exécuté sans erreur
- [ ] Services `healthy` dans `docker compose ps`
- [ ] Application accessible sur http://localhost
- [ ] Vous pouvez uploader un document et poser des questions

**Si tous les points sont ✅, vous êtes prêt ! 🎉**

---

**Prochaine étape** : Consulter **README_DOCKER.md** pour la configuration avancée et les phases suivantes.
