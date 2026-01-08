"""
Use Case : Requête RAG (Retrieval-Augmented Generation)
Architecture Hexagonale : Application Layer
"""

import logging
from typing import List, Optional, Dict

from ...domain.entities.query import Query, RAGResponse, SearchResult
from ...domain.ports.embedding_port import EmbeddingPort, EmbeddingError
from ...domain.ports.vector_store_port import VectorStorePort, VectorStoreError
from ...domain.ports.llm_port import LLMPort, LLMError


logger = logging.getLogger(__name__)


class QueryRAGUseCase:
    """Use case pour répondre à une requête avec augmentation RAG."""

    def __init__(
        self,
        embedding_port: EmbeddingPort,
        vector_store_port: VectorStorePort,
        llm_port: LLMPort
    ):
        """
        Initialise le use case avec injection de dépendances.

        Args:
            embedding_port: Port pour générer les embeddings
            vector_store_port: Port pour rechercher dans la base vectorielle
            llm_port: Port pour générer la réponse avec le LLM
        """
        self._embedding_port = embedding_port
        self._vector_store_port = vector_store_port
        self._llm_port = llm_port

    def execute(
        self,
        query_text: str,
        n_results: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        filter_metadata: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Répond à une requête avec augmentation RAG.

        Args:
            query_text: Texte de la requête
            n_results: Nombre de résultats à récupérer
            temperature: Température LLM (0-1)
            max_tokens: Nombre max de tokens
            filter_metadata: Filtres sur les métadonnées

        Returns:
            Réponse RAG complète avec sources

        Raises:
            RAGError: Si le traitement échoue
        """
        # Validation de la requête
        try:
            query = Query(text=query_text)
        except ValueError as e:
            raise RAGError(f"Requête invalide: {e}")

        logger.info(
            f"Requête RAG : '{query_text[:50]}...' "
            f"(n_results={n_results}, temp={temperature})"
        )

        try:
            # Étape 1 : Générer l'embedding de la requête
            query_embedding = self._embedding_port.embed_text(query_text)
            query.embedding = query_embedding

            # Étape 2 : Rechercher les chunks pertinents
            search_results = self._vector_store_port.search_similar(
                query_embedding=query_embedding,
                n_results=n_results,
                filter_metadata=filter_metadata
            )

            if not search_results:
                logger.warning("Aucun contexte trouvé pour la requête")
                # Possibilité de retourner une réponse vide ou lever une erreur
                context_text = "Aucun contexte disponible."
            else:
                # Étape 3 : Construire le contexte à partir des résultats
                context_text = self._build_context(search_results)

            # Étape 4 : Construire le prompt augmenté
            system_prompt = self._build_system_prompt()
            augmented_prompt = self._build_augmented_prompt(query_text, context_text)

            # Étape 5 : Générer la réponse avec le LLM
            response_text = self._llm_port.generate(
                prompt=augmented_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Étape 6 : Construire la réponse RAG
            rag_response = RAGResponse(
                query=query,
                response_text=response_text,
                sources=search_results,
                context_used=context_text,
                model_name=self._llm_port.get_model_name()
            )

            logger.info(
                f"Réponse RAG générée "
                f"({len(search_results)} sources, {len(response_text)} caractères)"
            )

            return rag_response

        except EmbeddingError as e:
            logger.error(f"Erreur génération embedding: {e}")
            raise RAGError(f"Échec génération embedding: {e}")

        except VectorStoreError as e:
            logger.error(f"Erreur recherche vectorielle: {e}")
            raise RAGError(f"Échec recherche: {e}")

        except LLMError as e:
            logger.error(f"Erreur génération LLM: {e}")
            raise RAGError(f"Échec génération réponse: {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue lors du traitement RAG: {e}")
            raise RAGError(f"Erreur inattendue: {e}")

    def _build_context(self, search_results: List[SearchResult]) -> str:
        """
        Construit le contexte textuel à partir des résultats de recherche.

        Args:
            search_results: Résultats de la recherche

        Returns:
            Contexte formaté
        """
        context_parts = []
        for i, result in enumerate(search_results, 1):
            filename = result.metadata.get("filename", "unknown")
            context_parts.append(
                f"[DOCUMENT {i} - Source: {filename}]\n"
                f"{result.text}\n"
                f"[FIN DOCUMENT {i}]"
            )

        return "\n\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """Construit le prompt système pour le LLM."""
        return (
            "Tu es un assistant IA qui répond aux questions en te basant "
            "sur les documents fournis. "
            "Réponds en français de manière claire et concise. "
            "Si l'information n'est pas dans les documents, indique-le clairement."
        )

    def _build_augmented_prompt(self, query: str, context: str) -> str:
        """
        Construit le prompt augmenté avec le contexte RAG.

        Args:
            query: Question de l'utilisateur
            context: Contexte extrait des documents

        Returns:
            Prompt augmenté
        """
        return (
            f"Contexte (documents) :\n\n{context}\n\n"
            f"---\n\n"
            f"Question de l'utilisateur : {query}\n\n"
            f"Réponds à la question en te basant sur le contexte ci-dessus. "
            f"Cite les sources (nom des documents) dans ta réponse."
        )


class RAGError(Exception):
    """Exception levée lors d'une erreur de traitement RAG."""
    pass
