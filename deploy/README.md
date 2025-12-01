# Déploiement sur RHEL 9.4

Guide complet pour déployer Aristote RAG Chatbot sur Red Hat Enterprise Linux 9.4.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Internet                               │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS (443)
┌──────────────────────────▼───────────────────────────────────┐
│                     Nginx (Reverse Proxy)                     │
│                   /etc/nginx/conf.d/aristote-rag.conf        │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP (8501)
┌──────────────────────────▼───────────────────────────────────┐
│                   Podman Container                            │
│                   aristote-rag-chatbot                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Streamlit (app_v2.py)                                  │ │
│  │  ├── ChromaDB (vectorstore)                             │ │
│  │  ├── → Aristote API (LLM)                               │ │
│  │  └── → Albert API (Embeddings/Rerank/Vision)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              Volume persistant                                │
│              /var/lib/aristote-rag                           │
│              ├── chroma_db/                                  │
│              ├── logs/                                       │
│              └── users/                                      │
└──────────────────────────────────────────────────────────────┘
```

## Installation rapide

```bash
# Sur le serveur RHEL 9.4
sudo dnf install -y git

# Cloner le dépôt
git clone https://github.com/jedeth/aristote-rag-chatbot-demo-DRASI.git
cd aristote-rag-chatbot-demo-DRASI

# Lancer l'installation
sudo ./deploy/install-rhel.sh
```

## Installation manuelle

### 1. Prérequis

```bash
# Installer les paquets nécessaires
sudo dnf install -y podman podman-compose nginx git curl

# Vérifier les versions
podman --version
podman-compose --version
nginx -v
```

### 2. Créer l'utilisateur système

```bash
sudo useradd --system --shell /sbin/nologin --home-dir /opt/aristote-rag aristote
```

### 3. Créer les répertoires

```bash
sudo mkdir -p /opt/aristote-rag
sudo mkdir -p /var/lib/aristote-rag/{chroma_db,logs,users}
sudo chown -R aristote:aristote /opt/aristote-rag /var/lib/aristote-rag
```

### 4. Cloner et configurer

```bash
# Cloner le dépôt
sudo -u aristote git clone https://github.com/jedeth/aristote-rag-chatbot-demo-DRASI.git /opt/aristote-rag
cd /opt/aristote-rag

# Créer le fichier de configuration
sudo cp .env.production.example .env
sudo chmod 600 .env
sudo chown aristote:aristote .env

# Éditer avec vos clés API
sudo nano .env
```

### 5. Configurer SELinux

```bash
# Autoriser Nginx à se connecter au backend
sudo setsebool -P httpd_can_network_connect 1

# Configurer les contextes pour les volumes Podman
sudo semanage fcontext -a -t container_file_t "/var/lib/aristote-rag(/.*)?"
sudo restorecon -Rv /var/lib/aristote-rag

sudo semanage fcontext -a -t container_file_t "/opt/aristote-rag(/.*)?"
sudo restorecon -Rv /opt/aristote-rag
```

### 6. Configurer le firewall

```bash
# Ouvrir HTTP et HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Vérifier
sudo firewall-cmd --list-all
```

### 7. Configurer Nginx

```bash
# Copier la configuration
sudo cp deploy/nginx/aristote-rag.conf /etc/nginx/conf.d/

# Modifier le nom de domaine
sudo nano /etc/nginx/conf.d/aristote-rag.conf
# Remplacer "aristote-rag.votre-domaine.fr" par votre domaine

# Ajouter les certificats SSL
sudo mkdir -p /etc/nginx/ssl
sudo cp /chemin/vers/certificat.crt /etc/nginx/ssl/aristote-rag.crt
sudo cp /chemin/vers/cle.key /etc/nginx/ssl/aristote-rag.key
sudo chmod 600 /etc/nginx/ssl/aristote-rag.key

# Tester et démarrer
sudo nginx -t
sudo systemctl enable --now nginx
```

### 8. Construire et démarrer l'application

```bash
cd /opt/aristote-rag

# Construire l'image
sudo -u aristote podman-compose build

# Tester manuellement
sudo -u aristote podman-compose up

# Si tout fonctionne, arrêter (Ctrl+C) et installer le service
sudo cp deploy/aristote-rag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aristote-rag
```

## Commandes utiles

```bash
# Statut des services
sudo systemctl status aristote-rag
sudo systemctl status nginx

# Logs de l'application
sudo journalctl -u aristote-rag -f

# Logs Nginx
sudo tail -f /var/log/nginx/aristote-rag.error.log

# Redémarrer
sudo systemctl restart aristote-rag
sudo systemctl restart nginx

# Mettre à jour
cd /opt/aristote-rag
sudo -u aristote git pull
sudo -u aristote podman-compose build
sudo systemctl restart aristote-rag
```

## Dépannage

### SELinux bloque l'accès

```bash
# Voir les denials récents
sudo ausearch -m avc -ts recent

# Mode permissif temporaire (pour debug uniquement)
sudo setenforce 0

# Générer les règles manquantes
sudo ausearch -c 'podman' --raw | audit2allow -M aristote-podman
sudo semodule -i aristote-podman.pp
```

### Podman ne démarre pas

```bash
# Vérifier les logs
sudo -u aristote podman-compose logs

# Vérifier l'espace disque
df -h

# Vérifier les permissions
ls -la /var/lib/aristote-rag
```

### Nginx erreur 502

```bash
# Vérifier que l'application écoute
curl http://127.0.0.1:8501/_stcore/health

# Vérifier les logs
sudo tail -f /var/log/nginx/aristote-rag.error.log
```

## Sauvegarde

```bash
# Sauvegarder les données
sudo tar czf /backup/aristote-rag-$(date +%Y%m%d).tar.gz /var/lib/aristote-rag

# Restaurer
sudo tar xzf /backup/aristote-rag-XXXXXXXX.tar.gz -C /
```

## Intégration SAML

Pour l'intégration avec votre système d'authentification SAML, vous devrez :

1. Configurer `AUTH_MODE=saml` dans `.env`
2. Implémenter le module SAML (à faire avec votre équipe système)
3. Configurer les URLs de callback dans votre IdP

L'architecture est prête à recevoir l'authentification SAML - chaque utilisateur aura sa propre collection ChromaDB isolée.
