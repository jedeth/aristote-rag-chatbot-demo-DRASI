"""
Entités du domaine - Query
Architecture Hexagonale : Couche Domain
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4


@dataclass
class Query:
    """Représente une requête utilisateur."""

    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validation après initialisation."""
        if not self.text or not self.text.strip():
            raise ValueError("La requête ne peut pas être vide")

        if len(self.text) > 20000:
            raise ValueError("La requête est trop longue (max 20000 caractères)")


@dataclass
class SearchResult:
    """Représente un résultat de recherche."""

    chunk_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validation après initialisation."""
        if not 0 <= self.score <= 1:
            raise ValueError("Le score doit être entre 0 et 1")


@dataclass
class RAGResponse:
    """Représente une réponse RAG complète."""

    query: Query
    response_text: str
    id: str = field(default_factory=lambda: str(uuid4()))
    sources: List[SearchResult] = field(default_factory=list)
    context_used: str = ""
    model_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def sources_count(self) -> int:
        """Retourne le nombre de sources utilisées."""
        return len(self.sources)
