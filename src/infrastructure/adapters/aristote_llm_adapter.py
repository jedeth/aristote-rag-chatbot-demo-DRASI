"""
Adapter Aristote LLM - Implémente LLMPort
Architecture Hexagonale : Infrastructure Layer
"""

import logging
from typing import List, Dict, Optional
from openai import OpenAI

from ...domain.ports.llm_port import LLMPort, LLMError


logger = logging.getLogger(__name__)


class AristoteLLMAdapter(LLMPort):
    """Adapter pour Aristote API - implémente l'interface LLMPort."""

    DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
    API_BASE = "https://llm.ilaas.fr/v1"

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        """
        Initialise l'adapter Aristote.

        Args:
            api_key: Clé API Aristote
            model_name: Nom du modèle (défaut: Llama-3.3-70B)

        Raises:
            LLMError: Si l'initialisation échoue
        """
        if not api_key:
            raise LLMError("La clé API Aristote est requise")

        self._model_name = model_name

        try:
            self._client = OpenAI(
                api_key=api_key,
                base_url=self.API_BASE
            )
            logger.info(f"Aristote LLM Adapter initialisé (modèle: {model_name})")
        except Exception as e:
            logger.error(f"Erreur initialisation Aristote: {e}")
            raise LLMError(f"Impossible d'initialiser Aristote: {e}")

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
        if not prompt or not prompt.strip():
            raise LLMError("Le prompt ne peut pas être vide")

        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMError("Aucune réponse générée par le LLM")

            logger.info(f"Réponse générée ({len(content)} caractères)")
            return content

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération Aristote: {e}")
            raise LLMError(f"Échec génération: {e}")

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Génère une réponse avec historique de conversation.

        Args:
            messages: Liste de messages (role/content)
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens

        Returns:
            Réponse du LLM

        Raises:
            LLMError: Si la génération échoue
        """
        if not messages:
            raise LLMError("L'historique de messages est vide")

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMError("Aucune réponse générée par le LLM")

            logger.info(
                f"Réponse générée avec historique "
                f"({len(messages)} messages, {len(content)} caractères)"
            )
            return content

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Erreur génération avec historique Aristote: {e}")
            raise LLMError(f"Échec génération: {e}")

    def get_model_name(self) -> str:
        """Retourne le nom du modèle utilisé."""
        return self._model_name
