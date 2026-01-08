"""
Port (Interface) pour les services d'embeddings
Architecture Hexagonale : Domain Layer (abstraction)
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingPort(ABC):
    """Interface abstraite pour les providers d'embeddings."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Génère l'embedding d'un texte.

        Args:
            text: Texte à vectoriser

        Returns:
            Vecteur d'embedding (liste de floats)

        Raises:
            EmbeddingError: Si l'embedding échoue
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour plusieurs textes.

        Args:
            texts: Liste de textes à vectoriser

        Returns:
            Liste de vecteurs d'embeddings

        Raises:
            EmbeddingError: Si l'embedding échoue
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Retourne la dimension des vecteurs d'embeddings.

        Returns:
            Dimension (ex: 768, 1024, 1536)
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Retourne le nom du modèle utilisé.

        Returns:
            Nom du modèle (ex: "nomic-embed-text", "embeddings-small")
        """
        pass


class EmbeddingError(Exception):
    """Exception levée lors d'une erreur d'embedding."""
    pass
