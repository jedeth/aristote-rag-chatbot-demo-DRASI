"""
Interface abstraite pour les providers LLM.
Permet de basculer entre Aristote et Albert de manière transparente.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator, Union


class LLMProvider(ABC):
    """Interface abstraite pour les providers LLM."""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Envoie une requête de chat au LLM.

        Args:
            messages: Liste de messages [{"role": "user/assistant/system", "content": "..."}]
            temperature: Température de génération (0.0 - 1.0)
            max_tokens: Nombre maximum de tokens à générer
            stream: Si True, retourne un générateur pour le streaming

        Returns:
            Réponse du LLM (str) ou générateur si stream=True
        """
        pass

    @abstractmethod
    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Complète un prompt (mode completion simple).

        Args:
            prompt: Texte à compléter
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens

        Returns:
            Texte généré
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Retourne le nom du provider (aristote, albert, etc.)."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Indique si le provider supporte le streaming."""
        pass
