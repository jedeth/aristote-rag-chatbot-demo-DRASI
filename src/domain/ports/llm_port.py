"""
Port (Interface) pour les services LLM
Architecture Hexagonale : Domain Layer
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMPort(ABC):
    """Interface abstraite pour les providers LLM."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Génère une réponse textuelle.

        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système (optionnel)
            temperature: Température de génération (0-1)
            max_tokens: Nombre maximum de tokens

        Returns:
            Texte généré par le LLM

        Raises:
            LLMError: Si la génération échoue
        """
        pass

    @abstractmethod
    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Génère une réponse avec historique de conversation.

        Args:
            messages: Liste de messages (role: "user"/"assistant"/"system", content: str)
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens

        Returns:
            Réponse du LLM

        Raises:
            LLMError: Si la génération échoue
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        pass


class LLMError(Exception):
    """Exception levée lors d'une erreur LLM."""
    pass
