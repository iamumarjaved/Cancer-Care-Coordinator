"""RAG (Retrieval-Augmented Generation) Pipeline for Cancer Care Coordinator.

This module provides:
- EmbeddingService: Generate text embeddings
- VectorStore: Store and query document vectors
- Retriever: Retrieve relevant documents
- Reranker: Re-rank search results
- DataIngestion: Load and index documents
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStore, SearchResult
from .retriever import Retriever
from .reranker import Reranker
from .ingestion import DataIngestion

__all__ = [
    "EmbeddingService",
    "VectorStore",
    "SearchResult",
    "Retriever",
    "Reranker",
    "DataIngestion",
]
