"""
Adapter ChromaDB - Implémente VectorStorePort
Architecture Hexagonale : Infrastructure Layer
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

from ...domain.entities.document import Chunk
from ...domain.entities.query import SearchResult
from ...domain.ports.vector_store_port import VectorStorePort, VectorStoreError


logger = logging.getLogger(__name__)


class ChromaDBAdapter(VectorStorePort):
    """Adapter pour ChromaDB - implémente l'interface VectorStorePort."""

    def __init__(self, persist_directory: str, collection_name: str = "documents"):
        """
        Initialise l'adapter ChromaDB.

        Args:
            persist_directory: Chemin du répertoire de persistance
            collection_name: Nom de la collection (défaut: "documents")
        """
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._client = None
        self._collection = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialise le client ChromaDB."""
        try:
            self._client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(
                f"ChromaDB initialisé : {self._persist_directory} "
                f"(collection: {self._collection_name})"
            )
        except Exception as e:
            logger.error(f"Erreur initialisation ChromaDB: {e}")
            raise VectorStoreError(f"Impossible d'initialiser ChromaDB: {e}")

    def add_chunks(self, chunks: List[Chunk], document_id: str) -> None:
        """
        Ajoute des chunks à la base vectorielle.

        Args:
            chunks: Liste de chunks avec embeddings
            document_id: ID du document source

        Raises:
            VectorStoreError: Si l'ajout échoue
        """
        if not chunks:
            raise VectorStoreError("La liste de chunks est vide")

        try:
            # Préparer les données pour ChromaDB
            ids = [chunk.id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = [
                {**chunk.metadata, "document_id": document_id}
                for chunk in chunks
            ]

            # Vérifier que tous les embeddings sont présents
            if any(emb is None for emb in embeddings):
                raise VectorStoreError("Certains chunks n'ont pas d'embedding")

            # Ajouter à ChromaDB
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"{len(chunks)} chunks ajoutés (document: {document_id})")

        except VectorStoreError:
            raise
        except Exception as e:
            logger.error(f"Erreur ajout chunks ChromaDB: {e}")
            raise VectorStoreError(f"Échec ajout chunks: {e}")

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
            n_results: Nombre de résultats
            filter_metadata: Filtres sur les métadonnées

        Returns:
            Liste de résultats triés par pertinence

        Raises:
            VectorStoreError: Si la recherche échoue
        """
        if not query_embedding:
            raise VectorStoreError("L'embedding de la requête est vide")

        try:
            # Requête ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )

            # Vérifier si des résultats existent
            if not results or not results.get("ids") or not results["ids"][0]:
                logger.info("Aucun résultat trouvé")
                return []

            # Convertir en SearchResult
            search_results = []
            ids = results["ids"][0]
            documents = results["documents"][0]
            distances = results["distances"][0]
            metadatas = results.get("metadatas", [[]])[0]

            for chunk_id, text, distance, metadata in zip(
                ids, documents, distances, metadatas
            ):
                # ChromaDB retourne une distance (0 = identique, 2 = opposé)
                # On convertit en score de similarité (0-1)
                score = 1.0 - (distance / 2.0)
                score = max(0.0, min(1.0, score))  # Clamp entre 0 et 1

                search_results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        text=text,
                        score=score,
                        metadata=metadata or {}
                    )
                )

            logger.info(f"{len(search_results)} résultats trouvés")
            return search_results

        except VectorStoreError:
            raise
        except Exception as e:
            logger.error(f"Erreur recherche ChromaDB: {e}")
            raise VectorStoreError(f"Échec recherche: {e}")

    def delete_document(self, document_id: str) -> None:
        """
        Supprime tous les chunks d'un document.

        Args:
            document_id: ID du document à supprimer

        Raises:
            VectorStoreError: Si la suppression échoue
        """
        try:
            # Supprimer tous les chunks ayant ce document_id dans les métadonnées
            self._collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"Document {document_id} supprimé")

        except Exception as e:
            logger.error(f"Erreur suppression document ChromaDB: {e}")
            raise VectorStoreError(f"Échec suppression: {e}")

    def count_chunks(self) -> int:
        """
        Retourne le nombre total de chunks indexés.

        Returns:
            Nombre de chunks
        """
        try:
            return self._collection.count()
        except Exception as e:
            logger.error(f"Erreur comptage ChromaDB: {e}")
            raise VectorStoreError(f"Échec comptage: {e}")

    def get_indexed_documents(self) -> List[str]:
        """
        Retourne la liste des documents indexés.

        Returns:
            Liste des noms de fichiers (uniques)
        """
        try:
            if self._collection.count() == 0:
                return []

            # Récupérer tous les métadonnées
            results = self._collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])

            # Extraire les noms de fichiers uniques
            filenames = set()
            for metadata in metadatas:
                if metadata and "filename" in metadata:
                    filenames.add(metadata["filename"])

            return list(filenames)

        except Exception as e:
            logger.error(f"Erreur liste documents ChromaDB: {e}")
            raise VectorStoreError(f"Échec liste documents: {e}")

    def clear_all(self) -> None:
        """
        Supprime tous les chunks de la base.

        Raises:
            VectorStoreError: Si la suppression échoue
        """
        try:
            # Supprimer la collection et la recréer
            self._client.delete_collection(self._collection_name)
            self._collection = self._client.create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Base vectorielle vidée")

        except Exception as e:
            logger.error(f"Erreur reset ChromaDB: {e}")
            raise VectorStoreError(f"Échec reset: {e}")
