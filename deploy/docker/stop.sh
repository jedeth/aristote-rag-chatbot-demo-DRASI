#!/bin/bash
# =============================================================================
# Script d'arrêt - Aristote RAG Chatbot
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Arrêt des services..."
docker compose down

echo ""
echo "Services arrêtés."
echo "Les données sont préservées dans les volumes Docker."
echo ""
echo "Pour supprimer aussi les données: docker compose down -v"
