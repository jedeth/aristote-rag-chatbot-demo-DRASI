"""
Entités du domaine - Document
Architecture Hexagonale : Couche Domain (pas de dépendances externes)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4


@dataclass
class Chunk:
    """Représente un fragment de document avec son embedding."""

    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    embedding: Optional[List[float]] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validation après initialisation."""
        if not self.text:
            raise ValueError("Le texte du chunk ne peut pas être vide")

        if len(self.text) > 10000:
            raise ValueError("Le chunk est trop long (max 10000 caractères)")


@dataclass
class Document:
    """Représente un document uploadé avec ses chunks."""

    id: str = field(default_factory=lambda: str(uuid4()))
    filename: str = ""
    content: str = ""
    chunks: List[Chunk] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    indexed_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validation après initialisation."""
        if not self.filename:
            raise ValueError("Le nom du fichier ne peut pas être vide")

        if not self.filename.lower().endswith(('.pdf', '.docx')):
            raise ValueError("Format de fichier non supporté (PDF ou DOCX uniquement)")

    @property
    def chunks_count(self) -> int:
        """Retourne le nombre de chunks."""
        return len(self.chunks)

    @property
    def total_length(self) -> int:
        """Retourne la taille totale du contenu."""
        return len(self.content)

    def add_chunk(self, chunk: Chunk) -> None:
        """Ajoute un chunk au document."""
        if not isinstance(chunk, Chunk):
            raise TypeError("Le chunk doit être de type Chunk")
        self.chunks.append(chunk)


@dataclass
class ImageChunk:
    """Représente un chunk d'image analysée."""

    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    image_data: Optional[bytes] = None
    embedding: Optional[List[float]] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validation après initialisation."""
        if not self.description:
            raise ValueError("La description de l'image ne peut pas être vide")
