# Guide d'Installation Docker - RedHat 9.4

## Aristote RAG Chatbot

Ce guide vous accompagne pas à pas pour installer le chatbot sur votre serveur RedHat 9.4 avec Docker.

---

## Prérequis

- Serveur RedHat 9.4 avec Docker installé
- Connexion Internet (pour télécharger les images)
- Clé API Aristote

---

## Installation en 4 étapes

### Étape 1 : Récupérer les fichiers

Connectez-vous à votre serveur et clonez ou copiez le projet :

```bash
# Option A : Cloner le dépôt (si git disponible)
git clone <url-du-depot> chatbot-rag
cd chatbot-rag/deploy/docker

# Option B : Copier les fichiers manuellement
# Transférez le dossier du projet sur le serveur
cd /chemin/vers/aristote-rag-chatbot-demo-DRASI/deploy/docker
```

### Étape 2 : Configurer la clé API

```bash
# Créer le fichier de configuration
cp .env.example .env

# Éditer le fichier
nano .env
```

Dans le fichier `.env`, remplacez `votre_cle_api_ici` par votre vraie clé API Aristote :

```
ARISTOTE_API_BASE=https://llm.ilaas.fr/v1
ARISTOTE_API_KEY=votre_vraie_cle_api_ici
```

Sauvegardez avec `Ctrl+O`, puis quittez avec `Ctrl+X`.

### Étape 3 : Lancer l'application

```bash
# Rendre le script exécutable (si nécessaire)
chmod +x start.sh stop.sh restart.sh

# Démarrer l'application
./start.sh
```

**Premier démarrage** : Le script va télécharger :
- L'image Ollama (~2 Go)
- Le modèle d'embeddings nomic-embed-text (~270 Mo)
- L'image Python avec les dépendances

Cela peut prendre **2-5 minutes** selon votre connexion.

### Étape 4 : Accéder à l'application

Ouvrez votre navigateur et accédez à :

```
http://IP_DU_SERVEUR:8501
```

Exemple : `http://192.168.1.100:8501`

---

## Commandes utiles

| Action | Commande |
|--------|----------|
| Démarrer | `./start.sh` |
| Arrêter | `./stop.sh` |
| Redémarrer | `./restart.sh` |
| Voir les logs | `docker compose logs -f` |
| Logs du chatbot | `docker compose logs -f chatbot` |
| Logs d'Ollama | `docker compose logs -f ollama` |
| État des services | `docker compose ps` |

---

## Configuration du Pare-feu (si nécessaire)

Si le port 8501 n'est pas accessible depuis l'extérieur :

```bash
# Ouvrir le port 8501
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload

# Vérifier
sudo firewall-cmd --list-ports
```

---

## Dépannage

### Erreur "Permission denied"

```bash
chmod +x *.sh
```

### L'application ne démarre pas

Vérifiez les logs :
```bash
docker compose logs -f
```

### Ollama ne télécharge pas le modèle

Vérifiez que le service Ollama est en bonne santé :
```bash
docker compose ps
# Le service "ollama" doit être "healthy"

# Si ce n'est pas le cas, redémarrez :
docker compose restart ollama
```

### Erreur de connexion API Aristote

1. Vérifiez votre clé API dans `.env`
2. Testez la connexion depuis le serveur :
   ```bash
   curl -H "Authorization: Bearer VOTRE_CLE" https://llm.ilaas.fr/v1/models
   ```

### Réinitialiser complètement

```bash
# Arrêter et supprimer les conteneurs + volumes
docker compose down -v

# Nettoyer les images (optionnel)
docker system prune -a

# Redémarrer
./start.sh
```

---

## Mise à jour de l'application

```bash
# Mettre à jour le code source
cd /chemin/vers/aristote-rag-chatbot-demo-DRASI
git pull

# Reconstruire et redémarrer
cd deploy/docker
docker compose build --no-cache
docker compose up -d
```

---

## Configuration avancée

### Changer le port

Éditez `docker-compose.yml` et modifiez la ligne :
```yaml
ports:
  - "8501:8501"  # Changez le premier 8501
```

Exemple pour le port 80 :
```yaml
ports:
  - "80:8501"
```

### Activer le GPU (NVIDIA)

Si votre serveur a un GPU NVIDIA, décommentez dans `docker-compose.yml` :

```yaml
ollama:
  # ...
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

Assurez-vous que nvidia-container-toolkit est installé.

---

## Support

En cas de problème :
1. Consultez les logs : `docker compose logs -f`
2. Vérifiez l'état des services : `docker compose ps`
3. Contactez l'équipe DRASI
