"""
Provider LLM utilisant l'API Albert d'Etalab.
Supporte les modèles: albert-small, albert-large, albert-code
"""

import os
from typing import List, Dict, Optional, Generator
from openai import OpenAI
from .base import LLMProvider


class AlbertLLM(LLMProvider):
    """Provider LLM utilisant l'API Albert d'Etalab."""

    # Modèles disponibles sur Albert
    AVAILABLE_MODELS = {
        "albert-small": "albert-small",      # Modèle léger pour tâches simples
        "albert-large": "albert-large",      # Modèle principal (multimodal)
        "albert-code": "albert-code",        # Spécialisé pour le code
    }

    DEFAULT_MODEL = "albert-large"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://albert.api.etalab.gouv.fr/v1",
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialise le provider Albert.

        Args:
            api_key: Clé API Albert (ou variable d'env ALBERT_API_KEY)
            base_url: URL de l'API Albert
            model: Nom du modèle LLM (albert-small, albert-large, albert-code)
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

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """
        Envoie une requête de chat au LLM Albert.

        Args:
            messages: Liste de messages
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens
            stream: Si True, retourne un générateur

        Returns:
            Réponse du LLM ou générateur si stream=True
        """
        kwargs = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if stream:
            return self._stream_response(**kwargs)
        else:
            response = self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

    def _stream_response(self, **kwargs) -> Generator[str, None, None]:
        """Génère les tokens en streaming."""
        stream = self._client.chat.completions.create(**kwargs)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Complète un prompt en mode chat.

        Args:
            prompt: Texte à compléter
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens

        Returns:
            Texte généré
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature, max_tokens, stream=False)

    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model

    @property
    def provider_name(self) -> str:
        """Retourne le nom du provider."""
        return "albert"

    @property
    def supports_streaming(self) -> bool:
        """Albert supporte le streaming."""
        return True

    @classmethod
    def list_models(cls) -> List[str]:
        """Liste les modèles disponibles."""
        return list(cls.AVAILABLE_MODELS.keys())
