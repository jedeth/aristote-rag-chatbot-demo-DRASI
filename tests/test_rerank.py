"""
Tests unitaires pour le module de reranking.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.rerank.albert_rerank import AlbertReranker, RerankResult


class TestRerankResult:
    """Tests pour la dataclass RerankResult."""

    def test_create_rerank_result(self):
        """Test de création d'un RerankResult."""
        result = RerankResult(index=0, score=0.95, text="Test document")

        assert result.index == 0
        assert result.score == 0.95
        assert result.text == "Test document"


class TestAlbertReranker:
    """Tests pour le reranker Albert."""

    def test_init_without_api_key_raises(self):
        """Test qu'une erreur est levée sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ALBERT_API_KEY est requis"):
                AlbertReranker()

    def test_init_with_api_key(self):
        """Test d'initialisation avec clé API."""
        reranker = AlbertReranker(api_key="test-key")

        assert reranker.model_name == "rerank-small"

    def test_init_custom_model(self):
        """Test d'initialisation avec modèle personnalisé."""
        reranker = AlbertReranker(api_key="test-key", model="custom-rerank")

        assert reranker.model_name == "custom-rerank"

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_empty_documents(self, mock_post):
        """Test du reranking avec liste vide."""
        reranker = AlbertReranker(api_key="test-key")
        results = reranker.rerank("query", [])

        assert results == []
        mock_post.assert_not_called()

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_success(self, mock_post):
        """Test du reranking avec succès."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.80},
                {"index": 2, "relevance_score": 0.60},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = AlbertReranker(api_key="test-key")
        documents = ["doc1", "doc2", "doc3"]
        results = reranker.rerank("test query", documents)

        assert len(results) == 3
        # Vérifie que les résultats sont triés par score décroissant
        assert results[0].score == 0.95
        assert results[0].index == 1
        assert results[0].text == "doc2"
        assert results[1].score == 0.80
        assert results[2].score == 0.60

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_with_top_k(self, mock_post):
        """Test du reranking avec limite top_k."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 1, "relevance_score": 0.80},
                {"index": 2, "relevance_score": 0.60},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = AlbertReranker(api_key="test-key")
        documents = ["doc1", "doc2", "doc3"]
        results = reranker.rerank("query", documents, top_k=2)

        assert len(results) == 2

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_with_min_score(self, mock_post):
        """Test du reranking avec score minimum."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 1, "relevance_score": 0.50},
                {"index": 2, "relevance_score": 0.30},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = AlbertReranker(api_key="test-key")
        documents = ["doc1", "doc2", "doc3"]
        results = reranker.rerank("query", documents, min_score=0.5)

        assert len(results) == 2  # Seulement les docs avec score >= 0.5
        assert all(r.score >= 0.5 for r in results)

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_api_call_params(self, mock_post):
        """Test des paramètres de l'appel API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = AlbertReranker(
            api_key="test-key",
            base_url="https://custom.api.com/v1"
        )
        reranker.rerank("my query", ["doc1", "doc2"])

        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Vérifier l'URL
        assert call_args[0][0] == "https://custom.api.com/v1/rerank"

        # Vérifier les headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"

        # Vérifier le body
        json_data = call_args[1]["json"]
        assert json_data["model"] == "rerank-small"
        assert json_data["query"] == "my query"
        assert json_data["documents"] == ["doc1", "doc2"]

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_with_metadata(self, mock_post):
        """Test du reranking avec métadonnées."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 1, "relevance_score": 0.9},
                {"index": 0, "relevance_score": 0.7},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = AlbertReranker(api_key="test-key")
        documents = [
            ("doc1 content", {"source": "file1.pdf"}),
            ("doc2 content", {"source": "file2.pdf"}),
        ]
        results = reranker.rerank_with_metadata("query", documents)

        assert len(results) == 2
        # Premier résultat (meilleur score)
        assert results[0][0].text == "doc2 content"
        assert results[0][1]["source"] == "file2.pdf"
        # Second résultat
        assert results[1][0].text == "doc1 content"
        assert results[1][1]["source"] == "file1.pdf"

    @patch('providers.rerank.albert_rerank.requests.post')
    def test_rerank_with_metadata_empty(self, mock_post):
        """Test du reranking avec métadonnées sur liste vide."""
        reranker = AlbertReranker(api_key="test-key")
        results = reranker.rerank_with_metadata("query", [])

        assert results == []
        mock_post.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
