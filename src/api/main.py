"""
API FastAPI - Point d'entrée de l'application
Architecture Hexagonale : API Layer avec Wiring/Injection
"""

import logging
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .schemas.requests import QueryRequest
from .schemas.responses import (
    QueryResponse,
    HealthResponse,
    ErrorResponse,
    SourceDTO,
    DocumentIndexResponse
)

from ..config import get_container
from ..application.use_cases.query_rag import QueryRAGUseCase, RAGError
from ..application.use_cases.search_similar import SearchSimilarUseCase, SearchError
from ..application.use_cases.index_document import IndexDocumentUseCase, IndexError
from ..application.use_cases.delete_documents import DeleteDocumentsUseCase, DeleteError
from ..infrastructure.adapters.document_parser_adapter import DocumentParserAdapter


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

        # Utiliser les providers spécifiés dans la requête
        embedding_port = container.get_embedding_port(request.embedding_provider)
        vector_store_port = container.get_vector_store()
        llm_port = container.get_llm_port(request.llm_provider)

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


@app.post(
    "/documents/upload",
    response_model=DocumentIndexResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Fichier invalide"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload et indexe un document.

    Args:
        file: Fichier à indexer (PDF, DOCX, TXT)

    Returns:
        DocumentIndexResponse: Informations sur le document indexé

    Raises:
        HTTPException: Si l'indexation échoue
    """
    logger.info(f"📤 Upload du fichier: {file.filename}")

    # Validation du nom de fichier
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom de fichier est requis"
        )

    # Validation du type de fichier
    allowed_extensions = [".pdf", ".docx", ".txt"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté. Formats acceptés: {', '.join(allowed_extensions)}"
        )

    try:
        # Lire le contenu du fichier
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le fichier est vide"
            )

        # Parser le document
        parser = DocumentParserAdapter(chunk_size=1000, chunk_overlap=200)
        document = parser.parse_document(file_bytes, file.filename)

        # Indexer le document
        container = get_container()
        embedding_port = container.get_embedding_port()
        vector_store_port = container.get_vector_store()

        use_case = IndexDocumentUseCase(
            embedding_port=embedding_port,
            vector_store_port=vector_store_port
        )

        indexed_doc = use_case.execute(document)

        logger.info(f"✅ Document {file.filename} indexé ({indexed_doc.chunks_count} chunks)")

        return DocumentIndexResponse(
            document_id=indexed_doc.id,
            filename=indexed_doc.filename,
            chunks_count=indexed_doc.chunks_count,
            message=f"Document '{file.filename}' indexé avec succès"
        )

    except ValueError as e:
        logger.error(f"❌ Erreur validation fichier: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except IndexError as e:
        logger.error(f"❌ Erreur indexation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"❌ Erreur inattendue upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite lors de l'upload"
        )


@app.delete(
    "/documents",
    responses={
        200: {"description": "Documents supprimés"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"}
    }
)
async def delete_all_documents():
    """
    Supprime tous les documents de la base.

    Returns:
        Message de confirmation avec le nombre de documents supprimés

    Raises:
        HTTPException: Si la suppression échoue
    """
    logger.info("🗑️ Suppression de tous les documents")

    try:
        container = get_container()
        vector_store_port = container.get_vector_store()

        use_case = DeleteDocumentsUseCase(vector_store_port=vector_store_port)
        count = use_case.execute_all()

        logger.info(f"✅ {count} documents supprimés")

        return {
            "message": "Tous les documents ont été supprimés",
            "deleted_count": count
        }

    except DeleteError as e:
        logger.error(f"❌ Erreur suppression: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"❌ Erreur inattendue suppression: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite lors de la suppression"
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
