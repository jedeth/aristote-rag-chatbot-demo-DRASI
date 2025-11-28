"""
Provider d'embeddings utilisant Ollama local.
Utilise directement l'API Ollama sans dépendance externe.
"""

from typing import List
import ollama
from .base import EmbeddingProvider


class OllamaEmbeddings(EmbeddingProvider):
    """Provider d'embeddings utilisant Ollama local."""

    # Dimensions connues des modèles Ollama
    KNOWN_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "snowflake-arctic-embed": 1024,
    }

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialise le provider Ollama.

        Args:
            model: Nom du modèle d'embeddings (default: nomic-embed-text)
            base_url: URL de l'API Ollama (default: http://localhost:11434)
        """
        self._model = model
        self._base_url = base_url
        self._dimension = self.KNOWN_DIMENSIONS.get(model, 768)

        # Configurer le client Ollama si URL personnalisée
        if base_url != "http://localhost:11434":
            self._client = ollama.Client(host=base_url)
        else:
            self._client = None  # Utiliser le client par défaut

    def _get_embedding(self, text: str) -> List[float]:
        """Génère l'embedding pour un texte via Ollama."""
        if self._client:
            response = self._client.embeddings(model=self._model, prompt=text)
        else:
            response = ollama.embeddings(model=self._model, prompt=text)
        return response["embedding"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Génère les embeddings pour une liste de documents."""
        return [self._get_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Génère l'embedding pour une requête utilisateur."""
        return self._get_embedding(text)

    @property
    def dimension(self) -> int:
        """Retourne la dimension des vecteurs d'embeddings."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model

    def get_langchain_embeddings(self) -> "OllamaEmbeddings":
        """
        Retourne self car cette classe implémente l'interface LangChain.

        Returns:
            Self (compatible LangChain Embeddings)
        """
        return self
