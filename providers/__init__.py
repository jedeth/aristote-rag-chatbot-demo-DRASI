# Providers pour le RAG Chatbot
# Abstraction multi-provider pour embeddings, LLM, vision et reranking

from .embeddings.base import EmbeddingProvider
from .embeddings.ollama import OllamaEmbeddings
from .embeddings.albert import AlbertEmbeddings

from .llm.base import LLMProvider
from .llm.aristote import AristoteLLM
from .llm.albert import AlbertLLM

from .rerank.albert_rerank import AlbertReranker

from .vision.albert_vision import AlbertVision

__all__ = [
    # Embeddings
    "EmbeddingProvider",
    "OllamaEmbeddings",
    "AlbertEmbeddings",
    # LLM
    "LLMProvider",
    "AristoteLLM",
    "AlbertLLM",
    # Reranking
    "AlbertReranker",
    # Vision
    "AlbertVision",
]
