#!/bin/bash
# =============================================================================
# Script de redémarrage - Aristote RAG Chatbot
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Redémarrage des services..."
docker compose restart

echo ""
echo "Services redémarrés."
echo "Accédez à l'application: http://localhost:8501"
