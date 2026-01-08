"""
Adapter Ollama Embeddings - Implémente EmbeddingPort
Architecture Hexagonale : Infrastructure Layer
"""

import logging
from typing import List
import ollama

from ...domain.ports.embedding_port import EmbeddingPort, EmbeddingError


logger = logging.getLogger(__name__)


class OllamaEmbeddingAdapter(EmbeddingPort):
    """Adapter pour Ollama - implémente l'interface EmbeddingPort."""

    MODEL_NAME = "nomic-embed-text"
    DIMENSION = 768

    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialise l'adapter Ollama.

        Args:
            model_name: Nom du modèle Ollama (défaut: nomic-embed-text)

        Raises:
            EmbeddingError: Si l'initialisation échoue
        """
        self._model_name = model_name

        try:
            # Test de connexion Ollama
            ollama.list()
            logger.info(f"Ollama Embedding Adapter initialisé (modèle: {model_name})")
        except Exception as e:
            logger.error(f"Erreur initialisation Ollama: {e}")
            raise EmbeddingError(
                f"Impossible de se connecter à Ollama: {e}. "
                "Vérifiez qu'Ollama est lancé et que le modèle est installé."
            )

    def embed_text(self, text: str) -> List[float]:
        """
        Génère l'embedding d'un texte.

        Args:
            text: Texte à vectoriser

        Returns:
            Vecteur d'embedding

        Raises:
            EmbeddingError: Si l'embedding échoue
        """
        if not text or not text.strip():
            raise EmbeddingError("Le texte ne peut pas être vide")

        try:
            response = ollama.embeddings(
                model=self._model_name,
                prompt=text
            )

            embedding = response.get("embedding")

            if not embedding:
                raise EmbeddingError("Aucun embedding retourné par Ollama")

            logger.debug(f"Embedding généré (dim: {len(embedding)})")
            return embedding

        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération embedding Ollama: {e}")
            raise EmbeddingError(f"Échec génération embedding: {e}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour plusieurs textes.

        Note: Ollama ne supporte pas le batch nativement,
        donc on fait plusieurs appels séquentiels.

        Args:
            texts: Liste de textes à vectoriser

        Returns:
            Liste de vecteurs d'embeddings

        Raises:
            EmbeddingError: Si l'embedding échoue
        """
        if not texts:
            raise EmbeddingError("La liste de textes est vide")

        try:
            embeddings = []
            for text in texts:
                embedding = self.embed_text(text)
                embeddings.append(embedding)

            logger.info(f"{len(embeddings)} embeddings générés (Ollama)")
            return embeddings

        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération embeddings batch Ollama: {e}")
            raise EmbeddingError(f"Échec génération embeddings: {e}")

    def get_dimension(self) -> int:
        """Retourne la dimension des vecteurs d'embeddings."""
        return self.DIMENSION

    def get_model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model_name
