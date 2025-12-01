"""
Tests unitaires pour l'extracteur d'images PDF.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.vision.pdf_image_extractor import (
    PDFImageExtractor,
    ExtractedImage,
    AnalyzedImage,
    extract_pdf_with_vision,
)


class TestExtractedImage:
    """Tests pour la dataclass ExtractedImage."""

    def test_create_extracted_image(self):
        """Test de création d'une ExtractedImage."""
        img = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake image",
            width=800,
            height=600,
            image_type="png",
            bbox=(0, 0, 800, 600),
        )

        assert img.page_number == 1
        assert img.image_index == 0
        assert img.width == 800
        assert img.height == 600
        assert img.image_type == "png"


class TestAnalyzedImage:
    """Tests pour la dataclass AnalyzedImage."""

    def test_create_analyzed_image(self):
        """Test de création d'une AnalyzedImage."""
        extracted = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=400,
            height=300,
            image_type="png",
            bbox=(0, 0, 400, 300),
        )

        analyzed = AnalyzedImage(
            extracted_image=extracted,
            description="A chart showing sales data",
            is_table=False,
            is_chart=True,
            extracted_data=None,
        )

        assert analyzed.is_chart is True
        assert analyzed.is_table is False
        assert "sales" in analyzed.description


class TestPDFImageExtractor:
    """Tests pour PDFImageExtractor."""

    def test_init_without_vision(self):
        """Test d'initialisation sans provider de vision."""
        extractor = PDFImageExtractor()

        assert extractor.vision is None
        assert extractor.analyze_tables is True
        assert extractor.analyze_charts is True

    @patch('providers.vision.albert_vision.OpenAI')
    def test_init_with_vision(self, mock_openai):
        """Test d'initialisation avec provider de vision."""
        from providers.vision import AlbertVision
        vision = AlbertVision(api_key="test-key")

        extractor = PDFImageExtractor(vision_provider=vision)

        assert extractor.vision is not None

    def test_init_custom_params(self):
        """Test d'initialisation avec paramètres personnalisés."""
        extractor = PDFImageExtractor(
            analyze_tables=False,
            analyze_charts=False,
            min_width=200,
            min_height=200,
        )

        assert extractor.analyze_tables is False
        assert extractor.analyze_charts is False
        assert extractor.min_width == 200
        assert extractor.min_height == 200

    def test_classify_image_table_heuristic(self):
        """Test de classification heuristique - tableau."""
        extractor = PDFImageExtractor()

        # Image large (typique d'un tableau)
        table_image = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=800,
            height=400,
            image_type="png",
            bbox=(0, 0, 800, 400),
        )

        is_table, is_chart = extractor.classify_image(table_image)

        assert is_table is True  # Aspect ratio > 1.2 et width > 300

    def test_classify_image_chart_heuristic(self):
        """Test de classification heuristique - graphique."""
        extractor = PDFImageExtractor()

        # Image carrée (typique d'un graphique)
        chart_image = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=400,
            height=400,
            image_type="png",
            bbox=(0, 0, 400, 400),
        )

        is_table, is_chart = extractor.classify_image(chart_image)

        assert is_chart is True

    def test_analyze_image_without_vision(self):
        """Test d'analyse sans provider de vision."""
        extractor = PDFImageExtractor()

        image = ExtractedImage(
            page_number=2,
            image_index=1,
            image_bytes=b"fake",
            width=500,
            height=300,
            image_type="png",
            bbox=(0, 0, 500, 300),
        )

        analyzed = extractor.analyze_image(image)

        assert analyzed.description == "Image page 2 (500x300)"
        assert analyzed.is_table is False
        assert analyzed.is_chart is False

    @patch('providers.vision.albert_vision.OpenAI')
    def test_analyze_image_as_table(self, mock_openai_class):
        """Test d'analyse d'une image comme tableau."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="| Col1 | Col2 |\n|---|---|\n| A | B |"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        from providers.vision import AlbertVision
        vision = AlbertVision(api_key="test-key")
        extractor = PDFImageExtractor(vision_provider=vision)

        image = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=800,
            height=400,
            image_type="png",
            bbox=(0, 0, 800, 400),
        )

        analyzed = extractor.analyze_image(image, force_table=True)

        assert analyzed.is_table is True
        assert analyzed.extracted_data is not None

    def test_generate_image_chunks_table(self):
        """Test de génération de chunks pour un tableau."""
        extractor = PDFImageExtractor()

        extracted = ExtractedImage(
            page_number=3,
            image_index=0,
            image_bytes=b"fake",
            width=600,
            height=400,
            image_type="png",
            bbox=(0, 0, 600, 400),
        )

        analyzed_images = [
            AnalyzedImage(
                extracted_image=extracted,
                description="Budget table",
                is_table=True,
                is_chart=False,
                extracted_data="| Item | Cost |\n|---|---|\n| A | 100 |",
            )
        ]

        chunks = extractor.generate_image_chunks(analyzed_images, "report.pdf")

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["type"] == "table"
        assert chunks[0]["metadata"]["filename"] == "report.pdf"
        assert chunks[0]["metadata"]["page"] == 3
        assert chunks[0]["metadata"]["is_visual_content"] is True
        assert "[TABLEAU" in chunks[0]["text"]

    def test_generate_image_chunks_chart(self):
        """Test de génération de chunks pour un graphique."""
        extractor = PDFImageExtractor()

        extracted = ExtractedImage(
            page_number=5,
            image_index=0,
            image_bytes=b"fake",
            width=400,
            height=400,
            image_type="png",
            bbox=(0, 0, 400, 400),
        )

        analyzed_images = [
            AnalyzedImage(
                extracted_image=extracted,
                description="Bar chart showing quarterly sales",
                is_table=False,
                is_chart=True,
                extracted_data=None,
            )
        ]

        chunks = extractor.generate_image_chunks(analyzed_images, "report.pdf")

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["type"] == "chart"
        assert "[GRAPHIQUE" in chunks[0]["text"]

    def test_generate_image_chunks_generic_image(self):
        """Test de génération de chunks pour une image générique."""
        extractor = PDFImageExtractor()

        extracted = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=200,
            height=200,
            image_type="jpeg",
            bbox=(0, 0, 200, 200),
        )

        analyzed_images = [
            AnalyzedImage(
                extracted_image=extracted,
                description="Company logo",
                is_table=False,
                is_chart=False,
                extracted_data=None,
            )
        ]

        chunks = extractor.generate_image_chunks(analyzed_images, "doc.pdf")

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["type"] == "image"
        assert "[IMAGE" in chunks[0]["text"]


class TestExtractPdfWithVision:
    """Tests pour la fonction utilitaire extract_pdf_with_vision."""

    @patch('providers.vision.pdf_image_extractor.fitz.open')
    def test_extract_text_only(self, mock_fitz_open):
        """Test d'extraction texte sans vision."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Page text content"
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc

        text, image_chunks = extract_pdf_with_vision(
            pdf_bytes=b"fake pdf",
            document_name="test.pdf",
            vision_api_key=None,  # Pas de vision
        )

        assert "Page text content" in text
        assert image_chunks == []

    @patch('providers.vision.pdf_image_extractor.PDFImageExtractor.extract_and_analyze_all')
    @patch('providers.vision.pdf_image_extractor.AlbertVision')
    @patch('providers.vision.pdf_image_extractor.fitz.open')
    def test_extract_with_vision(self, mock_fitz_open, mock_vision_class, mock_extract):
        """Test d'extraction avec vision."""
        # Mock fitz
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Text content"
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc

        # Mock vision
        mock_vision_class.return_value = MagicMock()

        # Mock extraction d'images
        extracted = ExtractedImage(
            page_number=1,
            image_index=0,
            image_bytes=b"fake",
            width=400,
            height=300,
            image_type="png",
            bbox=(0, 0, 400, 300),
        )
        mock_extract.return_value = [
            AnalyzedImage(
                extracted_image=extracted,
                description="Test image",
                is_table=False,
                is_chart=False,
                extracted_data=None,
            )
        ]

        text, image_chunks = extract_pdf_with_vision(
            pdf_bytes=b"fake pdf",
            document_name="test.pdf",
            vision_api_key="test-key",
        )

        assert "Text content" in text
        assert len(image_chunks) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
