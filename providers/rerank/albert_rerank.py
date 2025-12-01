"""
Module de reranking utilisant l'API Albert d'Etalab.
Permet de réordonner les résultats RAG par pertinence.
"""

import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
import requests


@dataclass
class RerankResult:
    """Résultat du reranking d'un document."""
    index: int           # Index original dans la liste
    score: float         # Score de pertinence (0.0 - 1.0)
    text: str            # Contenu du document


class AlbertReranker:
    """
    Reranker utilisant l'API Albert d'Etalab.
    Utilise le modèle rerank-small pour réordonner les résultats.
    """

    DEFAULT_MODEL = "rerank-small"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialise le reranker Albert.

        Args:
            api_key: Clé API Albert (ou variable d'env ALBERT_API_KEY)
            base_url: URL de l'API Albert
            model: Nom du modèle de reranking
        """
        self._api_key = api_key or os.getenv("ALBERT_API_KEY")
        if not self._api_key:
            raise ValueError(
                "ALBERT_API_KEY est requis. "
                "Définissez-le dans .env ou passez-le en paramètre."
            )

        self._base_url = base_url.rstrip("/")
        self._model = model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        min_score: float = 0.0,
    ) -> List[RerankResult]:
        """
        Réordonne une liste de documents par pertinence par rapport à la requête.

        Args:
            query: Requête de l'utilisateur
            documents: Liste des documents à réordonner
            top_k: Nombre maximum de documents à retourner (None = tous)
            min_score: Score minimum pour garder un document

        Returns:
            Liste de RerankResult triés par score décroissant
        """
        if not documents:
            return []

        # Appel à l'API de reranking
        response = requests.post(
            f"{self._base_url}/rerank",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "query": query,
                "documents": documents,
            },
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()

        # Construire les résultats
        results = []
        for item in data.get("results", []):
            idx = item["index"]
            score = item["relevance_score"]

            if score >= min_score:
                results.append(
                    RerankResult(
                        index=idx,
                        score=score,
                        text=documents[idx],
                    )
                )

        # Trier par score décroissant
        results.sort(key=lambda x: x.score, reverse=True)

        # Limiter le nombre de résultats
        if top_k is not None:
            results = results[:top_k]

        return results

    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Tuple[str, dict]],
        top_k: Optional[int] = None,
        min_score: float = 0.0,
    ) -> List[Tuple[RerankResult, dict]]:
        """
        Réordonne des documents avec leurs métadonnées.

        Args:
            query: Requête de l'utilisateur
            documents: Liste de tuples (texte, metadata)
            top_k: Nombre maximum de documents à retourner
            min_score: Score minimum

        Returns:
            Liste de tuples (RerankResult, metadata) triés par score
        """
        if not documents:
            return []

        texts = [doc[0] for doc in documents]
        metadata_list = [doc[1] for doc in documents]

        results = self.rerank(query, texts, top_k, min_score)

        return [
            (result, metadata_list[result.index])
            for result in results
        ]

    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model
