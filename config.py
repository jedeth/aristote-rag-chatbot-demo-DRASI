"""
Configuration centralisée pour Aristote RAG Chatbot.

Toute la configuration est lue depuis les variables d'environnement.
En développement, utilisez un fichier .env (jamais commité).
En production, configurez les variables via systemd, Docker, ou le CI/CD.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger .env si présent (développement local)
load_dotenv()


# =============================================================================
# CHEMINS
# =============================================================================

# Répertoire racine de l'application
APP_DIR = Path(__file__).parent.resolve()

# Répertoire de données (ChromaDB, métadonnées)
# En production : /var/lib/aristote-rag ou volume Docker
DATA_DIR = Path(os.getenv("ARISTOTE_DATA_DIR", APP_DIR / "data"))

# Répertoire ChromaDB
CHROMA_DIR = DATA_DIR / "chroma_db"

# Répertoire des logs
LOG_DIR = Path(os.getenv("ARISTOTE_LOG_DIR", DATA_DIR / "logs"))

# Fichier de métadonnées des documents
METADATA_FILE = DATA_DIR / "documents_metadata.json"


# =============================================================================
# API ARISTOTE (DRASI)
# =============================================================================

ARISTOTE_API_KEY = os.getenv("ARISTOTE_API_KEY", "")
ARISTOTE_API_BASE = os.getenv(
    "ARISTOTE_API_BASE",
    os.getenv("ARISTOTE_DISPATCHER_URL", "https://llm.ilaas.fr/v1")
)


# =============================================================================
# API ALBERT (Etalab)
# =============================================================================

ALBERT_API_KEY = os.getenv("ALBERT_API_KEY", "")
ALBERT_API_BASE = os.getenv("ALBERT_API_BASE", "https://albert.api.etalab.gouv.fr/v1")

# Modèles Albert disponibles
ALBERT_MODELS = {
    "embeddings": os.getenv("ALBERT_EMBEDDING_MODEL", "embeddings-small"),
    "llm": os.getenv("ALBERT_LLM_MODEL", "albert-large"),
    "rerank": os.getenv("ALBERT_RERANK_MODEL", "rerank-small"),
    "vision": os.getenv("ALBERT_VISION_MODEL", "albert-large"),
}


# =============================================================================
# OLLAMA (local)
# =============================================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


# =============================================================================
# PROVIDERS PAR DÉFAUT
# =============================================================================

# Provider d'embeddings : "ollama" ou "albert"
DEFAULT_EMBEDDING_PROVIDER = os.getenv("DEFAULT_EMBEDDING_PROVIDER", "ollama")

# Provider LLM : "aristote" ou "albert"
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "aristote")

# Activer le reranking Albert (nécessite ALBERT_API_KEY)
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "false").lower() == "true"

# Activer la vision Albert pour les images/tableaux dans les PDF
VISION_ENABLED = os.getenv("VISION_ENABLED", "false").lower() == "true"


# =============================================================================
# SÉCURITÉ
# =============================================================================

# Taille max des fichiers uploadés (en bytes)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10 MB

# Nombre max de requêtes par minute (rate limiting)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 20))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # secondes

# Longueur max de l'historique de conversation
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", 20))


# =============================================================================
# AUTHENTIFICATION (pour isolation multi-tenant)
# =============================================================================

# Mode d'authentification : "none", "simple", "cas" (SSO académique)
AUTH_MODE = os.getenv("AUTH_MODE", "none")

# Secret pour signer les sessions (générer avec: python -c "import secrets; print(secrets.token_hex(32))")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")

# URL du serveur CAS (si AUTH_MODE=cas)
CAS_SERVER_URL = os.getenv("CAS_SERVER_URL", "")


# =============================================================================
# DEBUG
# =============================================================================

# Mode debug (affiche les détails des requêtes)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# =============================================================================
# STREAMLIT
# =============================================================================

# Port Streamlit (utilisé par le script de démarrage)
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))

# Adresse d'écoute (0.0.0.0 pour écouter sur toutes les interfaces)
STREAMLIT_ADDRESS = os.getenv("STREAMLIT_ADDRESS", "0.0.0.0")


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def ensure_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_provider_config():
    """Retourne la configuration des providers au format attendu par app_v2.py."""
    return {
        "embeddings": {
            "default": DEFAULT_EMBEDDING_PROVIDER,
            "ollama": {
                "model": OLLAMA_EMBEDDING_MODEL,
                "base_url": OLLAMA_BASE_URL,
            },
            "albert": {
                "model": ALBERT_MODELS["embeddings"],
            }
        },
        "llm": {
            "default": DEFAULT_LLM_PROVIDER,
            "aristote": {
                "model": "auto",  # Récupéré dynamiquement
            },
            "albert": {
                "model": ALBERT_MODELS["llm"],
            }
        },
        "rerank": {
            "enabled": RERANK_ENABLED,
            "model": ALBERT_MODELS["rerank"],
        },
        "vision": {
            "enabled": VISION_ENABLED,
            "model": ALBERT_MODELS["vision"],
        }
    }


def validate_config():
    """Valide la configuration et retourne les erreurs éventuelles."""
    errors = []
    warnings = []

    # Vérifier les clés API selon les providers choisis
    if DEFAULT_LLM_PROVIDER == "aristote" and not ARISTOTE_API_KEY:
        errors.append("ARISTOTE_API_KEY requis (provider LLM = aristote)")

    if DEFAULT_LLM_PROVIDER == "albert" and not ALBERT_API_KEY:
        errors.append("ALBERT_API_KEY requis (provider LLM = albert)")

    if DEFAULT_EMBEDDING_PROVIDER == "albert" and not ALBERT_API_KEY:
        errors.append("ALBERT_API_KEY requis (provider embeddings = albert)")

    if RERANK_ENABLED and not ALBERT_API_KEY:
        warnings.append("Reranking désactivé : ALBERT_API_KEY manquant")

    if VISION_ENABLED and not ALBERT_API_KEY:
        warnings.append("Vision désactivée : ALBERT_API_KEY manquant")

    if AUTH_MODE != "none" and not SESSION_SECRET:
        errors.append("SESSION_SECRET requis pour l'authentification")

    if AUTH_MODE == "cas" and not CAS_SERVER_URL:
        errors.append("CAS_SERVER_URL requis (AUTH_MODE = cas)")

    return errors, warnings


# Créer les répertoires au chargement du module
ensure_directories()
