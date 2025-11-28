"""
Configuration pytest et fixtures partagées.
"""

import pytest
import os
import sys

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_env_albert_key(monkeypatch):
    """Fixture pour simuler la clé API Albert."""
    monkeypatch.setenv("ALBERT_API_KEY", "test-albert-key")


@pytest.fixture
def mock_env_aristote(monkeypatch):
    """Fixture pour simuler les variables Aristote."""
    monkeypatch.setenv("ARISTOTE_API_KEY", "test-aristote-key")
    monkeypatch.setenv("ARISTOTE_DISPATCHER_URL", "https://test.aristote.com/v1")


@pytest.fixture
def mock_env_all(mock_env_albert_key, mock_env_aristote):
    """Fixture pour simuler toutes les variables d'environnement."""
    pass


@pytest.fixture
def sample_documents():
    """Fixture avec des documents de test."""
    return [
        "Le chatbot RAG utilise des embeddings pour la recherche sémantique.",
        "Albert est l'API d'IA de l'État français développée par Etalab.",
        "Les modèles de langage peuvent être utilisés pour la génération de texte.",
    ]


@pytest.fixture
def sample_chunks():
    """Fixture avec des chunks de test."""
    return [
        {
            "id": 0,
            "text": "Premier chunk de test",
            "metadata": {"filename": "test.pdf", "chunk_id": 0}
        },
        {
            "id": 1,
            "text": "Deuxième chunk de test",
            "metadata": {"filename": "test.pdf", "chunk_id": 1}
        },
    ]


@pytest.fixture
def sample_messages():
    """Fixture avec des messages de chat de test."""
    return [
        {"role": "system", "content": "Tu es un assistant helpful."},
        {"role": "user", "content": "Bonjour, comment ça va ?"},
        {"role": "assistant", "content": "Bonjour ! Je vais bien, merci."},
        {"role": "user", "content": "Que peux-tu faire ?"},
    ]
