"""
Tests unitaires pour les providers d'embeddings.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.embeddings.base import EmbeddingProvider
from providers.embeddings.ollama import OllamaEmbeddings
from providers.embeddings.albert import AlbertEmbeddings


class TestEmbeddingProviderInterface:
    """Tests pour l'interface abstraite EmbeddingProvider."""

    def test_cannot_instantiate_abstract_class(self):
        """Vérifie qu'on ne peut pas instancier la classe abstraite."""
        with pytest.raises(TypeError):
            EmbeddingProvider()

    def test_concrete_class_must_implement_methods(self):
        """Vérifie que les classes concrètes doivent implémenter les méthodes."""
        class IncompleteProvider(EmbeddingProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()


class TestOllamaEmbeddings:
    """Tests pour le provider Ollama."""

    @patch('providers.embeddings.ollama.ollama')
    def test_init_default_params(self, mock_ollama):
        """Test d'initialisation avec paramètres par défaut."""
        provider = OllamaEmbeddings()

        assert provider.model_name == "nomic-embed-text"
        assert provider.dimension == 768
        assert provider._client is None  # Utilise le client par défaut

    @patch('providers.embeddings.ollama.ollama')
    def test_init_custom_params(self, mock_ollama):
        """Test d'initialisation avec paramètres personnalisés."""
        mock_ollama.Client.return_value = MagicMock()

        provider = OllamaEmbeddings(
            model="mxbai-embed-large",
            base_url="http://custom:11434"
        )

        assert provider.model_name == "mxbai-embed-large"
        assert provider.dimension == 1024
        assert provider._client is not None

    @patch('providers.embeddings.ollama.ollama')
    def test_embed_query(self, mock_ollama):
        """Test de la génération d'embedding pour une requête."""
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        provider = OllamaEmbeddings()
        result = provider.embed_query("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_ollama.embeddings.assert_called_once_with(
            model="nomic-embed-text",
            prompt="test query"
        )

    @patch('providers.embeddings.ollama.ollama')
    def test_embed_documents(self, mock_ollama):
        """Test de la génération d'embeddings pour des documents."""
        mock_ollama.embeddings.side_effect = [
            {"embedding": [0.1, 0.2]},
            {"embedding": [0.3, 0.4]}
        ]

        provider = OllamaEmbeddings()
        result = provider.embed_documents(["doc1", "doc2"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        assert mock_ollama.embeddings.call_count == 2

    @patch('providers.embeddings.ollama.ollama')
    def test_get_langchain_embeddings_returns_self(self, mock_ollama):
        """Test que get_langchain_embeddings retourne self."""
        provider = OllamaEmbeddings()

        assert provider.get_langchain_embeddings() is provider

    def test_known_dimensions(self):
        """Test des dimensions connues des modèles."""
        assert OllamaEmbeddings.KNOWN_DIMENSIONS["nomic-embed-text"] == 768
        assert OllamaEmbeddings.KNOWN_DIMENSIONS["mxbai-embed-large"] == 1024
        assert OllamaEmbeddings.KNOWN_DIMENSIONS["all-minilm"] == 384


class TestAlbertEmbeddings:
    """Tests pour le provider Albert."""

    def test_init_without_api_key_raises(self):
        """Test qu'une erreur est levée sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            # S'assurer que ALBERT_API_KEY n'est pas défini
            if "ALBERT_API_KEY" in os.environ:
                del os.environ["ALBERT_API_KEY"]

            with pytest.raises(ValueError, match="ALBERT_API_KEY est requis"):
                AlbertEmbeddings()

    @patch('providers.embeddings.albert.OpenAI')
    def test_init_with_api_key_param(self, mock_openai):
        """Test d'initialisation avec clé API en paramètre."""
        provider = AlbertEmbeddings(api_key="test-key")

        assert provider.model_name == "embeddings-small"
        assert provider.dimension == 1536
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.albert.gouv.fr/v1",
        )

    @patch('providers.embeddings.albert.OpenAI')
    def test_init_with_env_api_key(self, mock_openai):
        """Test d'initialisation avec clé API depuis l'environnement."""
        with patch.dict(os.environ, {"ALBERT_API_KEY": "env-key"}):
            provider = AlbertEmbeddings()

            mock_openai.assert_called_once_with(
                api_key="env-key",
                base_url="https://api.albert.gouv.fr/v1",
            )

    @patch('providers.embeddings.albert.OpenAI')
    def test_embed_query(self, mock_openai_class):
        """Test de la génération d'embedding pour une requête."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AlbertEmbeddings(api_key="test-key")
        result = provider.embed_query("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once_with(
            model="embeddings-small",
            input="test query",
        )

    @patch('providers.embeddings.albert.OpenAI')
    def test_embed_documents(self, mock_openai_class):
        """Test de la génération d'embeddings pour des documents."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Simuler la réponse avec les index
        mock_response.data = [
            MagicMock(index=0, embedding=[0.1, 0.2]),
            MagicMock(index=1, embedding=[0.3, 0.4]),
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AlbertEmbeddings(api_key="test-key")
        result = provider.embed_documents(["doc1", "doc2"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_client.embeddings.create.assert_called_once_with(
            model="embeddings-small",
            input=["doc1", "doc2"],
        )

    @patch('providers.embeddings.albert.OpenAI')
    def test_embed_documents_empty_list(self, mock_openai_class):
        """Test avec une liste vide."""
        provider = AlbertEmbeddings(api_key="test-key")
        result = provider.embed_documents([])

        assert result == []
        mock_openai_class.return_value.embeddings.create.assert_not_called()

    @patch('providers.embeddings.albert.OpenAI')
    def test_get_langchain_embeddings_returns_self(self, mock_openai):
        """Test que get_langchain_embeddings retourne self."""
        provider = AlbertEmbeddings(api_key="test-key")

        assert provider.get_langchain_embeddings() is provider


class TestCosineSimlarity:
    """Tests pour la fonction de similarité cosinus."""

    @patch('providers.embeddings.ollama.ollama')
    def test_cosine_similarity_identical_vectors(self, mock_ollama):
        """Test de similarité avec vecteurs identiques."""
        provider = OllamaEmbeddings()
        vec = [1.0, 0.0, 0.0]

        similarity = provider.cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 0.0001

    @patch('providers.embeddings.ollama.ollama')
    def test_cosine_similarity_orthogonal_vectors(self, mock_ollama):
        """Test de similarité avec vecteurs orthogonaux."""
        provider = OllamaEmbeddings()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = provider.cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.0001

    @patch('providers.embeddings.ollama.ollama')
    def test_cosine_similarity_opposite_vectors(self, mock_ollama):
        """Test de similarité avec vecteurs opposés."""
        provider = OllamaEmbeddings()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]

        similarity = provider.cosine_similarity(vec1, vec2)

        assert abs(similarity + 1.0) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
