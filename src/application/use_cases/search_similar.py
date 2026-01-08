"""
Use Case : Rechercher des chunks similaires
Architecture Hexagonale : Application Layer
"""

import logging
from typing import List, Optional, Dict

from ...domain.entities.query import Query, SearchResult
from ...domain.ports.embedding_port import EmbeddingPort, EmbeddingError
from ...domain.ports.vector_store_port import VectorStorePort, VectorStoreError


logger = logging.getLogger(__name__)


class SearchSimilarUseCase:
    """Use case pour rechercher des chunks similaires à une requête."""

    def __init__(
        self,
        embedding_port: EmbeddingPort,
        vector_store_port: VectorStorePort
    ):
        """
        Initialise le use case avec injection de dépendances.

        Args:
            embedding_port: Port pour générer les embeddings
            vector_store_port: Port pour rechercher dans la base vectorielle
        """
        self._embedding_port = embedding_port
        self._vector_store_port = vector_store_port

    def execute(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Recherche les chunks similaires à une requête.

        Args:
            query_text: Texte de la requête
            n_results: Nombre de résultats à retourner
            filter_metadata: Filtres sur les métadonnées (optionnel)

        Returns:
            Liste de résultats triés par pertinence

        Raises:
            SearchError: Si la recherche échoue
        """
        # Validation de la requête
        try:
            query = Query(text=query_text)
        except ValueError as e:
            raise SearchError(f"Requête invalide: {e}")

        logger.info(
            f"Recherche similaire : '{query_text[:50]}...' "
            f"(n_results={n_results})"
        )

        try:
            # Étape 1 : Générer l'embedding de la requête
            query_embedding = self._embedding_port.embed_text(query_text)
            query.embedding = query_embedding

            # Étape 2 : Rechercher dans la base vectorielle
            results = self._vector_store_port.search_similar(
                query_embedding=query_embedding,
                n_results=n_results,
                filter_metadata=filter_metadata
            )

            logger.info(f"{len(results)} résultats trouvés")
            return results

        except EmbeddingError as e:
            logger.error(f"Erreur génération embedding: {e}")
            raise SearchError(f"Échec génération embedding: {e}")

        except VectorStoreError as e:
            logger.error(f"Erreur recherche vectorielle: {e}")
            raise SearchError(f"Échec recherche: {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche: {e}")
            raise SearchError(f"Erreur inattendue: {e}")


class SearchError(Exception):
    """Exception levée lors d'une erreur de recherche."""
    pass
