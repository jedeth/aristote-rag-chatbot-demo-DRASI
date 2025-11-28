"""
Interface abstraite pour les providers d'embeddings.
Permet de basculer entre Ollama et Albert de manière transparente.
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class EmbeddingProvider(ABC):
    """Interface abstraite pour les providers d'embeddings."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour une liste de documents.

        Args:
            texts: Liste de textes à encoder

        Returns:
            Liste de vecteurs d'embeddings
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Génère l'embedding pour une requête utilisateur.

        Args:
            text: Texte de la requête

        Returns:
            Vecteur d'embedding
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Retourne la dimension des vecteurs d'embeddings."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        pass

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
