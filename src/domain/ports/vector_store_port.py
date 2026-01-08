"""
Port (Interface) pour les bases vectorielles
Architecture Hexagonale : Domain Layer
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..entities.document import Chunk
from ..entities.query import SearchResult


class VectorStorePort(ABC):
    """Interface abstraite pour les bases vectorielles."""

    @abstractmethod
    def add_chunks(self, chunks: List[Chunk], document_id: str) -> None:
        """
        Ajoute des chunks à la base vectorielle.

        Args:
            chunks: Liste de chunks avec embeddings
            document_id: ID du document source

        Raises:
            VectorStoreError: Si l'ajout échoue
        """
        pass

    @abstractmethod
    def search_similar(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Recherche les chunks similaires.

        Args:
            query_embedding: Embedding de la requête
            n_results: Nombre de résultats à retourner
            filter_metadata: Filtres sur les métadonnées (optionnel)

        Returns:
            Liste de résultats triés par pertinence

        Raises:
            VectorStoreError: Si la recherche échoue
        """
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """
        Supprime tous les chunks d'un document.

        Args:
            document_id: ID du document à supprimer

        Raises:
            VectorStoreError: Si la suppression échoue
        """
        pass

    @abstractmethod
    def count_chunks(self) -> int:
        """
        Retourne le nombre total de chunks indexés.

        Returns:
            Nombre de chunks
        """
        pass

    @abstractmethod
    def get_indexed_documents(self) -> List[str]:
        """
        Retourne la liste des documents indexés.

        Returns:
            Liste des noms de fichiers
        """
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """
        Supprime tous les chunks de la base.

        Raises:
            VectorStoreError: Si la suppression échoue
        """
        pass


class VectorStoreError(Exception):
    """Exception levée lors d'une erreur de base vectorielle."""
    pass
