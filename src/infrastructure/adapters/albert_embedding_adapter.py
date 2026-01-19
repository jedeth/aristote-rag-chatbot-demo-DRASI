"""
Adapter Albert Embeddings - Implémente EmbeddingPort
Architecture Hexagonale : Infrastructure Layer
"""

import logging
from typing import List
from openai import OpenAI

from ...domain.ports.embedding_port import EmbeddingPort, EmbeddingError


logger = logging.getLogger(__name__)


class AlbertEmbeddingAdapter(EmbeddingPort):
    """Adapter pour Albert API - implémente l'interface EmbeddingPort."""

    MODEL_NAME = "openweight-embeddings"  # Anciennement embeddings-small (BAAI/bge-m3)
    DIMENSION = 1024
    API_BASE = "https://albert.api.etalab.gouv.fr/v1"

    def __init__(self, api_key: str):
        """
        Initialise l'adapter Albert.

        Args:
            api_key: Clé API Albert

        Raises:
            EmbeddingError: Si l'initialisation échoue
        """
        if not api_key:
            raise EmbeddingError("La clé API Albert est requise")

        try:
            self._client = OpenAI(
                api_key=api_key,
                base_url=self.API_BASE
            )
            logger.info("Albert Embedding Adapter initialisé")
        except Exception as e:
            logger.error(f"Erreur initialisation Albert: {e}")
            raise EmbeddingError(f"Impossible d'initialiser Albert: {e}")

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
            response = self._client.embeddings.create(
                model=self.MODEL_NAME,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding

            if not embedding or len(embedding) != self.DIMENSION:
                raise EmbeddingError(
                    f"Embedding invalide (dimension attendue: {self.DIMENSION})"
                )

            logger.debug(f"Embedding généré (dim: {len(embedding)})")
            return embedding

        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération embedding Albert: {e}")
            raise EmbeddingError(f"Échec génération embedding: {e}")

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
        if not texts:
            raise EmbeddingError("La liste de textes est vide")

        try:
            # Albert API accepte un batch d'inputs
            response = self._client.embeddings.create(
                model=self.MODEL_NAME,
                input=texts,
                encoding_format="float"
            )

            embeddings = [data.embedding for data in response.data]

            # Vérifier que tous les embeddings sont valides
            for emb in embeddings:
                if not emb or len(emb) != self.DIMENSION:
                    raise EmbeddingError(
                        f"Embedding invalide (dimension attendue: {self.DIMENSION})"
                    )

            logger.info(f"{len(embeddings)} embeddings générés (Albert)")
            return embeddings

        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération embeddings batch Albert: {e}")
            raise EmbeddingError(f"Échec génération embeddings: {e}")

    def get_dimension(self) -> int:
        """Retourne la dimension des vecteurs d'embeddings."""
        return self.DIMENSION

    def get_model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self.MODEL_NAME
