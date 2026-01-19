"""
Schémas Pydantic pour les REQUÊTES API
⚠️ SÉPARÉS des entités du domaine (pas de pollution)
Ces schémas servent uniquement pour la validation HTTP
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    """Schéma pour une requête RAG."""

    query: str = Field(..., min_length=1, max_length=20000, description="Question de l'utilisateur")
    n_results: int = Field(5, ge=1, le=20, description="Nombre de résultats à retourner")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Température LLM")
    max_tokens: int = Field(1000, ge=100, le=4000, description="Nombre max de tokens")
    filter_document: Optional[str] = Field(None, description="Filtrer par nom de fichier")
    llm_provider: Optional[str] = Field("aristote", description="Provider LLM (aristote/albert)")
    embedding_provider: Optional[str] = Field("ollama", description="Provider embeddings (ollama/albert)")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Quelle est la procédure de sécurité ?",
                "n_results": 5,
                "temperature": 0.7,
                "max_tokens": 1000,
                "llm_provider": "aristote",
                "embedding_provider": "ollama"
            }
        }


class DocumentUploadMetadata(BaseModel):
    """Métadonnées lors de l'upload d'un document."""

    chunk_size: int = Field(1000, ge=100, le=5000, description="Taille des chunks")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="Chevauchement entre chunks")
    analyze_images: bool = Field(False, description="Analyser les images (vision)")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "analyze_images": False
            }
        }
