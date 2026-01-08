"""
Use Case : Indexer un document
Architecture Hexagonale : Application Layer
"""

from typing import List
import logging
from ...domain.entities.document import Document, Chunk
from ...domain.ports.embedding_port import EmbeddingPort, EmbeddingError
from ...domain.ports.vector_store_port import VectorStorePort, VectorStoreError


logger = logging.getLogger(__name__)


class IndexDocumentUseCase:
    """Use case pour indexer un document dans la base vectorielle."""

    def __init__(
        self,
        embedding_port: EmbeddingPort,
        vector_store_port: VectorStorePort
    ):
        """
        Initialise le use case avec injection de dépendances.

        Args:
            embedding_port: Port pour générer les embeddings
            vector_store_port: Port pour stocker dans la base vectorielle
        """
        self._embedding_port = embedding_port
        self._vector_store_port = vector_store_port

    def execute(self, document: Document) -> Document:
        """
        Indexe un document : génère les embeddings et stocke dans la base.

        Args:
            document: Document à indexer (avec chunks mais sans embeddings)

        Returns:
            Document enrichi avec les embeddings

        Raises:
            IndexError: Si l'indexation échoue
        """
        if not document.chunks:
            raise IndexError("Le document ne contient aucun chunk")

        logger.info(
            f"Indexation du document {document.filename} "
            f"({document.chunks_count} chunks)"
        )

        try:
            # Étape 1 : Générer les embeddings pour tous les chunks
            texts = [chunk.text for chunk in document.chunks]
            embeddings = self._embedding_port.embed_texts(texts)

            # Étape 2 : Enrichir les chunks avec leurs embeddings
            for chunk, embedding in zip(document.chunks, embeddings):
                chunk.embedding = embedding
                chunk.metadata["document_id"] = document.id
                chunk.metadata["filename"] = document.filename

            # Étape 3 : Stocker dans la base vectorielle
            self._vector_store_port.add_chunks(document.chunks, document.id)

            logger.info(
                f"Document {document.filename} indexé avec succès "
                f"({document.chunks_count} chunks)"
            )

            return document

        except EmbeddingError as e:
            logger.error(f"Erreur génération embeddings: {e}")
            raise IndexError(f"Échec génération embeddings: {e}")

        except VectorStoreError as e:
            logger.error(f"Erreur stockage vectoriel: {e}")
            raise IndexError(f"Échec stockage: {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'indexation: {e}")
            raise IndexError(f"Erreur inattendue: {e}")


class IndexError(Exception):
    """Exception levée lors d'une erreur d'indexation."""
    pass
