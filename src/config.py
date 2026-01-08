"""
Configuration et Wiring - Injection de dépendances
⚠️ C'EST ICI qu'on décide qui fait quoi (Prod vs Test)
Architecture Hexagonale : Point de câblage
"""

import os
import logging
from typing import Tuple

from .domain.ports.embedding_port import EmbeddingPort
from .domain.ports.llm_port import LLMPort
from .domain.ports.vector_store_port import VectorStorePort

from .infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from .infrastructure.adapters.albert_embedding_adapter import AlbertEmbeddingAdapter
from .infrastructure.adapters.ollama_embedding_adapter import OllamaEmbeddingAdapter
from .infrastructure.adapters.aristote_llm_adapter import AristoteLLMAdapter
from .infrastructure.adapters.albert_llm_adapter import AlbertLLMAdapter


logger = logging.getLogger(__name__)


class Config:
    """Configuration de l'application."""

    # Chemins
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "documents")

    # Clés API
    ARISTOTE_API_KEY = os.getenv("ARISTOTE_API_KEY", "")
    ALBERT_API_KEY = os.getenv("ALBERT_API_KEY", "")

    # Providers (par défaut)
    DEFAULT_EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")  # "ollama" ou "albert"
    DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "aristote")  # "aristote" ou "albert"

    # Modèles
    ARISTOTE_MODEL = os.getenv("ARISTOTE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
    ALBERT_LLM_MODEL = os.getenv("ALBERT_LLM_MODEL", "albert-large")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


class DependencyContainer:
    """
    Conteneur d'injection de dépendances.
    ⚠️ C'EST ICI qu'on câble les adapters avec les use cases.
    """

    def __init__(self, config: Config = None):
        """
        Initialise le conteneur.

        Args:
            config: Configuration (utilise Config() par défaut)
        """
        self.config = config or Config()
        self._vector_store: VectorStorePort = None
        self._embedding_port: EmbeddingPort = None
        self._llm_port: LLMPort = None

    def get_vector_store(self) -> VectorStorePort:
        """
        Retourne l'instance du VectorStore (singleton).

        Returns:
            VectorStorePort implémenté par ChromaDBAdapter
        """
        if self._vector_store is None:
            logger.info(f"Initialisation VectorStore (ChromaDB) : {self.config.CHROMA_DB_PATH}")
            self._vector_store = ChromaDBAdapter(
                persist_directory=self.config.CHROMA_DB_PATH,
                collection_name=self.config.CHROMA_COLLECTION_NAME
            )
        return self._vector_store

    def get_embedding_port(self, provider: str = None) -> EmbeddingPort:
        """
        Retourne l'instance de l'EmbeddingPort.

        Args:
            provider: "ollama" ou "albert" (utilise DEFAULT_EMBEDDING_PROVIDER si None)

        Returns:
            EmbeddingPort implémenté par un adapter

        Raises:
            ValueError: Si le provider est invalide ou si la clé API manque
        """
        provider = provider or self.config.DEFAULT_EMBEDDING_PROVIDER

        if provider == "albert":
            if not self.config.ALBERT_API_KEY:
                raise ValueError("ALBERT_API_KEY est requis pour utiliser Albert Embeddings")

            if self._embedding_port is None or not isinstance(self._embedding_port, AlbertEmbeddingAdapter):
                logger.info("Initialisation EmbeddingPort (Albert)")
                self._embedding_port = AlbertEmbeddingAdapter(
                    api_key=self.config.ALBERT_API_KEY
                )

        elif provider == "ollama":
            if self._embedding_port is None or not isinstance(self._embedding_port, OllamaEmbeddingAdapter):
                logger.info(f"Initialisation EmbeddingPort (Ollama: {self.config.OLLAMA_EMBEDDING_MODEL})")
                self._embedding_port = OllamaEmbeddingAdapter(
                    model_name=self.config.OLLAMA_EMBEDDING_MODEL
                )

        else:
            raise ValueError(f"Provider d'embedding invalide: {provider}. Utilisez 'ollama' ou 'albert'.")

        return self._embedding_port

    def get_llm_port(self, provider: str = None) -> LLMPort:
        """
        Retourne l'instance du LLMPort.

        Args:
            provider: "aristote" ou "albert" (utilise DEFAULT_LLM_PROVIDER si None)

        Returns:
            LLMPort implémenté par un adapter

        Raises:
            ValueError: Si le provider est invalide ou si la clé API manque
        """
        provider = provider or self.config.DEFAULT_LLM_PROVIDER

        if provider == "aristote":
            if not self.config.ARISTOTE_API_KEY:
                raise ValueError("ARISTOTE_API_KEY est requis pour utiliser Aristote")

            if self._llm_port is None or not isinstance(self._llm_port, AristoteLLMAdapter):
                logger.info(f"Initialisation LLMPort (Aristote: {self.config.ARISTOTE_MODEL})")
                self._llm_port = AristoteLLMAdapter(
                    api_key=self.config.ARISTOTE_API_KEY,
                    model_name=self.config.ARISTOTE_MODEL
                )

        elif provider == "albert":
            if not self.config.ALBERT_API_KEY:
                raise ValueError("ALBERT_API_KEY est requis pour utiliser Albert")

            if self._llm_port is None or not isinstance(self._llm_port, AlbertLLMAdapter):
                logger.info(f"Initialisation LLMPort (Albert: {self.config.ALBERT_LLM_MODEL})")
                self._llm_port = AlbertLLMAdapter(
                    api_key=self.config.ALBERT_API_KEY,
                    model_name=self.config.ALBERT_LLM_MODEL
                )

        else:
            raise ValueError(f"Provider LLM invalide: {provider}. Utilisez 'aristote' ou 'albert'.")

        return self._llm_port


# Instance globale du conteneur (singleton)
_container: DependencyContainer = None


def get_container() -> DependencyContainer:
    """
    Retourne l'instance globale du conteneur de dépendances.

    Returns:
        DependencyContainer singleton
    """
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def reset_container():
    """Réinitialise le conteneur (utile pour les tests)."""
    global _container
    _container = None
