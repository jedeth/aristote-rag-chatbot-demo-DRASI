#!/bin/bash
# =============================================================================
# Script de déploiement Aristote RAG Chatbot
# =============================================================================
# Usage:
#   ./scripts/deploy.sh build     # Construire l'image
#   ./scripts/deploy.sh start     # Démarrer les services
#   ./scripts/deploy.sh stop      # Arrêter les services
#   ./scripts/deploy.sh restart   # Redémarrer
#   ./scripts/deploy.sh logs      # Voir les logs
#   ./scripts/deploy.sh status    # État des services
#   ./scripts/deploy.sh shell     # Shell dans le conteneur
#   ./scripts/deploy.sh backup    # Sauvegarder les données
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Détecter Docker ou Podman
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    COMPOSE_CMD="podman-compose"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Erreur: Docker ou Podman requis${NC}"
    exit 1
fi

echo -e "${BLUE}Utilisation de: $CONTAINER_CMD${NC}"

# Vérifier le fichier .env
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Fichier .env non trouvé. Création depuis le template...${NC}"
        if [ -f ".env.production.example" ]; then
            cp .env.production.example .env
            echo -e "${YELLOW}Éditez le fichier .env avec vos clés API avant de continuer.${NC}"
            exit 1
        else
            echo -e "${RED}Template .env.production.example non trouvé${NC}"
            exit 1
        fi
    fi
}

# Charger les variables d'environnement
load_env() {
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
}

case "$1" in
    build)
        echo -e "${GREEN}Construction de l'image Docker...${NC}"
        $CONTAINER_CMD build -t aristote-rag-chatbot:latest .
        echo -e "${GREEN}Image construite avec succès${NC}"
        ;;

    start)
        check_env
        load_env
        echo -e "${GREEN}Démarrage des services...${NC}"

        # Avec ou sans Ollama
        if [ "$DEFAULT_EMBEDDING_PROVIDER" = "ollama" ]; then
            echo -e "${BLUE}Démarrage avec Ollama...${NC}"
            $COMPOSE_CMD --profile ollama up -d

            # Attendre qu'Ollama soit prêt et télécharger le modèle
            echo -e "${BLUE}Attente d'Ollama...${NC}"
            sleep 5
            $CONTAINER_CMD exec aristote-ollama ollama pull nomic-embed-text || true
        else
            $COMPOSE_CMD up -d
        fi

        echo -e "${GREEN}Services démarrés${NC}"
        echo -e "${BLUE}Application disponible sur: http://localhost:${STREAMLIT_PORT:-8501}${NC}"
        ;;

    stop)
        echo -e "${YELLOW}Arrêt des services...${NC}"
        $COMPOSE_CMD --profile ollama down
        echo -e "${GREEN}Services arrêtés${NC}"
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    logs)
        $COMPOSE_CMD logs -f ${2:-app}
        ;;

    status)
        echo -e "${BLUE}État des services:${NC}"
        $COMPOSE_CMD ps
        echo ""
        echo -e "${BLUE}Santé de l'application:${NC}"
        curl -s http://localhost:${STREAMLIT_PORT:-8501}/_stcore/health || echo "Non accessible"
        ;;

    shell)
        echo -e "${BLUE}Connexion au conteneur...${NC}"
        $CONTAINER_CMD exec -it aristote-rag-chatbot /bin/bash
        ;;

    backup)
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        echo -e "${BLUE}Sauvegarde des données...${NC}"

        # Sauvegarder le volume de données
        $CONTAINER_CMD run --rm \
            -v aristote-rag-data:/data:ro \
            -v "$(pwd)/$BACKUP_DIR":/backup \
            alpine tar czf /backup/data.tar.gz -C /data .

        echo -e "${GREEN}Sauvegarde créée dans: $BACKUP_DIR${NC}"
        ;;

    restore)
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 restore <chemin_backup>${NC}"
            exit 1
        fi

        echo -e "${YELLOW}Restauration depuis: $2${NC}"
        echo -e "${RED}ATTENTION: Cela va écraser les données actuelles!${NC}"
        read -p "Continuer? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $CONTAINER_CMD run --rm \
                -v aristote-rag-data:/data \
                -v "$(pwd)/$2":/backup:ro \
                alpine sh -c "rm -rf /data/* && tar xzf /backup/data.tar.gz -C /data"
            echo -e "${GREEN}Restauration terminée${NC}"
        fi
        ;;

    update)
        echo -e "${BLUE}Mise à jour de l'application...${NC}"
        git pull
        $0 build
        $0 restart
        echo -e "${GREEN}Mise à jour terminée${NC}"
        ;;

    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|shell|backup|restore|update}"
        echo ""
        echo "Commandes:"
        echo "  build    - Construire l'image Docker"
        echo "  start    - Démarrer les services"
        echo "  stop     - Arrêter les services"
        echo "  restart  - Redémarrer les services"
        echo "  logs     - Voir les logs (optionnel: nom du service)"
        echo "  status   - État des services"
        echo "  shell    - Ouvrir un shell dans le conteneur"
        echo "  backup   - Sauvegarder les données"
        echo "  restore  - Restaurer une sauvegarde"
        echo "  update   - Mettre à jour depuis git et redéployer"
        exit 1
        ;;
esac
