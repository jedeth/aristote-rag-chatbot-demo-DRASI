"""
Module de vision utilisant l'API Albert d'Etalab.
Permet d'analyser les images (tableaux, graphiques) dans les documents.
"""

import os
import base64
from pathlib import Path
from typing import Optional, Union
from openai import OpenAI


class AlbertVision:
    """
    Provider de vision utilisant l'API Albert d'Etalab.
    Utilise le modèle openweight-medium (multimodal, Mistral-Small-3.2-24B) pour analyser les images.
    """

    DEFAULT_MODEL = "openweight-medium"  # Anciennement albert-large (multimodal)

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialise le provider de vision Albert.

        Args:
            api_key: Clé API Albert (ou variable d'env ALBERT_API_KEY)
            base_url: URL de l'API Albert
            model: Nom du modèle (doit supporter la vision)
        """
        self._api_key = api_key or os.getenv("ALBERT_API_KEY")
        if not self._api_key:
            raise ValueError(
                "ALBERT_API_KEY est requis. "
                "Définissez-le dans .env ou passez-le en paramètre."
            )

        self._base_url = base_url
        self._model = model
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def analyze_image(
        self,
        image: Union[str, Path, bytes],
        prompt: str = "Décris cette image en détail.",
        max_tokens: int = 1024,
    ) -> str:
        """
        Analyse une image avec le modèle de vision.

        Args:
            image: Chemin vers l'image, URL, ou bytes de l'image
            prompt: Question ou instruction pour l'analyse
            max_tokens: Nombre maximum de tokens dans la réponse

        Returns:
            Description textuelle de l'image
        """
        image_content = self._prepare_image(image)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        image_content,
                    ],
                }
            ],
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def analyze_table(
        self,
        image: Union[str, Path, bytes],
        extract_data: bool = True,
    ) -> str:
        """
        Analyse un tableau dans une image.

        Args:
            image: Image contenant le tableau
            extract_data: Si True, extrait les données structurées

        Returns:
            Description du tableau ou données extraites en markdown
        """
        if extract_data:
            prompt = """Analyse ce tableau et extrais son contenu.
Retourne les données sous forme de tableau markdown.
Si possible, identifie les en-têtes et les colonnes.
Sois précis sur les valeurs numériques."""
        else:
            prompt = """Décris ce tableau :
- Quel est son sujet ?
- Combien de lignes et colonnes ?
- Quelles sont les principales informations ?"""

        return self.analyze_image(image, prompt, max_tokens=2048)

    def analyze_chart(
        self,
        image: Union[str, Path, bytes],
    ) -> str:
        """
        Analyse un graphique dans une image.

        Args:
            image: Image contenant le graphique

        Returns:
            Description et interprétation du graphique
        """
        prompt = """Analyse ce graphique en détail :
1. Type de graphique (barres, lignes, camembert, etc.)
2. Données représentées (axes, légendes)
3. Tendances principales
4. Valeurs remarquables (min, max, moyennes si visibles)
5. Conclusions ou insights"""

        return self.analyze_image(image, prompt, max_tokens=1536)

    def extract_text_from_image(
        self,
        image: Union[str, Path, bytes],
    ) -> str:
        """
        Extrait le texte visible dans une image (OCR).

        Args:
            image: Image contenant du texte

        Returns:
            Texte extrait de l'image
        """
        prompt = """Extrais tout le texte visible dans cette image.
Conserve la mise en forme autant que possible (titres, paragraphes, listes).
Ne décris pas l'image, retourne uniquement le texte."""

        return self.analyze_image(image, prompt, max_tokens=2048)

    def _prepare_image(self, image: Union[str, Path, bytes]) -> dict:
        """
        Prépare l'image pour l'API (URL ou base64).

        Args:
            image: Chemin, URL ou bytes de l'image

        Returns:
            Dictionnaire formaté pour l'API OpenAI
        """
        if isinstance(image, bytes):
            # Image en bytes -> base64
            b64_image = base64.b64encode(image).decode("utf-8")
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_image}",
                },
            }

        image_str = str(image)

        if image_str.startswith(("http://", "https://")):
            # URL directe
            return {
                "type": "image_url",
                "image_url": {"url": image_str},
            }

        # Chemin local -> base64
        path = Path(image_str)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée: {path}")

        # Détecter le type MIME
        suffix = path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")

        with open(path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{b64_image}",
            },
        }

    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model
