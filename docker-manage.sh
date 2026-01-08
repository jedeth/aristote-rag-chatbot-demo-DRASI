#!/bin/bash
# =============================================================================
# Script de gestion Docker - Aristote RAG Chatbot
# =============================================================================

set -e

PROJECT_NAME="aristote-rag-chatbot"
ENV_FILE=".env"
ENV_TEMPLATE=".env.docker"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier que Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi

    print_success "Docker et Docker Compose sont installés"
}

# Vérifier le fichier .env
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Fichier .env non trouvé"

        if [ -f "$ENV_TEMPLATE" ]; then
            print_info "Copie du template .env.docker vers .env"
            cp "$ENV_TEMPLATE" "$ENV_FILE"
            print_warning "⚠️  IMPORTANT: Éditez le fichier .env et ajoutez vos clés API"
            print_info "   Commande: nano .env"
            exit 1
        else
            print_error "Template .env.docker non trouvé"
            exit 1
        fi
    fi

    # Vérifier que les clés ne sont pas les valeurs par défaut
    if grep -q "votre_token_aristote_ici" "$ENV_FILE"; then
        print_error "Le fichier .env contient encore les valeurs par défaut"
        print_info "Éditez .env et remplacez 'votre_token_aristote_ici' par votre vraie clé"
        exit 1
    fi

    print_success "Fichier .env configuré"
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 [COMMANDE]"
    echo ""
    echo "Commandes disponibles:"
    echo "  start       - Démarrer la stack (build + up)"
    echo "  stop        - Arrêter la stack"
    echo "  restart     - Redémarrer la stack"
    echo "  logs        - Afficher les logs en temps réel"
    echo "  status      - Voir l'état des services"
    echo "  build       - Rebuild les images"
    echo "  clean       - Arrêter et supprimer les volumes (⚠️  perte de données)"
    echo "  shell       - Ouvrir un shell dans le conteneur app"
    echo "  backup      - Créer un backup de la base ChromaDB"
    echo "  help        - Afficher cette aide"
    echo ""
}

# Démarrer la stack
start_stack() {
    print_info "Démarrage de la stack Docker..."
    check_docker
    check_env

    docker compose up -d --build

    print_success "Stack démarrée !"
    print_info "Accès: http://localhost ou https://localhost"
    print_info "Logs: docker compose logs -f"
}

# Arrêter la stack
stop_stack() {
    print_info "Arrêt de la stack..."
    docker compose down
    print_success "Stack arrêtée"
}

# Redémarrer la stack
restart_stack() {
    print_info "Redémarrage de la stack..."
    docker compose restart
    print_success "Stack redémarrée"
}

# Afficher les logs
show_logs() {
    print_info "Affichage des logs (Ctrl+C pour quitter)..."
    docker compose logs -f
}

# Afficher le statut
show_status() {
    print_info "État des services:"
    docker compose ps
    echo ""
    print_info "Utilisation des ressources:"
    docker stats --no-stream
}

# Rebuild
rebuild() {
    print_info "Rebuild des images..."
    docker compose build --no-cache
    print_success "Rebuild terminé"
}

# Nettoyage complet
clean_all() {
    print_warning "ATTENTION: Cette action supprimera TOUTES les données (volumes)"
    read -p "Êtes-vous sûr ? (oui/non): " confirm

    if [ "$confirm" = "oui" ]; then
        print_info "Nettoyage en cours..."
        docker compose down -v
        print_success "Nettoyage terminé"
    else
        print_info "Annulé"
    fi
}

# Shell dans le conteneur
open_shell() {
    print_info "Ouverture d'un shell dans le conteneur app..."
    docker compose exec app sh
}

# Backup
backup_data() {
    BACKUP_DIR="./backups"
    BACKUP_FILE="chroma_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

    print_info "Création du backup..."
    mkdir -p "$BACKUP_DIR"

    docker run --rm \
        -v "${PROJECT_NAME}_chroma_data:/data" \
        -v "$(pwd)/$BACKUP_DIR:/backup" \
        alpine tar czf "/backup/$BACKUP_FILE" -C /data .

    print_success "Backup créé: $BACKUP_DIR/$BACKUP_FILE"
}

# Main
case "${1:-}" in
    start)
        start_stack
        ;;
    stop)
        stop_stack
        ;;
    restart)
        restart_stack
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    build)
        rebuild
        ;;
    clean)
        clean_all
        ;;
    shell)
        open_shell
        ;;
    backup)
        backup_data
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        print_error "Commande inconnue: $1"
        show_help
        exit 1
        ;;
esac
