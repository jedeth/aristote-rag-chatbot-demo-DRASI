#!/bin/bash
# =============================================================================
# Script de gestion Docker V2 - Architecture Hexagonale
# =============================================================================

set -e

PROJECT_NAME="aristote-rag-v2"
COMPOSE_FILE="docker-compose-v2.yml"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_env() {
    if [ ! -f ".env" ]; then
        print_warning "Fichier .env non trouvé"
        print_info "Copie du template .env.docker vers .env"
        cp .env.docker .env 2>/dev/null || true
        print_warning "⚠️  Éditez .env et ajoutez vos clés API"
        print_info "   Commande: nano .env"
    fi

    if grep -q "votre_token_aristote_ici" .env 2>/dev/null; then
        print_error "Le fichier .env contient encore les valeurs par défaut"
        print_info "Éditez .env et remplacez les clés par vos vraies valeurs"
        exit 1
    fi

    print_success "Configuration .env OK"
}

show_help() {
    echo "Usage: $0 [COMMANDE]"
    echo ""
    echo "Commandes V2 (Architecture Hexagonale) :"
    echo "  start       - Démarrer la stack V2 (API + Frontend)"
    echo "  stop        - Arrêter la stack V2"
    echo "  restart     - Redémarrer la stack V2"
    echo "  logs        - Afficher les logs V2"
    echo "  status      - Voir l'état des services V2"
    echo "  build       - Rebuild les images V2"
    echo "  clean       - Arrêter et supprimer les volumes V2"
    echo "  api-only    - Démarrer seulement l'API"
    echo "  frontend-only - Démarrer seulement le Frontend"
    echo "  test-api    - Tester l'API avec curl"
    echo "  help        - Afficher cette aide"
    echo ""
}

start_stack() {
    print_info "Démarrage de la stack V2 (Architecture Hexagonale)..."
    check_env

    docker compose -f $COMPOSE_FILE up -d --build

    print_success "Stack V2 démarrée !"
    print_info "API : http://localhost:8000/docs"
    print_info "Frontend : http://localhost:8502"
    print_info "Logs : docker compose -f $COMPOSE_FILE logs -f"
}

stop_stack() {
    print_info "Arrêt de la stack V2..."
    docker compose -f $COMPOSE_FILE down
    print_success "Stack V2 arrêtée"
}

restart_stack() {
    print_info "Redémarrage de la stack V2..."
    docker compose -f $COMPOSE_FILE restart
    print_success "Stack V2 redémarrée"
}

show_logs() {
    print_info "Affichage des logs V2 (Ctrl+C pour quitter)..."
    docker compose -f $COMPOSE_FILE logs -f
}

show_status() {
    print_info "État des services V2:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    print_info "Utilisation des ressources:"
    docker stats --no-stream
}

rebuild() {
    print_info "Rebuild des images V2..."
    docker compose -f $COMPOSE_FILE build --no-cache
    print_success "Rebuild terminé"
}

clean_all() {
    print_warning "ATTENTION: Cette action supprimera les volumes V2 (pas la base ChromaDB partagée)"
    read -p "Êtes-vous sûr ? (oui/non): " confirm

    if [ "$confirm" = "oui" ]; then
        print_info "Nettoyage en cours..."
        docker compose -f $COMPOSE_FILE down -v
        print_success "Nettoyage terminé"
    else
        print_info "Annulé"
    fi
}

start_api_only() {
    print_info "Démarrage de l'API seule..."
    check_env
    docker compose -f $COMPOSE_FILE up api -d --build
    print_success "API démarrée sur http://localhost:8000"
}

start_frontend_only() {
    print_info "Démarrage du Frontend seul..."
    docker compose -f $COMPOSE_FILE up frontend -d
    print_success "Frontend démarré sur http://localhost:8502"
}

test_api() {
    print_info "Test de l'API V2..."

    echo ""
    print_info "Test 1: Health check"
    curl -s http://localhost:8000/health | jq . || echo "Erreur: API non accessible"

    echo ""
    print_info "Test 2: Liste des documents"
    curl -s http://localhost:8000/documents | jq . || echo "Erreur"

    echo ""
    print_info "Test 3: Documentation Swagger"
    print_success "Ouvrez http://localhost:8000/docs dans votre navigateur"
}

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
    api-only)
        start_api_only
        ;;
    frontend-only)
        start_frontend_only
        ;;
    test-api)
        test_api
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
