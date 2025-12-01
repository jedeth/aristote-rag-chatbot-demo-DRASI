#!/bin/bash
# =============================================================================
# Script d'entrée Docker pour Aristote RAG Chatbot
# =============================================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# -----------------------------------------------------------------------------
# Vérification de la configuration
# -----------------------------------------------------------------------------

log_info "Démarrage d'Aristote RAG Chatbot v2"
log_info "====================================="

# Vérifier les répertoires de données
if [ ! -d "$ARISTOTE_DATA_DIR" ]; then
    log_warn "Création du répertoire de données: $ARISTOTE_DATA_DIR"
    mkdir -p "$ARISTOTE_DATA_DIR"
fi

if [ ! -d "$ARISTOTE_LOG_DIR" ]; then
    mkdir -p "$ARISTOTE_LOG_DIR"
fi

# Vérifier les clés API selon le provider configuré
DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-aristote}
DEFAULT_EMBEDDING_PROVIDER=${DEFAULT_EMBEDDING_PROVIDER:-albert}

log_info "Provider LLM: $DEFAULT_LLM_PROVIDER"
log_info "Provider Embeddings: $DEFAULT_EMBEDDING_PROVIDER"

# Vérifications des clés API
if [ "$DEFAULT_LLM_PROVIDER" = "aristote" ] && [ -z "$ARISTOTE_API_KEY" ]; then
    log_error "ARISTOTE_API_KEY non définie (requis pour LLM Aristote)"
    log_error "Définissez la variable d'environnement ou utilisez un fichier .env"
    exit 1
fi

if [ "$DEFAULT_LLM_PROVIDER" = "albert" ] && [ -z "$ALBERT_API_KEY" ]; then
    log_error "ALBERT_API_KEY non définie (requis pour LLM Albert)"
    exit 1
fi

if [ "$DEFAULT_EMBEDDING_PROVIDER" = "albert" ] && [ -z "$ALBERT_API_KEY" ]; then
    log_error "ALBERT_API_KEY non définie (requis pour Embeddings Albert)"
    exit 1
fi

if [ "$DEFAULT_EMBEDDING_PROVIDER" = "ollama" ]; then
    OLLAMA_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
    log_info "Vérification de la connexion Ollama: $OLLAMA_URL"
    if ! curl -s --connect-timeout 5 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        log_warn "Ollama non accessible à $OLLAMA_URL"
        log_warn "Assurez-vous que le service Ollama est démarré"
    else
        log_info "Ollama accessible"
    fi
fi

# Afficher le mode d'authentification
AUTH_MODE=${AUTH_MODE:-none}
log_info "Mode d'authentification: $AUTH_MODE"

if [ "$AUTH_MODE" != "none" ] && [ -z "$SESSION_SECRET" ]; then
    log_warn "SESSION_SECRET non défini - génération d'un secret temporaire"
    export SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    log_warn "Ce secret sera perdu au redémarrage du conteneur!"
fi

# Afficher les informations de démarrage
log_info "====================================="
log_info "Port: ${STREAMLIT_SERVER_PORT:-8501}"
log_info "Données: $ARISTOTE_DATA_DIR"
log_info "Logs: $ARISTOTE_LOG_DIR"
log_info "====================================="

# -----------------------------------------------------------------------------
# Démarrage de l'application
# -----------------------------------------------------------------------------

exec "$@"
