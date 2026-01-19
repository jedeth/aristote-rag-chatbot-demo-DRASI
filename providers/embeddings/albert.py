"""
Provider d'embeddings utilisant l'API Albert d'Etalab.
Utilise le modèle openweight-embeddings (BAAI/bge-m3) via appels REST directs.
Gere les limites de tokens par batch processing.
"""

import os
import time
import logging
from typing import List, Optional
import requests
from .base import EmbeddingProvider


class AlbertEmbeddings(EmbeddingProvider):
    """Provider d'embeddings utilisant l'API Albert d'Etalab."""

    # Modele d'embeddings Albert
    DEFAULT_MODEL = "openweight-embeddings"  # Anciennement embeddings-small (BAAI/bge-m3)
    DIMENSION = 1024  # Dimension du modèle (confirme par API)

    # Limites de l'API Albert (conservatif pour éviter les erreurs)
    MAX_CHARS_PER_TEXT = 4000      # Limite par texte (réduit pour stabilité)
    MAX_TEXTS_PER_BATCH = 10       # Batch plus petit pour éviter les timeouts
    RETRY_ATTEMPTS = 5             # Plus de tentatives
    RETRY_DELAY = 2                # Delai entre tentatives (secondes)

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        model: str = DEFAULT_MODEL,
        max_chars_per_text: int = MAX_CHARS_PER_TEXT,
        batch_size: int = MAX_TEXTS_PER_BATCH,
    ):
        """
        Initialise le provider Albert.

        Args:
            api_key: Cle API Albert (ou variable d'env ALBERT_API_KEY)
            base_url: URL de l'API Albert
            model: Nom du modele d'embeddings
            max_chars_per_text: Limite de caracteres par texte
            batch_size: Nombre de textes par batch
        """
        self._api_key = api_key or os.getenv("ALBERT_API_KEY")
        if not self._api_key:
            raise ValueError(
                "ALBERT_API_KEY est requis. "
                "Definissez-le dans .env ou passez-le en parametre."
            )

        self._base_url = base_url.rstrip("/")
        self._model = model
        self._max_chars = max_chars_per_text
        self._batch_size = batch_size

    def _clean_text(self, text: str) -> str:
        """Nettoie un texte pour l'API (caractères spéciaux, etc.)."""
        import re
        # Remplacer les caractères de contrôle problématiques
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les espaces en début/fin
        return text.strip()

    def _truncate_text(self, text: str) -> str:
        """Nettoie et tronque un texte trop long pour l'API."""
        # D'abord nettoyer
        text = self._clean_text(text)

        if len(text) <= self._max_chars:
            return text
        # Tronquer en gardant le debut (plus informatif generalement)
        truncated = text[:self._max_chars]
        # Essayer de couper a un espace pour ne pas couper un mot
        last_space = truncated.rfind(' ')
        if last_space > self._max_chars * 0.8:
            truncated = truncated[:last_space]
        return truncated + "..."

    def _call_embeddings_api(self, input_data, attempt: int = 1) -> dict:
        """
        Appelle l'API embeddings d'Albert directement via requests.
        Avec retry automatique en cas d'erreur.
        """
        try:
            response = requests.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": input_data,
                    "encoding_format": "float",
                },
                timeout=120,  # Timeout plus long pour les gros batches
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_text = e.response.text if e.response else str(e)

            logging.warning(f"Albert API error {status_code}, attempt {attempt}: {error_text[:200]}")

            # Erreur 422 = probablement texte trop long ou trop de textes
            if status_code == 422:
                raise ValueError(f"Erreur de validation Albert API: {error_text}")

            # Erreur 429 = rate limit, retry avec délai croissant
            if status_code == 429 and attempt < self.RETRY_ATTEMPTS:
                wait_time = self.RETRY_DELAY * (attempt ** 2)  # Backoff exponentiel
                logging.warning(f"Albert API rate limit, waiting {wait_time}s...")
                time.sleep(wait_time)
                return self._call_embeddings_api(input_data, attempt + 1)

            # Erreur 5xx ou autre erreur serveur = retry
            if (status_code >= 500 or status_code == 0) and attempt < self.RETRY_ATTEMPTS:
                wait_time = self.RETRY_DELAY * attempt
                logging.warning(f"Albert API server error {status_code}, retry in {wait_time}s...")
                time.sleep(wait_time)
                return self._call_embeddings_api(input_data, attempt + 1)

            # Pour les autres erreurs, retry aussi
            if attempt < self.RETRY_ATTEMPTS:
                wait_time = self.RETRY_DELAY * attempt
                logging.warning(f"Albert API error, retry in {wait_time}s...")
                time.sleep(wait_time)
                return self._call_embeddings_api(input_data, attempt + 1)

            raise

        except requests.exceptions.Timeout:
            if attempt < self.RETRY_ATTEMPTS:
                wait_time = self.RETRY_DELAY * attempt
                logging.warning(f"Albert API timeout, retry {attempt} in {wait_time}s...")
                time.sleep(wait_time)
                return self._call_embeddings_api(input_data, attempt + 1)
            raise

        except requests.exceptions.RequestException as e:
            # Autres erreurs réseau
            if attempt < self.RETRY_ATTEMPTS:
                wait_time = self.RETRY_DELAY * attempt
                logging.warning(f"Albert API network error: {e}, retry in {wait_time}s...")
                time.sleep(wait_time)
                return self._call_embeddings_api(input_data, attempt + 1)
            raise

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genere les embeddings pour un petit batch de textes."""
        if not texts:
            return []

        # Tronquer les textes trop longs
        truncated_texts = [self._truncate_text(t) for t in texts]

        data = self._call_embeddings_api(truncated_texts)

        # Trier par index pour s'assurer de l'ordre
        embeddings = sorted(data.get("data", []), key=lambda x: x["index"])
        return [e["embedding"] for e in embeddings]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Genere les embeddings pour une liste de documents.
        Traite par batches pour respecter les limites de l'API.

        Args:
            texts: Liste de textes a encoder

        Returns:
            Liste de vecteurs d'embeddings
        """
        if not texts:
            return []

        all_embeddings = []
        total_batches = (len(texts) + self._batch_size - 1) // self._batch_size

        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            batch_num = i // self._batch_size + 1

            try:
                batch_embeddings = self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

                # Log de progression pour les gros documents
                if total_batches > 5 and batch_num % 5 == 0:
                    logging.info(f"Albert embeddings: batch {batch_num}/{total_batches}")

                # Petit delai entre les batches (500 RPM = ~8 req/sec max)
                if i + self._batch_size < len(texts):
                    time.sleep(0.1)

            except Exception as e:
                logging.error(f"Erreur batch {batch_num}/{total_batches}: {e}")
                # En cas d'erreur, essayer un par un
                for text in batch:
                    try:
                        single_embedding = self._embed_batch([text])
                        all_embeddings.extend(single_embedding)
                    except Exception as single_error:
                        logging.error(f"Erreur embedding individuel: {single_error}")
                        # Retourner un embedding zero en cas d'echec total
                        all_embeddings.append([0.0] * self.DIMENSION)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Genere l'embedding pour une requete utilisateur.

        Args:
            text: Texte de la requete

        Returns:
            Vecteur d'embedding
        """
        truncated = self._truncate_text(text)
        data = self._call_embeddings_api(truncated)
        return data["data"][0]["embedding"]

    @property
    def dimension(self) -> int:
        """Retourne la dimension des vecteurs d'embeddings."""
        return self.DIMENSION

    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model

    def get_langchain_embeddings(self) -> "AlbertEmbeddings":
        """
        Retourne self car cette classe implémente l'interface LangChain.

        Returns:
            Self (compatible LangChain Embeddings)
        """
        return self
