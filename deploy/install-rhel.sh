#!/bin/bash
# =============================================================================
# Script d'installation pour RHEL 9.4
# =============================================================================
# Usage: sudo ./install-rhel.sh
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Vérifier les droits root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en root (sudo)"
    exit 1
fi

# Variables
APP_NAME="aristote-rag"
APP_USER="aristote"
APP_DIR="/opt/aristote-rag"
DATA_DIR="/var/lib/aristote-rag"
REPO_URL="https://github.com/jedeth/aristote-rag-chatbot-demo-DRASI.git"

echo "=============================================="
echo "  Installation d'Aristote RAG Chatbot"
echo "  sur RHEL 9.4"
echo "=============================================="
echo ""

# =============================================================================
# ÉTAPE 1: Prérequis système
# =============================================================================
log_step "1/8 - Installation des prérequis..."

# Vérifier la version de RHEL
if [ -f /etc/redhat-release ]; then
    log_info "Système: $(cat /etc/redhat-release)"
else
    log_warn "Ce script est conçu pour RHEL 9.x"
fi

# Installer les paquets nécessaires
dnf install -y \
    podman \
    podman-compose \
    nginx \
    git \
    curl \
    policycoreutils-python-utils \
    || { log_error "Erreur installation paquets"; exit 1; }

log_info "Prérequis installés"

# =============================================================================
# ÉTAPE 2: Créer l'utilisateur système
# =============================================================================
log_step "2/8 - Création de l'utilisateur système..."

if id "$APP_USER" &>/dev/null; then
    log_info "Utilisateur $APP_USER existe déjà"
else
    useradd --system --shell /sbin/nologin --home-dir "$APP_DIR" "$APP_USER"
    log_info "Utilisateur $APP_USER créé"
fi

# =============================================================================
# ÉTAPE 3: Créer les répertoires
# =============================================================================
log_step "3/8 - Création des répertoires..."

mkdir -p "$APP_DIR"
mkdir -p "$DATA_DIR"/{chroma_db,logs,users}
mkdir -p /etc/nginx/ssl

chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$DATA_DIR"

log_info "Répertoires créés"

# =============================================================================
# ÉTAPE 4: Cloner le dépôt
# =============================================================================
log_step "4/8 - Clonage du dépôt..."

if [ -d "$APP_DIR/.git" ]; then
    log_info "Dépôt déjà cloné, mise à jour..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull
else
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
log_info "Dépôt cloné dans $APP_DIR"

# =============================================================================
# ÉTAPE 5: Configuration
# =============================================================================
log_step "5/8 - Configuration..."

if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.production.example" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    log_warn "Fichier .env créé - ÉDITEZ-LE avec vos clés API !"
    log_warn "  nano $APP_DIR/.env"
else
    log_info "Fichier .env existe déjà"
fi

# Mettre à jour les chemins dans .env
sed -i "s|^ARISTOTE_DATA_DIR=.*|ARISTOTE_DATA_DIR=$DATA_DIR|" "$APP_DIR/.env"
sed -i "s|^ARISTOTE_LOG_DIR=.*|ARISTOTE_LOG_DIR=$DATA_DIR/logs|" "$APP_DIR/.env"

# =============================================================================
# ÉTAPE 6: Configurer SELinux
# =============================================================================
log_step "6/8 - Configuration SELinux..."

if getenforce | grep -q "Enforcing"; then
    log_info "SELinux actif, configuration des contextes..."

    # Autoriser Nginx à se connecter au réseau
    setsebool -P httpd_can_network_connect 1

    # Contextes pour les répertoires de données
    semanage fcontext -a -t container_file_t "$DATA_DIR(/.*)?" 2>/dev/null || true
    restorecon -Rv "$DATA_DIR"

    # Contextes pour le répertoire de l'application
    semanage fcontext -a -t container_file_t "$APP_DIR(/.*)?" 2>/dev/null || true
    restorecon -Rv "$APP_DIR"

    log_info "Contextes SELinux configurés"
else
    log_warn "SELinux non actif ou en mode permissif"
fi

# =============================================================================
# ÉTAPE 7: Configurer le firewall
# =============================================================================
log_step "7/8 - Configuration du firewall..."

# Ouvrir les ports HTTP/HTTPS
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

log_info "Firewall configuré (HTTP/HTTPS ouverts)"

# =============================================================================
# ÉTAPE 8: Installer les services
# =============================================================================
log_step "8/8 - Installation des services..."

# Service systemd
cp "$APP_DIR/deploy/aristote-rag.service" /etc/systemd/system/
systemctl daemon-reload

# Configuration Nginx
cp "$APP_DIR/deploy/nginx/aristote-rag.conf" /etc/nginx/conf.d/
nginx -t || { log_error "Configuration Nginx invalide"; exit 1; }

log_info "Services installés"

# =============================================================================
# RÉSUMÉ
# =============================================================================
echo ""
echo "=============================================="
echo -e "${GREEN}  Installation terminée !${NC}"
echo "=============================================="
echo ""
echo "Prochaines étapes:"
echo ""
echo "1. Éditez le fichier de configuration:"
echo "   ${YELLOW}sudo nano $APP_DIR/.env${NC}"
echo "   (ajoutez vos clés API ARISTOTE_API_KEY et/ou ALBERT_API_KEY)"
echo ""
echo "2. Modifiez la configuration Nginx:"
echo "   ${YELLOW}sudo nano /etc/nginx/conf.d/aristote-rag.conf${NC}"
echo "   (remplacez 'aristote-rag.votre-domaine.fr' par votre domaine)"
echo ""
echo "3. Ajoutez vos certificats SSL:"
echo "   ${YELLOW}sudo cp votre-certificat.crt /etc/nginx/ssl/aristote-rag.crt${NC}"
echo "   ${YELLOW}sudo cp votre-cle.key /etc/nginx/ssl/aristote-rag.key${NC}"
echo ""
echo "4. Construisez l'image et démarrez:"
echo "   ${YELLOW}cd $APP_DIR${NC}"
echo "   ${YELLOW}sudo -u $APP_USER podman-compose build${NC}"
echo "   ${YELLOW}sudo systemctl enable --now aristote-rag${NC}"
echo "   ${YELLOW}sudo systemctl enable --now nginx${NC}"
echo ""
echo "5. Vérifiez le statut:"
echo "   ${YELLOW}sudo systemctl status aristote-rag${NC}"
echo "   ${YELLOW}sudo systemctl status nginx${NC}"
echo ""
echo "Logs:"
echo "   ${YELLOW}sudo journalctl -u aristote-rag -f${NC}"
echo ""
