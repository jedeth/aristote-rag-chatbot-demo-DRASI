# =============================================================================
# Dockerfile pour Aristote RAG Chatbot v2
# =============================================================================
# Image ALLÉGÉE utilisant Albert API pour les embeddings
# SANS PyTorch/sentence-transformers (~500 Mo au lieu de ~5 Go)
# Compatible Docker et Podman
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Installation des dépendances
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Installer les dépendances système pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python ALLÉGÉES
# (sans sentence-transformers/PyTorch - on utilise Albert API)
COPY requirements-light.txt .
RUN pip install --no-cache-dir --user -r requirements-light.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Image finale légère
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Métadonnées
LABEL maintainer="DRASI"
LABEL description="Aristote RAG Chatbot v2 - Multi-Provider Edition"
LABEL version="2.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Répertoires de données (seront montés en volumes)
    ARISTOTE_DATA_DIR=/data \
    ARISTOTE_LOG_DIR=/data/logs \
    # Streamlit
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Installer les dépendances système runtime
# - libmagic1: pour python-magic (validation MIME des fichiers)
# - curl: pour les healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier les dépendances Python depuis le builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copier le code de l'application
COPY config.py .
COPY auth.py .
COPY app_v2.py .
COPY providers/ ./providers/

# Créer les répertoires de données
RUN mkdir -p /data/chroma_db /data/logs

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app /data

# Copier le script d'entrée
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Point d'entrée
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["streamlit", "run", "app_v2.py", "--server.port=8501", "--server.address=0.0.0.0"]
