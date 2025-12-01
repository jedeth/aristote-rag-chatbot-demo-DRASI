#!/bin/bash
# =============================================================================
# Script de démarrage - Aristote RAG Chatbot
# Usage: ./start.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Aristote RAG Chatbot - Démarrage"
echo "=========================================="
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "ERREUR: Docker n'est pas installé."
    echo "Installez Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# Vérifier que docker compose est disponible
if ! docker compose version &> /dev/null; then
    echo "ERREUR: docker compose n'est pas disponible."
    exit 1
fi

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo "INFO: Fichier .env non trouvé, création depuis .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Éditez le fichier .env avec votre clé API :"
    echo "  nano $SCRIPT_DIR/.env"
    echo ""
    echo "Puis relancez ce script."
    exit 1
fi

# Vérifier que la clé API est configurée
if grep -q "votre_cle_api_ici" .env; then
    echo "ATTENTION: La clé API n'est pas configurée !"
    echo ""
    echo "Éditez le fichier .env :"
    echo "  nano $SCRIPT_DIR/.env"
    echo ""
    echo "Remplacez 'votre_cle_api_ici' par votre vraie clé API Aristote."
    exit 1
fi

echo "1/3 - Construction de l'image Docker..."
docker compose build --quiet

echo "2/3 - Démarrage des services..."
docker compose up -d

echo "3/3 - Attente du démarrage (téléchargement du modèle Ollama)..."
echo "     (Le premier démarrage peut prendre 2-5 minutes)"
echo ""

# Attendre que le chatbot soit prêt
MAX_WAIT=300
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "     Attente... ($WAITED s)"
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo "ATTENTION: Le démarrage prend plus de temps que prévu."
    echo "Vérifiez les logs avec: docker compose logs -f"
else
    echo ""
    echo "=========================================="
    echo "  APPLICATION PRÊTE !"
    echo "=========================================="
    echo ""
    echo "  Accédez à l'application :"
    echo "  http://localhost:8501"
    echo ""
    echo "  Commandes utiles :"
    echo "  - Voir les logs    : docker compose logs -f"
    echo "  - Arrêter          : ./stop.sh"
    echo "  - Redémarrer       : ./restart.sh"
    echo "  - État des services: docker compose ps"
    echo ""
fi
