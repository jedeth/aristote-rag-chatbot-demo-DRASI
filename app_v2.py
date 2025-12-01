"""
Aristote RAG Chatbot v2 - Multi-Provider Edition
================================================
Version avec support multi-provider:
- Embeddings: Ollama (local) ou Albert (API Etalab)
- LLM: Aristote (DRASI) ou Albert (small/large/code)
- Reranking: Albert rerank-small (optionnel)
- Vision: Albert albert-large pour les tableaux/graphiques (optionnel)
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement AVANT tout le reste
load_dotenv()

import streamlit as st
import re
import logging
import traceback
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from openai import OpenAI
import fitz  # PyMuPDF
from docx import Document
import io
import chromadb
from chromadb.config import Settings
import json
import math
from collections import Counter
from pathlib import Path

# =============================================================================
# CONFIGURATION DEVELOPPEMENT (CLÉS API LOCALES)
# =============================================================================

DEV_CONFIG_FILE = Path(__file__).parent / "dev_config.json"
DEV_MODE = False
DEV_CONFIG = {}

def load_dev_config():
    """Charge la configuration de développement si elle existe."""
    global DEV_MODE, DEV_CONFIG
    if DEV_CONFIG_FILE.exists():
        try:
            with open(DEV_CONFIG_FILE, "r", encoding="utf-8") as f:
                DEV_CONFIG = json.load(f)
            DEV_MODE = DEV_CONFIG.get("dev_mode", False)
            return True
        except Exception as e:
            logging.warning(f"Erreur chargement dev_config.json: {e}")
    return False

def save_dev_config():
    """Sauvegarde la configuration de développement."""
    global DEV_CONFIG
    try:
        with open(DEV_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEV_CONFIG, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Erreur sauvegarde dev_config.json: {e}")
        return False

def get_dev_api_key(key_name: str) -> str:
    """Récupère une clé API depuis la config dev."""
    if DEV_MODE and DEV_CONFIG:
        return DEV_CONFIG.get("api_keys", {}).get(key_name, "")
    return ""

# Charger la config dev au démarrage
load_dev_config()

# Import des providers multi-provider
from providers.embeddings import OllamaEmbeddings, AlbertEmbeddings
from providers.llm import AristoteLLM, AlbertLLM
from providers.rerank import AlbertReranker
from providers.vision import AlbertVision, PDFImageExtractor, extract_pdf_with_vision

# Essayer d'importer python-magic pour la validation des fichiers
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic non disponible. Validation MIME désactivée.")

# =============================================================================
# CONFIGURATION SÉCURITÉ
# =============================================================================

logging.basicConfig(
    filename="app_security.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_HISTORY_LENGTH = 20

PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db_v2")
METADATA_FILE = os.path.join(PERSIST_DIRECTORY, "documents_metadata.json")
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
}

DANGEROUS_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)",
    r"(?i)forget\s+(all\s+)?(previous|above|prior)",
    r"(?i)disregard\s+(all\s+)?(previous|above|prior)",
    r"(?i)new\s+instructions?:",
    r"(?i)system\s*prompt:",
    r"(?i)you\s+are\s+now",
    r"(?i)act\s+as\s+if",
    r"(?i)pretend\s+(you|to\s+be)",
    r"(?i)roleplay\s+as",
    r"(?i)<\s*/?system\s*>",
    r"(?i)\[\s*SYSTEM\s*\]",
    r"(?i)```system",
    r"(?i)override\s+(previous|system)",
    r"(?i)jailbreak",
    r"(?i)DAN\s+mode",
]

# =============================================================================
# CONFIGURATION DES PROVIDERS
# =============================================================================

# Configuration par défaut des providers
PROVIDER_CONFIG = {
    "embeddings": {
        "default": "ollama",  # ollama ou albert
        "ollama": {
            "model": "nomic-embed-text",
            "base_url": "http://localhost:11434"
        },
        "albert": {
            "model": "embeddings-small"
        }
    },
    "llm": {
        "default": "aristote",  # aristote ou albert
        "aristote": {
            "model": "meta-llama/Llama-3.3-70B-Instruct"
        },
        "albert": {
            "model": "albert-large",  # albert-small, albert-large, albert-code
            "available_models": ["albert-small", "albert-large", "albert-code"]
        }
    },
    "rerank": {
        "enabled": False,
        "model": "rerank-small",
        "top_k": 5
    },
    "vision": {
        "enabled": False,
        "model": "albert-large"
    }
}

# =============================================================================
# CLASSES DE SÉCURITÉ
# =============================================================================

class RateLimiter:
    """Rate limiter simple basé sur une fenêtre glissante."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    def is_allowed(self, key: str = "default") -> tuple[bool, int]:
        now = datetime.now()
        window_start = now - self.window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        if len(self.requests[key]) >= self.max_requests:
            oldest = min(self.requests[key])
            retry_after = int((oldest + self.window - now).total_seconds()) + 1
            return False, max(retry_after, 1)
        self.requests[key].append(now)
        return True, 0


# =============================================================================
# FONCTIONS DE SÉCURITÉ
# =============================================================================

def handle_error(error: Exception, context: str = "") -> str:
    error_id = str(uuid.uuid4())[:8]
    logging.error(
        f"[{error_id}] {context}: {type(error).__name__}: {error}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    return f"Une erreur s'est produite (réf: {error_id}). Contactez l'administrateur si le problème persiste."


def sanitize_document_content(text: str, max_length: int = 2000) -> str:
    sanitized = text
    for pattern in DANGEROUS_PATTERNS:
        sanitized = re.sub(pattern, "[CONTENU FILTRÉ]", sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [TRONQUÉ]"
    return sanitized


def build_safe_context(similar_chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(similar_chunks):
        source = chunk["metadata"]["filename"]
        safe_content = sanitize_document_content(chunk["text"])
        context_parts.append(
            f"[DOCUMENT {i+1} - Source: {source}]\n"
            f"{safe_content}\n"
            f"[FIN DOCUMENT {i+1}]"
        )
    return "\n\n".join(context_parts)


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    initial_pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
    try:
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)
    except Exception as e:
        return False, f"Erreur de lecture du fichier: {handle_error(e, 'File read')}"

    if len(file_bytes) > MAX_FILE_SIZE:
        return False, f"Fichier trop volumineux ({len(file_bytes) / 1024 / 1024:.1f} MB > {MAX_FILE_SIZE / 1024 / 1024:.0f} MB)"
    if len(file_bytes) == 0:
        return False, "Fichier vide"

    if MAGIC_AVAILABLE:
        try:
            mime = magic.from_buffer(file_bytes, mime=True)
            if mime not in ALLOWED_MIME_TYPES:
                return False, f"Type de fichier non autorisé: {mime}"
            expected_extension = ALLOWED_MIME_TYPES[mime]
            if not uploaded_file.name.lower().endswith(expected_extension):
                return False, f"Extension incohérente avec le contenu"
        except Exception as e:
            logging.warning(f"Erreur validation MIME: {e}")

    filename_lower = uploaded_file.name.lower()
    if filename_lower.endswith(".pdf"):
        if not file_bytes.startswith(b"%PDF"):
            return False, "En-tête PDF invalide"
    elif filename_lower.endswith(".docx"):
        if not file_bytes.startswith(b"PK"):
            return False, "En-tête DOCX invalide"
    else:
        return False, "Extension de fichier non supportée"

    return True, "OK"


# =============================================================================
# GESTION DES PROVIDERS
# =============================================================================

def get_embedding_provider():
    """Retourne le provider d'embeddings configuré."""
    config = st.session_state.get("provider_config", PROVIDER_CONFIG)
    provider_type = config["embeddings"]["default"]

    if provider_type == "albert":
        api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
        if not api_key:
            st.error("Clé API Albert requise pour les embeddings Albert")
            return None
        return AlbertEmbeddings(api_key=api_key)
    else:
        # Ollama par défaut
        ollama_config = config["embeddings"]["ollama"]
        return OllamaEmbeddings(
            model=ollama_config["model"],
            base_url=ollama_config["base_url"]
        )


def get_llm_provider():
    """Retourne le provider LLM configuré."""
    config = st.session_state.get("provider_config", PROVIDER_CONFIG)
    provider_type = config["llm"]["default"]

    if provider_type == "albert":
        api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
        if not api_key:
            st.error("Clé API Albert requise pour le LLM Albert")
            return None
        model = config["llm"]["albert"]["model"]
        return AlbertLLM(api_key=api_key, model=model)
    else:
        # Aristote par défaut
        api_key = st.session_state.get("aristote_api_key") or os.getenv("ARISTOTE_API_KEY")
        api_base = (
            st.session_state.get("aristote_api_url") or
            os.getenv("ARISTOTE_DISPATCHER_URL") or
            os.getenv("ARISTOTE_API_BASE") or
            "https://llm.ilaas.fr/v1"
        )
        if not api_key:
            st.error("Clé API Aristote requise. Configurez-la dans la sidebar.")
            return None
        model = st.session_state.get("selected_model") or config["llm"]["aristote"]["model"]
        return AristoteLLM(api_key=api_key, base_url=api_base, model=model)


def get_reranker():
    """Retourne le reranker Albert si activé."""
    config = st.session_state.get("provider_config", PROVIDER_CONFIG)
    if not config["rerank"]["enabled"]:
        return None

    api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
    if not api_key:
        return None

    return AlbertReranker(api_key=api_key, model=config["rerank"]["model"])


def get_vision_provider():
    """Retourne le provider de vision Albert si activé."""
    config = st.session_state.get("provider_config", PROVIDER_CONFIG)
    if not config["vision"]["enabled"]:
        return None

    api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
    if not api_key:
        return None

    return AlbertVision(api_key=api_key, model=config["vision"]["model"])


# =============================================================================
# FONCTIONS D'EMBEDDINGS
# =============================================================================

def get_embedding(text: str) -> list[float]:
    """Génère l'embedding d'un texte via le provider configuré."""
    try:
        provider = get_embedding_provider()
        if provider is None:
            raise ValueError("Provider d'embeddings non disponible")
        return provider.embed_query(text)
    except Exception as e:
        error_msg = handle_error(e, "Embeddings")
        st.error(f"Erreur embeddings: {error_msg}")
        raise


# =============================================================================
# CHROMADB
# =============================================================================

@st.cache_resource
def get_chroma_client():
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
    client = chromadb.PersistentClient(
        path=PERSIST_DIRECTORY,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    return client


def get_chroma_collection(session_id: str = None, embedding_provider: str = None):
    """
    Récupère ou crée une collection ChromaDB.

    Les collections sont séparées par provider d'embeddings car les dimensions
    diffèrent (Ollama nomic-embed-text: 768, Albert embeddings-small: 1024).
    """
    # Déterminer le provider d'embeddings actuel
    if embedding_provider is None:
        embedding_provider = st.session_state.get("provider_config", {}).get("embeddings", {}).get("default", "ollama")

    # Construire le nom de la collection avec le provider
    if session_id:
        base_name = f"docs_{hashlib.sha256(session_id.encode()).hexdigest()[:16]}"
    else:
        base_name = "documents_v2"

    # Ajouter le suffixe du provider pour séparer les collections
    collection_name = f"{base_name}_{embedding_provider}"

    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", "embedding_provider": embedding_provider}
    )
    return collection


def get_collection_for_current_provider():
    """Raccourci pour obtenir la collection du provider actuel."""
    provider = st.session_state.get("provider_config", {}).get("embeddings", {}).get("default", "ollama")
    return get_chroma_collection(embedding_provider=provider)


def save_documents_metadata(documents_text: dict):
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
    metadata = {}
    for filename, data in documents_text.items():
        metadata[filename] = {
            "text_length": len(data.get("text", "")),
            "chunks_count": len(data.get("chunks", [])),
            "indexed_at": datetime.now().isoformat()
        }
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_documents_metadata() -> dict:
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Erreur chargement métadonnées: {e}")
    return {}


def get_indexed_documents() -> list[str]:
    collection = get_chroma_collection()
    if collection.count() == 0:
        return []
    try:
        results = collection.get(include=["metadatas"])
        filenames = set()
        for metadata in results.get("metadatas", []):
            if metadata and "filename" in metadata:
                filenames.add(metadata["filename"])
        return list(filenames)
    except Exception as e:
        logging.warning(f"Erreur récupération documents indexés: {e}")
        return []


# =============================================================================
# API ARISTOTE (pour liste des modèles)
# =============================================================================

def get_client(api_key: str = None):
    key = api_key or st.session_state.get("aristote_api_key") or os.getenv("ARISTOTE_API_KEY", "")
    if not key:
        raise ValueError("Clé API non configurée")
    return OpenAI(
        api_key=key,
        base_url=os.getenv("ARISTOTE_API_BASE", "https://llm.ilaas.fr/v1")
    )


@st.cache_data(ttl=60)
def get_available_models(_api_key: str, _api_base: str = None):
    try:
        client = get_client(_api_key)
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            st.error("❌ Clé API Aristote invalide")
        else:
            st.error(f"❌ Erreur connexion Aristote: {error_type}")
        return []


# =============================================================================
# EXTRACTION DE TEXTE
# =============================================================================

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


def extract_text(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    return ""


def extract_pdf_with_images(
    file_bytes: bytes,
    filename: str,
    use_vision: bool = False,
    max_images: int = 10,
) -> tuple[str, list[dict]]:
    """
    Extrait le texte ET les images d'un PDF.

    Args:
        file_bytes: Contenu du PDF
        filename: Nom du fichier
        use_vision: Utiliser la vision Albert pour analyser les images
        max_images: Nombre maximum d'images à analyser

    Returns:
        Tuple (texte, liste_de_chunks_images)
    """
    # Extraire le texte standard
    text = extract_text_from_pdf(file_bytes)

    # Extraire et analyser les images si vision activée
    image_chunks = []
    if use_vision:
        config = st.session_state.get("provider_config", PROVIDER_CONFIG)
        if config["vision"]["enabled"]:
            api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
            if api_key:
                try:
                    text_from_vision, image_chunks = extract_pdf_with_vision(
                        pdf_bytes=file_bytes,
                        document_name=filename,
                        vision_api_key=api_key,
                        max_images=max_images,
                    )
                except Exception as e:
                    logging.warning(f"Erreur extraction images: {e}")

    return text, image_chunks


def extract_document_header(text: str, max_header_size: int = 300) -> str:
    lines = text.split('\n')
    header_lines = []
    current_size = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if current_size > 100 and any(marker in line for marker in ['🛠️', '👩‍🍳', '📌', '##', '###', 'Étapes', 'Instructions']):
            break
        header_lines.append(line)
        current_size += len(line)
        if current_size >= max_header_size:
            break
    return '\n'.join(header_lines)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    header = extract_document_header(text)
    header_prefix = f"[CONTEXTE DOCUMENT]\n{header}\n[FIN CONTEXTE]\n\n" if header else ""
    chunks = []
    start = 0
    chunk_id = 0
    effective_chunk_size = chunk_size - len(header_prefix) if header_prefix else chunk_size

    while start < len(text):
        end = start + effective_chunk_size
        if end < len(text):
            best_cut = -1
            for sep in ["\n\n", "\n", ". ", "? ", "! "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > effective_chunk_size * 0.5:
                    best_cut = start + last_sep + len(sep)
                    break
            if best_cut > start:
                end = best_cut

        chunk_text_content = text[start:end].strip()
        if chunk_text_content:
            if chunk_id == 0:
                full_chunk_text = chunk_text_content
            else:
                full_chunk_text = header_prefix + chunk_text_content

            chunks.append({
                "id": chunk_id,
                "text": full_chunk_text,
                "text_without_header": chunk_text_content,
                "start": start,
                "end": end,
                "has_header": chunk_id > 0
            })
            chunk_id += 1

        next_start = end - overlap
        if next_start <= start:
            start = start + 1
        else:
            start = next_start

    return chunks


def create_embeddings(chunks: list[dict], progress_callback=None) -> list[dict]:
    """
    Génère les embeddings pour une liste de chunks.
    Utilise embed_documents en batch pour de meilleures performances.

    Args:
        chunks: Liste de chunks avec leur texte
        progress_callback: Fonction optionnelle (current, total) pour la progression

    Returns:
        Chunks avec leurs embeddings ajoutés
    """
    provider = get_embedding_provider()
    if provider is None:
        raise ValueError("Provider d'embeddings non disponible")

    if not chunks:
        return chunks

    # Extraire tous les textes
    texts = [chunk["text"] for chunk in chunks]

    # Générer les embeddings en batch (beaucoup plus rapide)
    try:
        embeddings = provider.embed_documents(texts)

        # Assigner les embeddings aux chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
            if progress_callback:
                progress_callback(i + 1, len(chunks))

    except Exception as e:
        # Fallback: traitement un par un si le batch échoue
        logging.warning(f"Batch embedding failed, falling back to single: {e}")
        for i, chunk in enumerate(chunks):
            try:
                chunk["embedding"] = provider.embed_query(chunk["text"])
            except Exception as single_error:
                logging.error(f"Single embedding failed for chunk {i}: {single_error}")
                chunk["embedding"] = [0.0] * provider.dimension
            if progress_callback:
                progress_callback(i + 1, len(chunks))

    return chunks


def add_to_vectorstore(chunks: list[dict], filename: str):
    collection = get_chroma_collection()
    ids = [f"{filename}_{chunk['id']}" for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [{"filename": filename, "chunk_id": chunk["id"]} for chunk in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    return len(chunks)


# =============================================================================
# RECHERCHE HYBRIDE
# =============================================================================

CHAR_NORMALIZATIONS = {
    'œ': 'oe', 'Œ': 'OE', 'æ': 'ae', 'Æ': 'AE',
    'ç': 'c', 'Ç': 'C', 'é': 'e', 'É': 'E',
    'è': 'e', 'È': 'E', 'ê': 'e', 'Ê': 'E',
    'ë': 'e', 'Ë': 'E', 'à': 'a', 'À': 'A',
    'â': 'a', 'Â': 'A', 'ä': 'a', 'Ä': 'A',
    'î': 'i', 'Î': 'I', 'ï': 'i', 'Ï': 'I',
    'ô': 'o', 'Ô': 'O', 'ö': 'o', 'Ö': 'O',
    'ù': 'u', 'Ù': 'U', 'û': 'u', 'Û': 'U',
    'ü': 'u', 'Ü': 'U', 'ÿ': 'y', 'Ÿ': 'Y',
    ''': "'", ''': "'", '"': '"', '"': '"',
    '—': '-', '–': '-', '\u202f': ' ', '\xa0': ' ',
}


def normalize_text_for_search(text: str) -> str:
    for char, replacement in CHAR_NORMALIZATIONS.items():
        text = text.replace(char, replacement)
    return text


def tokenize(text: str) -> list[str]:
    text = normalize_text_for_search(text)
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'est',
                  'en', 'que', 'qui', 'dans', 'pour', 'sur', 'avec', 'ce', 'cette',
                  'au', 'aux', 'a', 'son', 'sa', 'ses', 'se', 'ou', 'ne', 'pas',
                  'plus', 'par', 'il', 'elle', 'ils', 'elles', 'nous', 'vous', 'je',
                  'tu', 'on', 'etre', 'avoir', 'faire', 'tout', 'tous', 'si', 'mais'}
    tokens = [word for word in text.split() if word and word not in stop_words and len(word) > 1]
    return tokens


def compute_bm25_scores(query: str, documents: list[str], k1: float = 1.5, b: float = 0.75) -> list[float]:
    if not documents:
        return []
    query_tokens = tokenize(query)
    doc_tokens_list = [tokenize(doc) for doc in documents]
    n_docs = len(documents)
    avg_doc_len = sum(len(tokens) for tokens in doc_tokens_list) / n_docs if n_docs > 0 else 1

    df = Counter()
    for doc_tokens in doc_tokens_list:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            df[token] += 1

    scores = []
    for doc_tokens in doc_tokens_list:
        score = 0.0
        doc_len = len(doc_tokens)
        tf = Counter(doc_tokens)
        for term in query_tokens:
            if term not in tf:
                continue
            idf = math.log((n_docs - df[term] + 0.5) / (df[term] + 0.5) + 1)
            term_freq = tf[term]
            tf_norm = (term_freq * (k1 + 1)) / (term_freq + k1 * (1 - b + b * doc_len / avg_doc_len))
            score += idf * tf_norm
        scores.append(score)
    return scores


def normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]


def search_similar(query: str, n_results: int = 7, hybrid: bool = True, semantic_weight: float = 0.5, use_rerank: bool = False) -> list[dict]:
    """Recherche hybride avec reranking optionnel."""
    collection = get_chroma_collection()
    if collection.count() == 0:
        return []

    fetch_count = min(n_results * 3, collection.count()) if hybrid else min(n_results, collection.count())
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_count
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0] if results["distances"] else [0] * len(documents)

    # Reranking si activé
    if use_rerank:
        reranker = get_reranker()
        if reranker:
            try:
                rerank_results = reranker.rerank(query, documents, top_k=n_results)
                similar_chunks = []
                for result in rerank_results:
                    orig_idx = result.index
                    similar_chunks.append({
                        "text": documents[orig_idx],
                        "metadata": metadatas[orig_idx],
                        "distance": distances[orig_idx],
                        "rerank_score": result.score,
                        "score_type": "reranked"
                    })
                return similar_chunks
            except Exception as e:
                logging.warning(f"Reranking échoué, fallback sur recherche standard: {e}")

    # Recherche standard
    if not hybrid or semantic_weight >= 1.0:
        similar_chunks = []
        for i, doc in enumerate(documents[:n_results]):
            similar_chunks.append({
                "text": doc,
                "metadata": metadatas[i],
                "distance": distances[i],
                "score_type": "semantic"
            })
        return similar_chunks

    # Recherche hybride
    semantic_scores = [1 - d for d in distances]
    semantic_scores_norm = normalize_scores(semantic_scores)
    bm25_scores = compute_bm25_scores(query, documents)
    bm25_scores_norm = normalize_scores(bm25_scores)

    keyword_weight = 1 - semantic_weight
    combined_scores = []
    for i in range(len(documents)):
        combined = (semantic_weight * semantic_scores_norm[i] +
                   keyword_weight * bm25_scores_norm[i])
        combined_scores.append({
            "index": i,
            "combined_score": combined,
            "semantic_score": semantic_scores_norm[i],
            "bm25_score": bm25_scores_norm[i]
        })

    combined_scores.sort(key=lambda x: x["combined_score"], reverse=True)

    similar_chunks = []
    for item in combined_scores[:n_results]:
        i = item["index"]
        similar_chunks.append({
            "text": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i],
            "combined_score": item["combined_score"],
            "semantic_score": item["semantic_score"],
            "bm25_score": item["bm25_score"],
            "score_type": "hybrid"
        })

    return similar_chunks


# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

st.set_page_config(
    page_title="Aristote RAG Chatbot v2",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Aristote RAG Chatbot v2")
st.caption("Chatbot intelligent avec RAG - Multi-Provider Edition (Aristote + Albert)")

# Initialisation
if "rate_limiter" not in st.session_state:
    st.session_state.rate_limiter = RateLimiter(max_requests=20, window_seconds=60)

if "session_id" not in st.session_state:
    st.session_state.session_id = secrets.token_hex(16)

if "provider_config" not in st.session_state:
    st.session_state.provider_config = PROVIDER_CONFIG.copy()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration Multi-Provider")

    # === ALERTE MODE DEVELOPPEMENT ===
    if DEV_MODE:
        st.warning(
            "⚠️ **MODE DÉVELOPPEMENT ACTIF**\n\n"
            "Les clés API sont chargées depuis `dev_config.json`.\n\n"
            "**NE PAS DÉPLOYER EN PRODUCTION !**",
            icon="🔧"
        )
        # Checkbox pour sauvegarder les modifications
        if "dev_save_keys" not in st.session_state:
            st.session_state.dev_save_keys = False

    # === Section Providers ===
    with st.expander("🔌 Providers", expanded=True):
        # Provider Embeddings
        st.subheader("Embeddings")
        embedding_provider = st.radio(
            "Provider",
            ["ollama", "albert"],
            index=0 if st.session_state.provider_config["embeddings"]["default"] == "ollama" else 1,
            key="embedding_provider_radio",
            help="Ollama: local, gratuit | Albert: API Etalab, cloud"
        )
        st.session_state.provider_config["embeddings"]["default"] = embedding_provider

        # Provider LLM
        st.subheader("LLM")
        llm_provider = st.radio(
            "Provider",
            ["aristote", "albert"],
            index=0 if st.session_state.provider_config["llm"]["default"] == "aristote" else 1,
            key="llm_provider_radio",
            help="Aristote: DRASI | Albert: Etalab (small/large/code)"
        )
        st.session_state.provider_config["llm"]["default"] = llm_provider

        if llm_provider == "albert":
            albert_model = st.selectbox(
                "Modèle Albert",
                ["albert-small", "albert-large", "albert-code"],
                index=1,
                help="small: rapide | large: polyvalent | code: dev"
            )
            st.session_state.provider_config["llm"]["albert"]["model"] = albert_model

        # Reranking
        st.subheader("Reranking")
        rerank_enabled = st.toggle(
            "Activer le reranking Albert",
            value=st.session_state.provider_config["rerank"]["enabled"],
            help="Améliore la pertinence des résultats RAG"
        )
        st.session_state.provider_config["rerank"]["enabled"] = rerank_enabled

        # Vision
        st.subheader("Vision")
        vision_enabled = st.toggle(
            "Activer la vision Albert",
            value=st.session_state.provider_config["vision"]["enabled"],
            help="Analyse les tableaux et graphiques"
        )
        st.session_state.provider_config["vision"]["enabled"] = vision_enabled

    st.divider()

    # === Section Clés API ===
    st.header("🔑 Clés API")

    # En mode dev, afficher un indicateur
    if DEV_MODE:
        st.caption("🔧 Clés pré-chargées depuis dev_config.json")

    # Aristote - Toujours afficher si LLM = aristote
    needs_aristote = st.session_state.provider_config["llm"]["default"] == "aristote"

    if needs_aristote:
        # Récupérer la valeur depuis: 1) session_state, 2) dev_config, 3) env
        default_aristote_key = (
            st.session_state.get("aristote_api_key") or
            get_dev_api_key("aristote_api_key") or
            os.getenv("ARISTOTE_API_KEY", "")
        )
        default_aristote_url = (
            st.session_state.get("aristote_api_url") or
            get_dev_api_key("aristote_api_url") or
            os.getenv("ARISTOTE_API_BASE") or
            os.getenv("ARISTOTE_DISPATCHER_URL", "https://llm.ilaas.fr/v1")
        )

        aristote_key = st.text_input(
            "Clé API Aristote",
            value=default_aristote_key,
            type="password",
            help="Token d'authentification Aristote Dispatcher"
        )

        aristote_url = st.text_input(
            "URL API Aristote",
            value=default_aristote_url,
            help="URL de base de l'API Aristote"
        )

        if aristote_key:
            st.session_state.aristote_api_key = aristote_key
            st.session_state.aristote_api_url = aristote_url
            # Aussi mettre dans os.environ pour compatibilité
            os.environ["ARISTOTE_API_KEY"] = aristote_key
            os.environ["ARISTOTE_API_BASE"] = aristote_url
            os.environ["ARISTOTE_DISPATCHER_URL"] = aristote_url

            # Sauvegarder dans dev_config si mode dev
            if DEV_MODE:
                DEV_CONFIG.setdefault("api_keys", {})
                DEV_CONFIG["api_keys"]["aristote_api_key"] = aristote_key
                DEV_CONFIG["api_keys"]["aristote_api_url"] = aristote_url

            # Liste des modèles Aristote
            models = get_available_models(aristote_key, aristote_url)
            if models:
                selected_model = st.selectbox("Modèle Aristote", options=models)
                st.session_state.selected_model = selected_model
                st.success(f"✅ Connecté - {len(models)} modèle(s)")
            else:
                st.warning("⚠️ Impossible de récupérer les modèles. Vérifiez la clé API.")

    # Albert (si utilisé)
    needs_albert = (
        st.session_state.provider_config["embeddings"]["default"] == "albert" or
        st.session_state.provider_config["llm"]["default"] == "albert" or
        st.session_state.provider_config["rerank"]["enabled"] or
        st.session_state.provider_config["vision"]["enabled"]
    )

    if needs_albert:
        # Récupérer depuis: 1) session_state, 2) dev_config, 3) env
        default_albert_key = (
            st.session_state.get("albert_api_key") or
            get_dev_api_key("albert_api_key") or
            os.getenv("ALBERT_API_KEY", "")
        )

        albert_key = st.text_input(
            "Clé API Albert (Etalab)",
            value=default_albert_key,
            type="password",
            help="Obtenez votre clé sur https://albert.api.etalab.gouv.fr"
        )
        if albert_key:
            st.session_state.albert_api_key = albert_key
            os.environ["ALBERT_API_KEY"] = albert_key

            # Sauvegarder dans dev_config si mode dev
            if DEV_MODE:
                DEV_CONFIG.setdefault("api_keys", {})
                DEV_CONFIG["api_keys"]["albert_api_key"] = albert_key

            st.success("✅ Clé Albert configurée")

    # Bouton pour sauvegarder les clés en mode dev
    if DEV_MODE and (needs_aristote or needs_albert):
        if st.button("💾 Sauvegarder les clés (dev)", help="Enregistre les clés dans dev_config.json"):
            if save_dev_config():
                st.success("✅ Clés sauvegardées dans dev_config.json")
            else:
                st.error("❌ Erreur lors de la sauvegarde")

    st.divider()

    # === Section RAG ===
    st.header("📚 Base de connaissances")

    # Récupérer la collection pour le provider actuel
    current_emb_provider = st.session_state.provider_config["embeddings"]["default"]
    collection = get_chroma_collection()
    collection_count = collection.count()

    # Avertissement si collection vide pour ce provider
    if collection_count == 0:
        # Vérifier si l'autre provider a des documents
        other_provider = "albert" if current_emb_provider == "ollama" else "ollama"
        other_collection = get_chroma_collection(embedding_provider=other_provider)
        other_count = other_collection.count()

        if other_count > 0:
            st.warning(
                f"⚠️ **Pas de documents indexés pour '{current_emb_provider}'**\n\n"
                f"Vous avez {other_count} chunks indexés avec '{other_provider}'.\n\n"
                f"Chaque provider d'embeddings utilise sa propre base "
                f"(dimensions différentes). Réindexez vos documents ou "
                f"changez de provider d'embeddings."
            )

    # Afficher le provider actuel
    st.caption(f"🔌 Provider embeddings: **{current_emb_provider}**")

    indexed_docs = get_indexed_documents()

    if collection_count > 0:
        st.success(f"💾 {collection_count} chunks indexés")
        with st.expander("📂 Documents indexés"):
            metadata = load_documents_metadata()
            for doc_name in indexed_docs:
                doc_meta = metadata.get(doc_name, {})
                st.caption(f"📄 {doc_name} - {doc_meta.get('chunks_count', '?')} chunks")
    else:
        st.info("📭 Aucun document indexé pour ce provider")

    # Paramètres RAG
    with st.expander("⚙️ Paramètres RAG"):
        rag_enabled = st.toggle("Activer le RAG", value=True)
        rag_exclusive = st.toggle("🔒 Mode exclusif", value=False, disabled=not rag_enabled)
        chunk_size = st.slider("Taille chunks", 200, 1500, 800, 50)
        chunk_overlap = st.slider("Chevauchement", 0, 300, 100, 10)
        n_results = st.slider("Nombre sources", 1, 15, 7)
        hybrid_enabled = st.toggle("Recherche hybride", value=True)
        semantic_weight = st.slider("Poids sémantique", 0.0, 1.0, 0.5, 0.1, disabled=not hybrid_enabled)

        st.session_state.rag_params = {
            "enabled": rag_enabled,
            "exclusive": rag_exclusive if rag_enabled else False,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "n_results": n_results,
            "hybrid_enabled": hybrid_enabled,
            "semantic_weight": semantic_weight if hybrid_enabled else 1.0,
            "use_rerank": st.session_state.provider_config["rerank"]["enabled"]
        }

    # Upload
    uploaded_files = st.file_uploader(
        "Charger des documents",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if "documents_text" not in st.session_state:
            st.session_state.documents_text = {}

        for file in uploaded_files:
            already_indexed = file.name in st.session_state.documents_text or file.name in indexed_docs
            if not already_indexed:
                is_valid, validation_msg = validate_uploaded_file(file)
                if not is_valid:
                    st.error(f"❌ {file.name}: {validation_msg}")
                    continue

                params = st.session_state.get("rag_params", {})
                config = st.session_state.get("provider_config", PROVIDER_CONFIG)
                use_vision = config["vision"]["enabled"]

                try:
                    # Extraction du texte
                    with st.spinner(f"Extraction de {file.name}..."):
                        file_bytes = file.read()
                        file.seek(0)  # Reset pour extract_text

                        if file.name.lower().endswith(".pdf"):
                            text = extract_text_from_pdf(file_bytes)
                        elif file.name.lower().endswith(".docx"):
                            text = extract_text_from_docx(file_bytes)
                        else:
                            text = ""

                        chunks = chunk_text(
                            text,
                            chunk_size=params.get("chunk_size", 800),
                            overlap=params.get("chunk_overlap", 100)
                        )

                    # Extraction des images si vision activée
                    image_chunks = []
                    if use_vision and file.name.lower().endswith(".pdf"):
                        api_key = st.session_state.get("albert_api_key") or os.getenv("ALBERT_API_KEY")
                        if api_key:
                            with st.spinner(f"Analyse des images avec Albert Vision..."):
                                try:
                                    _, image_chunks = extract_pdf_with_vision(
                                        pdf_bytes=file_bytes,
                                        document_name=file.name,
                                        vision_api_key=api_key,
                                        max_images=10,
                                    )
                                    if image_chunks:
                                        st.info(f"🖼️ {len(image_chunks)} image(s) analysée(s)")
                                except Exception as e:
                                    logging.warning(f"Erreur vision: {e}")
                                    st.warning(f"⚠️ Analyse images échouée: {e}")

                    # Créer les embeddings pour le texte avec barre de progression
                    total_chunks = len(chunks) + len(image_chunks)
                    st.write(f"📊 Génération des embeddings ({total_chunks} chunks)...")
                    progress_bar = st.progress(0, text="Initialisation...")

                    def update_progress(current, total):
                        progress = current / total
                        progress_bar.progress(progress, text=f"Chunk {current}/{total}")

                    chunks_with_embeddings = create_embeddings(chunks, progress_callback=update_progress)

                    # Ajouter les embeddings pour les chunks d'images
                    if image_chunks:
                        st.write(f"🖼️ Embeddings des images ({len(image_chunks)})...")
                        for i, img_chunk in enumerate(image_chunks):
                            img_chunk["id"] = len(chunks_with_embeddings)
                            img_chunk["embedding"] = get_embedding(img_chunk["text"])
                            progress_bar.progress(
                                (len(chunks) + i + 1) / total_chunks,
                                text=f"Image {i+1}/{len(image_chunks)}"
                            )
                        chunks_with_embeddings.extend(image_chunks)

                    progress_bar.progress(1.0, text="Terminé !")

                    with st.spinner(f"Indexation dans ChromaDB..."):
                        add_to_vectorstore(chunks_with_embeddings, file.name)

                    st.session_state.documents_text[file.name] = {
                        "text": text,
                        "chunks": chunks_with_embeddings,
                        "image_chunks": len(image_chunks)
                    }
                    save_documents_metadata(st.session_state.documents_text)

                    if image_chunks:
                        st.success(f"✅ {file.name} indexé ({len(chunks)} texte + {len(image_chunks)} images)")
                    else:
                        st.success(f"✅ {file.name} indexé")
                except Exception as e:
                    st.error(f"❌ {file.name}: {handle_error(e, 'Indexation')}")

    # Boutons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Effacer conv."):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset base"):
            client = get_chroma_client()
            try:
                client.delete_collection("documents_v2")
            except:
                pass
            if os.path.exists(METADATA_FILE):
                os.remove(METADATA_FILE)
            st.session_state.documents_text = {}
            st.cache_resource.clear()
            st.rerun()

# Indicateur de mode
rag_params = st.session_state.get("rag_params", {"enabled": True, "exclusive": False})
provider_info = f"Embeddings: {st.session_state.provider_config['embeddings']['default']} | LLM: {st.session_state.provider_config['llm']['default']}"
st.caption(f"🔌 {provider_info}")

if rag_params.get("enabled", True):
    collection = get_chroma_collection()
    if collection.count() > 0:
        mode_text = "🔒 RAG EXCLUSIF" if rag_params.get("exclusive", False) else "📚 RAG actif"
        extra = ""
        if st.session_state.provider_config["rerank"]["enabled"]:
            extra += " + Reranking"
        st.info(f"{mode_text} - {collection.count()} chunks{extra}")
    else:
        st.warning("📚 RAG actif - Aucun document chargé")

# Historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat
if prompt := st.chat_input("Posez votre question..."):
    # Vérifier la configuration
    llm_provider = st.session_state.provider_config["llm"]["default"]

    if llm_provider == "aristote" and "selected_model" not in st.session_state:
        st.warning("⚠️ Configurez votre clé API Aristote")
    elif llm_provider == "albert" and not st.session_state.get("albert_api_key"):
        st.warning("⚠️ Configurez votre clé API Albert")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)

        if len(st.session_state.messages) >= MAX_HISTORY_LENGTH * 2:
            st.session_state.messages = st.session_state.messages[-(MAX_HISTORY_LENGTH * 2):]

        st.session_state.messages.append({"role": "user", "content": prompt})

        # Recherche RAG
        context = ""
        similar_chunks = []
        rag_params = st.session_state.get("rag_params", {"enabled": True})

        if rag_params.get("enabled", True):
            similar_chunks = search_similar(
                prompt,
                n_results=rag_params.get("n_results", 7),
                hybrid=rag_params.get("hybrid_enabled", True),
                semantic_weight=rag_params.get("semantic_weight", 0.5),
                use_rerank=rag_params.get("use_rerank", False)
            )

        if similar_chunks:
            context = build_safe_context(similar_chunks)

        with st.chat_message("assistant"):
            if similar_chunks:
                with st.expander(f"📚 Sources consultées ({len(similar_chunks)})"):
                    for chunk in similar_chunks:
                        if chunk.get("score_type") == "reranked":
                            score_info = f"rerank: {chunk['rerank_score']:.2f}"
                        elif chunk.get("score_type") == "hybrid":
                            score_info = f"combiné: {chunk['combined_score']:.2f}"
                        else:
                            score_info = f"score: {1 - chunk['distance']:.2f}"
                        st.caption(f"**{chunk['metadata']['filename']}** ({score_info})")
                        # Afficher un aperçu du contenu
                        preview = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                        st.text(preview)

            is_exclusive = rag_params.get("exclusive", False)

            if is_exclusive and not context:
                st.warning("🔒 Mode RAG exclusif : Aucune information trouvée dans les documents.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Je suis en mode RAG exclusif et je n'ai trouvé aucune information pertinente."
                })
            else:
                allowed, retry_after = st.session_state.rate_limiter.is_allowed()
                if not allowed:
                    st.warning(f"⏳ Trop de requêtes. Réessayez dans {retry_after}s.")
                else:
                    with st.spinner("Réflexion en cours..."):
                        try:
                            llm = get_llm_provider()
                            if llm is None:
                                raise ValueError("LLM non disponible")

                            # Détecter le provider pour adapter le prompt
                            llm_provider = st.session_state.provider_config["llm"]["default"]

                            # Construire les messages différemment selon le mode et le provider
                            if is_exclusive and context:
                                if llm_provider == "albert":
                                    # Albert : prompt simple et direct, sans instruction de refus
                                    # Le mode exclusif est géré côté app (pas de réponse si pas de context)
                                    system_prompt = "Tu es un assistant qui répond aux questions en utilisant les documents fournis. Réponds en français. Cite la source du document quand tu donnes une information."
                                    user_content = f"""Voici des extraits de documents :

{context}

Question : {prompt}

Réponds à la question en te basant sur les documents ci-dessus."""
                                else:
                                    # Aristote et autres : garder le format original
                                    system_prompt = f"""Tu es un assistant documentaire strict.

INSTRUCTIONS SYSTÈME (IMMUABLES) :
- Tu réponds UNIQUEMENT avec les informations des DOCUMENTS ci-dessous
- Si l'information n'est PAS dans les documents, réponds : "Cette information n'est pas présente dans les documents fournis."
- Cite toujours la source
- Réponds en français

=== DOCUMENTS ===
{context}
=== FIN DOCUMENTS ==="""
                                    user_content = None
                            elif context:
                                if llm_provider == "albert":
                                    system_prompt = "Tu es un assistant qui répond aux questions. Réponds en français."
                                    user_content = f"""Voici des extraits de documents qui peuvent t'aider :

{context}

Question : {prompt}

Réponds à la question. Tu peux utiliser les documents ou tes connaissances."""
                                else:
                                    system_prompt = f"""Tu es un assistant helpful et réponds en français.

Tu as accès aux documents suivants pour répondre à la question.
Utilise ces informations et cite tes sources.

=== DOCUMENTS ===
{context}
=== FIN DOCUMENTS ==="""
                                    user_content = None
                            else:
                                system_prompt = "Tu es un assistant helpful et réponds en français."
                                user_content = None

                            # Construire les messages
                            messages = [{"role": "system", "content": system_prompt}]

                            # Ajouter l'historique (sauf le dernier message si on le reformate)
                            if user_content:
                                # Pour Albert avec contexte : ajouter l'historique puis le message reformaté
                                for m in st.session_state.messages[:-1]:  # Tous sauf le dernier
                                    messages.append({"role": m["role"], "content": m["content"]})
                                messages.append({"role": "user", "content": user_content})
                            else:
                                # Format standard : ajouter tout l'historique
                                for m in st.session_state.messages:
                                    messages.append({"role": m["role"], "content": m["content"]})

                            # Debug: afficher le contexte si mode dev
                            if DEV_MODE:
                                with st.expander("🔧 Debug: Contexte envoyé au LLM"):
                                    st.text(f"Provider: {llm_provider}")
                                    st.text(f"Taille contexte: {len(context)} caractères")
                                    st.text(f"Nombre de messages: {len(messages)}")
                                    if user_content:
                                        st.text(f"User content (tronqué): {user_content[:500]}...")

                            response = llm.chat(messages, stream=False)
                            st.markdown(response)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response
                            })

                        except Exception as e:
                            st.error(f"Erreur: {handle_error(e, 'Appel LLM')}")
