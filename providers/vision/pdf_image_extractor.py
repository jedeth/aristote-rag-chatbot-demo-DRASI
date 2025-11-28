"""
Module d'extraction et d'analyse des images depuis les fichiers PDF.
Utilise PyMuPDF (fitz) pour l'extraction et Albert Vision pour l'analyse.
"""

import fitz  # PyMuPDF
import io
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path

from .albert_vision import AlbertVision


@dataclass
class ExtractedImage:
    """Représente une image extraite d'un PDF."""
    page_number: int           # Numéro de page (1-indexed)
    image_index: int           # Index de l'image sur la page
    image_bytes: bytes         # Contenu de l'image
    width: int                 # Largeur en pixels
    height: int                # Hauteur en pixels
    image_type: str            # Type (png, jpeg, etc.)
    bbox: Tuple[float, float, float, float]  # Bounding box (x0, y0, x1, y1)


@dataclass
class AnalyzedImage:
    """Représente une image analysée avec sa description."""
    extracted_image: ExtractedImage
    description: str           # Description textuelle générée
    is_table: bool             # Est-ce un tableau ?
    is_chart: bool             # Est-ce un graphique ?
    extracted_data: Optional[str]  # Données extraites (markdown pour tableaux)


class PDFImageExtractor:
    """
    Extracteur et analyseur d'images pour les documents PDF.
    Utilise Albert Vision pour analyser les tableaux et graphiques.
    """

    # Taille minimale pour considérer une image (éviter les icônes, logos)
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    MIN_IMAGE_AREA = 10000  # pixels²

    def __init__(
        self,
        vision_provider: Optional[AlbertVision] = None,
        analyze_tables: bool = True,
        analyze_charts: bool = True,
        min_width: int = MIN_IMAGE_WIDTH,
        min_height: int = MIN_IMAGE_HEIGHT,
    ):
        """
        Initialise l'extracteur d'images PDF.

        Args:
            vision_provider: Provider de vision Albert (optionnel)
            analyze_tables: Analyser les tableaux détectés
            analyze_charts: Analyser les graphiques détectés
            min_width: Largeur minimale des images à extraire
            min_height: Hauteur minimale des images à extraire
        """
        self.vision = vision_provider
        self.analyze_tables = analyze_tables
        self.analyze_charts = analyze_charts
        self.min_width = min_width
        self.min_height = min_height

    def extract_images_from_pdf(
        self,
        pdf_bytes: bytes,
        max_images: int = 50,
    ) -> List[ExtractedImage]:
        """
        Extrait toutes les images significatives d'un PDF.

        Args:
            pdf_bytes: Contenu du fichier PDF
            max_images: Nombre maximum d'images à extraire

        Returns:
            Liste des images extraites
        """
        images = []

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    if len(images) >= max_images:
                        break

                    try:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)

                        if not base_image:
                            continue

                        width = base_image["width"]
                        height = base_image["height"]

                        # Filtrer les petites images
                        if width < self.min_width or height < self.min_height:
                            continue
                        if width * height < self.MIN_IMAGE_AREA:
                            continue

                        image_bytes = base_image["image"]
                        image_type = base_image["ext"]

                        # Récupérer la bounding box si disponible
                        bbox = (0, 0, width, height)
                        for img_rect in page.get_image_rects(xref):
                            bbox = tuple(img_rect)
                            break

                        images.append(ExtractedImage(
                            page_number=page_num + 1,
                            image_index=img_index,
                            image_bytes=image_bytes,
                            width=width,
                            height=height,
                            image_type=image_type,
                            bbox=bbox,
                        ))

                    except Exception as e:
                        logging.warning(f"Erreur extraction image page {page_num + 1}: {e}")
                        continue

            doc.close()

        except Exception as e:
            logging.error(f"Erreur ouverture PDF: {e}")

        return images

    def classify_image(self, image: ExtractedImage) -> Tuple[bool, bool]:
        """
        Classifie une image comme tableau et/ou graphique.
        Heuristique basée sur les dimensions.

        Args:
            image: Image à classifier

        Returns:
            Tuple (is_table, is_chart)
        """
        aspect_ratio = image.width / image.height if image.height > 0 else 1

        # Heuristiques simples
        # Les tableaux sont souvent plus larges que hauts
        is_likely_table = aspect_ratio > 1.2 and image.width > 300

        # Les graphiques sont souvent carrés ou légèrement plus larges
        is_likely_chart = 0.7 < aspect_ratio < 2.0 and image.width > 200

        return is_likely_table, is_likely_chart

    def analyze_image(
        self,
        image: ExtractedImage,
        force_table: bool = False,
        force_chart: bool = False,
    ) -> AnalyzedImage:
        """
        Analyse une image extraite avec Albert Vision.

        Args:
            image: Image à analyser
            force_table: Forcer l'analyse comme tableau
            force_chart: Forcer l'analyse comme graphique

        Returns:
            Image analysée avec description
        """
        if self.vision is None:
            # Sans provider de vision, retourner une description basique
            return AnalyzedImage(
                extracted_image=image,
                description=f"Image page {image.page_number} ({image.width}x{image.height})",
                is_table=False,
                is_chart=False,
                extracted_data=None,
            )

        is_table, is_chart = self.classify_image(image)

        if force_table:
            is_table = True
        if force_chart:
            is_chart = True

        description = ""
        extracted_data = None

        try:
            if is_table and self.analyze_tables:
                # Analyser comme tableau
                description = self.vision.analyze_table(
                    image.image_bytes,
                    extract_data=True
                )
                extracted_data = description  # Le markdown du tableau
                is_table = True
                is_chart = False

            elif is_chart and self.analyze_charts:
                # Analyser comme graphique
                description = self.vision.analyze_chart(image.image_bytes)
                is_chart = True
                is_table = False

            else:
                # Description générale
                description = self.vision.analyze_image(
                    image.image_bytes,
                    prompt="Décris cette image de document. Est-ce un tableau, un graphique, ou autre chose ?"
                )

        except Exception as e:
            logging.error(f"Erreur analyse image: {e}")
            description = f"[Erreur d'analyse] Image page {image.page_number}"

        return AnalyzedImage(
            extracted_image=image,
            description=description,
            is_table=is_table,
            is_chart=is_chart,
            extracted_data=extracted_data,
        )

    def extract_and_analyze_all(
        self,
        pdf_bytes: bytes,
        max_images: int = 20,
    ) -> List[AnalyzedImage]:
        """
        Extrait et analyse toutes les images d'un PDF.

        Args:
            pdf_bytes: Contenu du PDF
            max_images: Nombre maximum d'images à traiter

        Returns:
            Liste des images analysées
        """
        images = self.extract_images_from_pdf(pdf_bytes, max_images)

        analyzed = []
        for image in images:
            analyzed_image = self.analyze_image(image)
            analyzed.append(analyzed_image)

        return analyzed

    def generate_image_chunks(
        self,
        analyzed_images: List[AnalyzedImage],
        document_name: str,
    ) -> List[dict]:
        """
        Génère des chunks de texte à partir des images analysées.
        Ces chunks peuvent être ajoutés à la base vectorielle.

        Args:
            analyzed_images: Liste des images analysées
            document_name: Nom du document source

        Returns:
            Liste de chunks pour l'indexation
        """
        chunks = []

        for img in analyzed_images:
            # Construire le texte du chunk
            if img.is_table and img.extracted_data:
                text = f"[TABLEAU - Page {img.extracted_image.page_number}]\n{img.extracted_data}"
                chunk_type = "table"
            elif img.is_chart:
                text = f"[GRAPHIQUE - Page {img.extracted_image.page_number}]\n{img.description}"
                chunk_type = "chart"
            else:
                text = f"[IMAGE - Page {img.extracted_image.page_number}]\n{img.description}"
                chunk_type = "image"

            chunks.append({
                "text": text,
                "metadata": {
                    "filename": document_name,
                    "page": img.extracted_image.page_number,
                    "type": chunk_type,
                    "is_visual_content": True,
                    "width": img.extracted_image.width,
                    "height": img.extracted_image.height,
                },
            })

        return chunks


def extract_pdf_with_vision(
    pdf_bytes: bytes,
    document_name: str,
    vision_api_key: Optional[str] = None,
    max_images: int = 20,
) -> Tuple[str, List[dict]]:
    """
    Fonction utilitaire pour extraire le texte ET les images d'un PDF.

    Args:
        pdf_bytes: Contenu du PDF
        document_name: Nom du document
        vision_api_key: Clé API Albert pour la vision (optionnel)
        max_images: Nombre maximum d'images à analyser

    Returns:
        Tuple (texte_complet, liste_de_chunks_images)
    """
    # Extraire le texte standard
    text = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        logging.error(f"Erreur extraction texte PDF: {e}")

    # Extraire et analyser les images si vision disponible
    image_chunks = []
    if vision_api_key:
        try:
            vision = AlbertVision(api_key=vision_api_key)
            extractor = PDFImageExtractor(vision_provider=vision)
            analyzed_images = extractor.extract_and_analyze_all(pdf_bytes, max_images)
            image_chunks = extractor.generate_image_chunks(analyzed_images, document_name)
        except Exception as e:
            logging.warning(f"Erreur extraction images: {e}")

    return text, image_chunks
