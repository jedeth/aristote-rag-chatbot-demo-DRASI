# =============================================================================
# Dockerfile - Aristote RAG Chatbot
# Image multi-stage optimisée pour production
# =============================================================================

# Stage 1: Base avec dépendances système
FROM python:3.11-slim-bookworm AS base

# Métadonnées
LABEL maintainer="DRASI Team"
LABEL description="Aristote RAG Chatbot - Chatbot intelligent avec RAG"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système (libmagic pour python-magic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash appuser

# Répertoire de travail
WORKDIR /app

# Stage 2: Installation des dépendances Python
FROM base AS dependencies

# Copier uniquement requirements.txt d'abord (cache Docker)
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application finale
FROM dependencies AS production

# Copier le code source
COPY app.py .
COPY .env.example .env.example

# Créer les répertoires de données
RUN mkdir -p /app/data /app/chroma_db /app/logs \
    && chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Variables d'environnement par défaut (peuvent être surchargées)
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
