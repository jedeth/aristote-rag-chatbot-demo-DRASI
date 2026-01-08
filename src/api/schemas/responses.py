"""
Schémas Pydantic pour les RÉPONSES API
⚠️ SÉPARÉS des entités du domaine (DTOs pour l'API)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SourceDTO(BaseModel):
    """DTO pour une source (chunk retrouvé)."""

    chunk_id: str
    text: str
    score: float = Field(..., ge=0.0, le=1.0)
    filename: str
    document_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Réponse à une requête RAG."""

    query_id: str
    query_text: str
    response_text: str
    sources: List[SourceDTO]
    model_name: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "abc123",
                "query_text": "Quelle est la procédure ?",
                "response_text": "La procédure consiste à...",
                "sources": [
                    {
                        "chunk_id": "chunk_1",
                        "text": "Extrait pertinent...",
                        "score": 0.95,
                        "filename": "procedure.pdf"
                    }
                ],
                "model_name": "meta-llama/Llama-3.3-70B-Instruct",
                "created_at": "2026-01-08T16:00:00"
            }
        }


class DocumentDTO(BaseModel):
    """DTO pour un document indexé."""

    document_id: str
    filename: str
    chunks_count: int
    indexed_at: datetime


class DocumentIndexResponse(BaseModel):
    """Réponse après indexation d'un document."""

    document_id: str
    filename: str
    chunks_count: int
    message: str = "Document indexé avec succès"


class DocumentListResponse(BaseModel):
    """Liste des documents indexés."""

    documents: List[DocumentDTO]
    total_count: int


class HealthResponse(BaseModel):
    """Health check."""

    status: str = "healthy"
    version: str = "2.0.0"
    architecture: str = "hexagonal"


class ErrorResponse(BaseModel):
    """Réponse d'erreur."""

    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Document not found",
                "detail": "Le document abc123 n'existe pas",
                "error_code": "DOC_NOT_FOUND"
            }
        }
