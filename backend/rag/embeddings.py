"""Embedding service for generating text vectors."""

import hashlib
import math
from typing import List, Optional
import logging

from config import settings


class EmbeddingService:
    """Service for generating text embeddings.

    In mock mode, generates deterministic hash-based vectors.
    In production mode, uses OpenAI embedding API.
    """

    # Standard embedding dimensions
    EMBEDDING_DIM = 1536  # OpenAI ada-002/text-embedding-3-small dimension

    def __init__(self, use_mock: bool = None):
        """Initialize embedding service.

        Args:
            use_mock: Whether to use mock embeddings (defaults to config setting)
        """
        self.use_mock = use_mock if use_mock is not None else settings.USE_MOCK_VECTOR_STORE
        self.logger = logging.getLogger("rag.embeddings")
        self._client = None
        self._model = settings.EMBEDDING_MODEL

        if not self.use_mock:
            self._init_client()

    def _init_client(self):
        """Initialize the embedding client (OpenAI)."""
        try:
            import openai
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.logger.info(f"OpenAI embedding client initialized with model: {self._model}")
        except Exception as e:
            self.logger.warning(f"Could not initialize OpenAI client: {e}")
            self.use_mock = True

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if self.use_mock:
            return self._mock_embedding(text)

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Embedding failed, using mock: {e}")
            return self._mock_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.use_mock:
            return [self._mock_embedding(t) for t in texts]

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=texts
            )
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [d.embedding for d in sorted_data]
        except Exception as e:
            self.logger.error(f"Batch embedding failed, using mock: {e}")
            return [self._mock_embedding(t) for t in texts]

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding from text hash.

        Uses MD5 hash to generate a deterministic but distributed
        vector representation. Same text always produces same vector.

        Args:
            text: Text to embed

        Returns:
            Deterministic embedding vector
        """
        # Normalize text
        text = text.lower().strip()

        # Generate hash
        hash_bytes = hashlib.md5(text.encode()).digest()

        # Extend hash to full embedding dimension
        vector = []
        seed_value = int.from_bytes(hash_bytes, byteorder='big')

        for i in range(self.EMBEDDING_DIM):
            # Use hash-based pseudo-random generation
            seed_value = (seed_value * 1103515245 + 12345) % (2 ** 31)
            # Normalize to [-1, 1]
            value = (seed_value / (2 ** 30)) - 1.0
            vector.append(value)

        # Normalize vector to unit length
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score [-1, 1]
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def text_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts using mock embeddings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score [0, 1]
        """
        vec1 = self._mock_embedding(text1)
        vec2 = self._mock_embedding(text2)
        # Convert from [-1, 1] to [0, 1]
        return (self.cosine_similarity(vec1, vec2) + 1) / 2
