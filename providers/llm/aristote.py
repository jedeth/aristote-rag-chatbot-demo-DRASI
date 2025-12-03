"""
Provider LLM utilisant l'API Aristote (Dispatcher DRASI).
Wrapper autour de l'API OpenAI-compatible d'Aristote.
"""

import os
from typing import List, Dict, Optional, Generator, Union
from openai import OpenAI
from .base import LLMProvider


class AristoteLLM(LLMProvider):
    """Provider LLM utilisant l'API Aristote Dispatcher."""

    DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialise le provider Aristote.

        Args:
            api_key: Clé API Aristote (ou variable d'env ARISTOTE_API_KEY)
            base_url: URL de l'API (ou variable d'env ARISTOTE_DISPATCHER_URL)
            model: Nom du modèle LLM
        """
        self._api_key = api_key or os.getenv("ARISTOTE_API_KEY")
        self._base_url = base_url or os.getenv("ARISTOTE_DISPATCHER_URL")

        if not self._api_key:
            raise ValueError(
                "ARISTOTE_API_KEY est requis. "
                "Définissez-le dans .env ou passez-le en paramètre."
            )

        if not self._base_url:
            raise ValueError(
                "ARISTOTE_DISPATCHER_URL est requis. "
                "Définissez-le dans .env ou passez-le en paramètre."
            )

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
    ) -> Union[str, Generator[str, None, None]]:
        """
        Envoie une requête de chat au LLM Aristote.

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
        return "aristote"

    @property
    def supports_streaming(self) -> bool:
        """Aristote supporte le streaming."""
        return True
