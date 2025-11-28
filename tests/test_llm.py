"""
Tests unitaires pour les providers LLM.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.llm.base import LLMProvider
from providers.llm.aristote import AristoteLLM
from providers.llm.albert import AlbertLLM


class TestLLMProviderInterface:
    """Tests pour l'interface abstraite LLMProvider."""

    def test_cannot_instantiate_abstract_class(self):
        """Vérifie qu'on ne peut pas instancier la classe abstraite."""
        with pytest.raises(TypeError):
            LLMProvider()


class TestAristoteLLM:
    """Tests pour le provider Aristote."""

    def test_init_without_api_key_raises(self):
        """Test qu'une erreur est levée sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ARISTOTE_API_KEY est requis"):
                AristoteLLM()

    def test_init_without_base_url_raises(self):
        """Test qu'une erreur est levée sans URL de base."""
        with patch.dict(os.environ, {"ARISTOTE_API_KEY": "test-key"}, clear=True):
            with pytest.raises(ValueError, match="ARISTOTE_DISPATCHER_URL est requis"):
                AristoteLLM()

    @patch('providers.llm.aristote.OpenAI')
    def test_init_with_params(self, mock_openai):
        """Test d'initialisation avec paramètres."""
        provider = AristoteLLM(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model="test-model"
        )

        assert provider.model_name == "test-model"
        assert provider.provider_name == "aristote"
        assert provider.supports_streaming is True
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.test.com/v1",
        )

    @patch('providers.llm.aristote.OpenAI')
    def test_chat_non_streaming(self, mock_openai_class):
        """Test du chat sans streaming."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AristoteLLM(
            api_key="test-key",
            base_url="https://api.test.com/v1"
        )
        messages = [{"role": "user", "content": "Hello"}]
        result = provider.chat(messages, temperature=0.5, stream=False)

        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch('providers.llm.aristote.OpenAI')
    def test_chat_with_max_tokens(self, mock_openai_class):
        """Test du chat avec max_tokens."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AristoteLLM(
            api_key="test-key",
            base_url="https://api.test.com/v1"
        )
        provider.chat(
            [{"role": "user", "content": "Test"}],
            max_tokens=100,
            stream=False
        )

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_tokens"] == 100

    @patch('providers.llm.aristote.OpenAI')
    def test_complete(self, mock_openai_class):
        """Test de la méthode complete."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Completed text"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AristoteLLM(
            api_key="test-key",
            base_url="https://api.test.com/v1"
        )
        result = provider.complete("Complete this:")

        assert result == "Completed text"

    @patch('providers.llm.aristote.OpenAI')
    def test_chat_streaming(self, mock_openai_class):
        """Test du chat avec streaming."""
        mock_client = MagicMock()

        # Simuler les chunks de streaming
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content=" World"))]
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock(delta=MagicMock(content=None))]

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2, chunk3])
        mock_openai_class.return_value = mock_client

        provider = AristoteLLM(
            api_key="test-key",
            base_url="https://api.test.com/v1"
        )
        result = provider.chat(
            [{"role": "user", "content": "Hi"}],
            stream=True
        )

        # Consommer le générateur
        tokens = list(result)
        assert tokens == ["Hello", " World"]


class TestAlbertLLM:
    """Tests pour le provider Albert."""

    def test_init_without_api_key_raises(self):
        """Test qu'une erreur est levée sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ALBERT_API_KEY est requis"):
                AlbertLLM()

    @patch('providers.llm.albert.OpenAI')
    def test_init_with_api_key(self, mock_openai):
        """Test d'initialisation avec clé API."""
        provider = AlbertLLM(api_key="test-key")

        assert provider.model_name == "albert-large"
        assert provider.provider_name == "albert"
        assert provider.supports_streaming is True
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.albert.gouv.fr/v1",
        )

    @patch('providers.llm.albert.OpenAI')
    def test_init_custom_model(self, mock_openai):
        """Test d'initialisation avec modèle personnalisé."""
        provider = AlbertLLM(api_key="test-key", model="albert-code")

        assert provider.model_name == "albert-code"

    @patch('providers.llm.albert.OpenAI')
    def test_list_models(self, mock_openai):
        """Test de la liste des modèles disponibles."""
        models = AlbertLLM.list_models()

        assert "albert-small" in models
        assert "albert-large" in models
        assert "albert-code" in models
        assert len(models) == 3

    @patch('providers.llm.albert.OpenAI')
    def test_chat_non_streaming(self, mock_openai_class):
        """Test du chat sans streaming."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Albert response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = AlbertLLM(api_key="test-key")
        result = provider.chat(
            [{"role": "user", "content": "Hello Albert"}],
            stream=False
        )

        assert result == "Albert response"

    @patch('providers.llm.albert.OpenAI')
    def test_available_models_constant(self, mock_openai):
        """Test des modèles disponibles."""
        assert AlbertLLM.AVAILABLE_MODELS["albert-small"] == "albert-small"
        assert AlbertLLM.AVAILABLE_MODELS["albert-large"] == "albert-large"
        assert AlbertLLM.AVAILABLE_MODELS["albert-code"] == "albert-code"


class TestLLMProviderProperties:
    """Tests des propriétés communes aux providers."""

    @patch('providers.llm.aristote.OpenAI')
    def test_aristote_properties(self, mock_openai):
        """Test des propriétés Aristote."""
        provider = AristoteLLM(
            api_key="key",
            base_url="https://api.test.com/v1",
            model="custom-model"
        )

        assert provider.model_name == "custom-model"
        assert provider.provider_name == "aristote"
        assert provider.supports_streaming is True

    @patch('providers.llm.albert.OpenAI')
    def test_albert_properties(self, mock_openai):
        """Test des propriétés Albert."""
        provider = AlbertLLM(api_key="key", model="albert-code")

        assert provider.model_name == "albert-code"
        assert provider.provider_name == "albert"
        assert provider.supports_streaming is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
