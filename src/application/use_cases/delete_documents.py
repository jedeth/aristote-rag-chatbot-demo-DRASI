"""
Use Case : Supprimer des documents
Architecture Hexagonale : Application Layer
"""

import logging
from ...domain.ports.vector_store_port import VectorStorePort, VectorStoreError


logger = logging.getLogger(__name__)


class DeleteDocumentsUseCase:
    """Use case pour supprimer des documents de la base vectorielle."""

    def __init__(self, vector_store_port: VectorStorePort):
        """
        Initialise le use case avec injection de dépendances.

        Args:
            vector_store_port: Port pour accéder à la base vectorielle
        """
        self._vector_store_port = vector_store_port

    def execute_all(self) -> int:
        """
        Supprime tous les documents de la base.

        Returns:
            Nombre de documents supprimés

        Raises:
            DeleteError: Si la suppression échoue
        """
        logger.info("Suppression de tous les documents")

        try:
            count = self._vector_store_port.clear_all()
            logger.info(f"{count} documents supprimés")
            return count

        except VectorStoreError as e:
            logger.error(f"Erreur suppression: {e}")
            raise DeleteError(f"Échec de la suppression: {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la suppression: {e}")
            raise DeleteError(f"Erreur inattendue: {e}")

    def execute_by_id(self, document_id: str) -> bool:
        """
        Supprime un document spécifique par son ID.

        Args:
            document_id: ID du document à supprimer

        Returns:
            True si le document a été supprimé

        Raises:
            DeleteError: Si la suppression échoue
        """
        logger.info(f"Suppression du document {document_id}")

        try:
            self._vector_store_port.delete_document(document_id)
            logger.info(f"Document {document_id} supprimé")
            return True

        except VectorStoreError as e:
            logger.error(f"Erreur suppression document {document_id}: {e}")
            raise DeleteError(f"Échec de la suppression: {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la suppression: {e}")
            raise DeleteError(f"Erreur inattendue: {e}")


class DeleteError(Exception):
    """Exception levée lors d'une erreur de suppression."""
    pass
