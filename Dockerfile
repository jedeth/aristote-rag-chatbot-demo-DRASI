# =============================================================================
# Dockerfile multi-stage pour Aristote RAG Chatbot
# Architecture: Debian Slim + Python 3.11 + User non-root + Health checks
# Note: Debian utilisé au lieu d'Alpine pour compatibilité PyMuPDF
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder - Installation des dépendances
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Variables d'environnement pour optimiser pip
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libsqlite3-dev \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un répertoire de travail
WORKDIR /build

# Copier les fichiers de requirements
COPY requirements.txt .

# Créer un virtual environment et installer les dépendances
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installer les dépendances Python
# Note: pysqlite3-binary pour le patch SQLite de ChromaDB
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pysqlite3-binary

# -----------------------------------------------------------------------------
# STAGE 2: Runtime - Image minimale de production
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm

# Métadonnées
LABEL maintainer="DRASI" \
      description="Aristote RAG Chatbot - Conteneurisé" \
      version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    DEBIAN_FRONTEND=noninteractive

# Installer uniquement les dépendances runtime (pas de compilateurs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier le virtual environment depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Créer un utilisateur non-root pour la sécurité (syntaxe Debian)
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser

# Créer les répertoires nécessaires et définir les permissions
WORKDIR /app
RUN mkdir -p /app/chroma_db /app/data && \
    chown -R appuser:appuser /app

# Copier le code de l'application
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser providers/ ./providers/
COPY --chown=appuser:appuser .env.example .env.example

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port Streamlit
EXPOSE 8501

# Health check pour vérifier que l'application répond
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
