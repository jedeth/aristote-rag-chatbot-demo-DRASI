"""
API FastAPI - Point d'entrée de l'application
Architecture Hexagonale : API Layer avec Wiring/Injection
"""

import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .schemas.requests import QueryRequest
from .schemas.responses import (
    QueryResponse,
    HealthResponse,
    ErrorResponse,
    SourceDTO
)

from ..config import get_container
from ..application.use_cases.query_rag import QueryRAGUseCase, RAGError
from ..application.use_cases.search_similar import SearchSimilarUseCase, SearchError


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Initialisation de l'application FastAPI
app = FastAPI(
    title="Aristote RAG API",
    description="API RAG avec Architecture Hexagonale",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS (si le frontend est sur un autre domaine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    logger.info("🚀 Démarrage de l'API Aristote RAG (Architecture Hexagonale)")
    container = get_container()
    logger.info(f"✅ Configuration chargée (ChromaDB: {container.config.CHROMA_DB_PATH})")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application."""
    logger.info("🛑 Arrêt de l'API Aristote RAG")


@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint racine - redirection vers /health."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "hexagonal"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check de l'API.

    Returns:
        HealthResponse: Statut de l'API
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "hexagonal"
    }


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Requête invalide"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)
async def query_rag(request: QueryRequest):
    """
    Endpoint pour une requête RAG.

    Args:
        request: Requête utilisateur avec paramètres

    Returns:
        QueryResponse: Réponse avec sources

    Raises:
        HTTPException: Si le traitement échoue
    """
    logger.info(f"📥 Requête RAG reçue : '{request.query[:50]}...'")

    try:
        # WIRING : Récupération des ports depuis le conteneur
        container = get_container()
        embedding_port = container.get_embedding_port()
        vector_store_port = container.get_vector_store()
        llm_port = container.get_llm_port()

        # WIRING : Injection dans le use case
        use_case = QueryRAGUseCase(
            embedding_port=embedding_port,
            vector_store_port=vector_store_port,
            llm_port=llm_port
        )

        # Filtres optionnels
        filter_metadata = None
        if request.filter_document:
            filter_metadata = {"filename": request.filter_document}

        # Exécution du use case
        rag_response = use_case.execute(
            query_text=request.query,
            n_results=request.n_results,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            filter_metadata=filter_metadata
        )

        # Conversion en DTO API (séparation domaine/API)
        sources_dto = [
            SourceDTO(
                chunk_id=source.chunk_id,
                text=source.text,
                score=source.score,
                filename=source.metadata.get("filename", "unknown"),
                document_id=source.metadata.get("document_id")
            )
            for source in rag_response.sources
        ]

        return QueryResponse(
            query_id=rag_response.id,
            query_text=rag_response.query.text,
            response_text=rag_response.response_text,
            sources=sources_dto,
            model_name=rag_response.model_name,
            created_at=rag_response.created_at
        )

    except RAGError as e:
        logger.error(f"❌ Erreur RAG: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    except ValueError as e:
        logger.error(f"❌ Erreur validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite"
        )


@app.get("/documents")
async def list_documents():
    """
    Liste les documents indexés.

    Returns:
        Liste des documents
    """
    logger.info("📋 Récupération de la liste des documents")

    try:
        container = get_container()
        vector_store = container.get_vector_store()

        documents = vector_store.get_indexed_documents()
        total_chunks = vector_store.count_chunks()

        return {
            "documents": documents,
            "total_documents": len(documents),
            "total_chunks": total_chunks
        }

    except Exception as e:
        logger.error(f"❌ Erreur liste documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
