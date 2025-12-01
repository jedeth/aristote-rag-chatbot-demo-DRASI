"""
Tests unitaires pour le module de vision.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.vision.albert_vision import AlbertVision


class TestAlbertVision:
    """Tests pour le provider de vision Albert."""

    def test_init_without_api_key_raises(self):
        """Test qu'une erreur est levée sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ALBERT_API_KEY est requis"):
                AlbertVision()

    @patch('providers.vision.albert_vision.OpenAI')
    def test_init_with_api_key(self, mock_openai):
        """Test d'initialisation avec clé API."""
        vision = AlbertVision(api_key="test-key")

        assert vision.model_name == "albert-large"
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.albert.gouv.fr/v1",
        )

    @patch('providers.vision.albert_vision.OpenAI')
    def test_init_custom_model(self, mock_openai):
        """Test d'initialisation avec modèle personnalisé."""
        vision = AlbertVision(api_key="test-key", model="custom-vision")

        assert vision.model_name == "custom-vision"

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_with_url(self, mock_openai_class):
        """Test d'analyse d'image avec URL."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Image description"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        result = vision.analyze_image(
            "https://example.com/image.png",
            prompt="Describe this"
        )

        assert result == "Image description"
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["content"][1]["type"] == "image_url"
        assert messages[0]["content"][1]["image_url"]["url"] == "https://example.com/image.png"

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_with_bytes(self, mock_openai_class):
        """Test d'analyse d'image avec bytes."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Image from bytes"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        image_bytes = b"fake image content"
        result = vision.analyze_image(image_bytes, prompt="Analyze")

        assert result == "Image from bytes"
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        # Vérifie que c'est une URL base64
        image_url = messages[0]["content"][1]["image_url"]["url"]
        assert image_url.startswith("data:image/png;base64,")

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_with_file_path(self, mock_openai_class):
        """Test d'analyse d'image avec chemin de fichier."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Image from file"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Créer un fichier image temporaire
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake png content")
            temp_path = f.name

        try:
            vision = AlbertVision(api_key="test-key")
            result = vision.analyze_image(temp_path, prompt="Describe")

            assert result == "Image from file"
        finally:
            os.unlink(temp_path)

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_file_not_found(self, mock_openai):
        """Test avec fichier inexistant."""
        vision = AlbertVision(api_key="test-key")

        with pytest.raises(FileNotFoundError, match="Image non trouvée"):
            vision.analyze_image("/nonexistent/image.png")

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_table_extract_data(self, mock_openai_class):
        """Test d'analyse de tableau avec extraction de données."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="| Col1 | Col2 |\n|---|---|\n| A | B |"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        result = vision.analyze_table(
            "https://example.com/table.png",
            extract_data=True
        )

        assert "Col1" in result
        # Vérifier que le prompt demande l'extraction
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt_text = messages[0]["content"][0]["text"]
        assert "markdown" in prompt_text.lower()

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_table_describe(self, mock_openai_class):
        """Test d'analyse de tableau avec description."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This table shows sales data"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        result = vision.analyze_table(
            "https://example.com/table.png",
            extract_data=False
        )

        assert "sales" in result.lower()

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_chart(self, mock_openai_class):
        """Test d'analyse de graphique."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Bar chart showing revenue trends"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        result = vision.analyze_chart("https://example.com/chart.png")

        assert "revenue" in result.lower()
        # Vérifier le prompt spécifique aux graphiques
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt_text = messages[0]["content"][0]["text"]
        assert "graphique" in prompt_text.lower()

    @patch('providers.vision.albert_vision.OpenAI')
    def test_extract_text_from_image(self, mock_openai_class):
        """Test d'extraction de texte (OCR)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Extracted text content"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        result = vision.extract_text_from_image("https://example.com/doc.png")

        assert result == "Extracted text content"

    @patch('providers.vision.albert_vision.OpenAI')
    def test_prepare_image_mime_types(self, mock_openai):
        """Test de détection des types MIME."""
        vision = AlbertVision(api_key="test-key")

        # Créer des fichiers temporaires avec différentes extensions
        extensions = {".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif"}

        for ext, expected_mime in extensions.items():
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"fake content")
                temp_path = f.name

            try:
                result = vision._prepare_image(temp_path)
                assert expected_mime in result["image_url"]["url"]
            finally:
                os.unlink(temp_path)

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_default_prompt(self, mock_openai_class):
        """Test du prompt par défaut."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Description"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        vision = AlbertVision(api_key="test-key")
        vision.analyze_image("https://example.com/image.png")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt_text = messages[0]["content"][0]["text"]
        assert "Décris cette image" in prompt_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
