"""Vector store for document storage and retrieval using ChromaDB."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import math
import os

from .embeddings import EmbeddingService
from config import settings


class SearchResult(BaseModel):
    """Result from vector search."""
    doc_id: str
    content: str
    score: float = Field(ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorDocument(BaseModel):
    """Document stored in vector store."""
    doc_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorStore:
    """ChromaDB-backed vector store with persistent storage.

    In mock mode, stores vectors in memory and uses cosine similarity.
    In production mode, uses ChromaDB with persistent storage.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        use_mock: bool = None,
        namespace: str = "default"
    ):
        """Initialize vector store.

        Args:
            embedding_service: Service for generating embeddings
            use_mock: Whether to use in-memory mock store (defaults to config)
            namespace: Namespace for document isolation (collection name in ChromaDB)
        """
        self.embedding_service = embedding_service
        self.use_mock = use_mock if use_mock is not None else settings.USE_MOCK_VECTOR_STORE
        self.namespace = namespace
        self.logger = logging.getLogger(f"rag.vector_store.{namespace}")

        # In-memory storage for mock mode
        self._documents: Dict[str, VectorDocument] = {}
        self._collection = None
        self._client = None

        if not self.use_mock:
            self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB client with persistent storage."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # Ensure persist directory exists
            persist_dir = settings.CHROMA_PERSIST_DIR
            os.makedirs(persist_dir, exist_ok=True)

            # Initialize persistent client
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection for this namespace
            self._collection = self._client.get_or_create_collection(
                name=self.namespace,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

            self.logger.info(f"ChromaDB initialized at {persist_dir}, collection: {self.namespace}")
        except Exception as e:
            self.logger.warning(f"Could not initialize ChromaDB: {e}, falling back to mock")
            self.use_mock = True

    async def upsert(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Insert or update a document.

        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Optional metadata dictionary

        Returns:
            True if successful
        """
        metadata = metadata or {}

        # Generate embedding
        embedding = await self.embedding_service.embed_text(content)

        if self.use_mock:
            self._documents[doc_id] = VectorDocument(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            self.logger.debug(f"Upserted document: {doc_id}")
            return True

        try:
            # ChromaDB upsert - store content in metadata for retrieval
            doc_metadata = {**metadata, "content": content}
            self._collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[doc_metadata],
                documents=[content]
            )
            self.logger.debug(f"Upserted document to ChromaDB: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"ChromaDB upsert failed: {e}")
            # Fallback to mock
            self._documents[doc_id] = VectorDocument(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            return True

    async def upsert_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """Insert or update multiple documents.

        Args:
            documents: List of dicts with doc_id, content, metadata

        Returns:
            Number of documents upserted
        """
        count = 0
        for doc in documents:
            success = await self.upsert(
                doc_id=doc["doc_id"],
                content=doc["content"],
                metadata=doc.get("metadata", {})
            )
            if success:
                count += 1

        self.logger.info(f"Upserted {count} documents")
        return count

    async def query(
        self,
        query_text: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """Query for similar documents.

        Args:
            query_text: Text to search for
            top_k: Maximum number of results
            filter_metadata: Optional metadata filter
            min_score: Minimum similarity score threshold

        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query_text)

        if self.use_mock:
            return self._mock_query(query_embedding, top_k, filter_metadata, min_score)

        try:
            # ChromaDB query
            where_filter = filter_metadata if filter_metadata else None
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distances, convert to similarity score
                    # For cosine distance: similarity = 1 - distance
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = max(0, min(1, 1 - distance))  # Clamp to [0, 1]

                    if score >= min_score:
                        content = results["documents"][0][i] if results["documents"] else ""
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        # Remove content from metadata if it was stored there
                        metadata = {k: v for k, v in metadata.items() if k != "content"}

                        search_results.append(SearchResult(
                            doc_id=doc_id,
                            content=content,
                            score=score,
                            metadata=metadata
                        ))

            return search_results
        except Exception as e:
            self.logger.error(f"ChromaDB query failed: {e}")
            return self._mock_query(query_embedding, top_k, filter_metadata, min_score)

    def _mock_query(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]],
        min_score: float
    ) -> List[SearchResult]:
        """Execute mock query using cosine similarity.

        Args:
            query_embedding: Query vector
            top_k: Max results
            filter_metadata: Metadata filter
            min_score: Min similarity threshold

        Returns:
            List of search results
        """
        results = []

        for doc in self._documents.values():
            # Apply metadata filter
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            # Calculate similarity
            score = self._cosine_similarity(query_embedding, doc.embedding)

            # Normalize score to [0, 1]
            normalized_score = (score + 1) / 2

            if normalized_score >= min_score:
                results.append(SearchResult(
                    doc_id=doc.doc_id,
                    content=doc.content,
                    score=normalized_score,
                    metadata=doc.metadata
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def delete(self, doc_id: str) -> bool:
        """Delete a document.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        if self.use_mock:
            if doc_id in self._documents:
                del self._documents[doc_id]
                return True
            return False

        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            self.logger.error(f"ChromaDB delete failed: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all documents in namespace.

        Returns:
            True if successful
        """
        if self.use_mock:
            self._documents.clear()
            return True

        try:
            # ChromaDB: delete and recreate collection to clear all documents
            self._client.delete_collection(self.namespace)
            self._collection = self._client.get_or_create_collection(
                name=self.namespace,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            self.logger.error(f"ChromaDB clear failed: {e}")
            return False

    @property
    def count(self) -> int:
        """Get number of documents in store."""
        if self.use_mock:
            return len(self._documents)

        try:
            return self._collection.count()
        except Exception:
            return len(self._documents)

    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID (mock mode only).

        Args:
            doc_id: Document ID

        Returns:
            VectorDocument if found
        """
        return self._documents.get(doc_id)
