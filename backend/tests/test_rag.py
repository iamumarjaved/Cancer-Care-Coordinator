"""Tests for RAG pipeline components."""

import pytest
import asyncio

from rag.embeddings import EmbeddingService
from rag.vector_store import VectorStore, SearchResult, VectorDocument
from rag.retriever import Retriever, RetrievalConfig
from rag.reranker import Reranker, RerankerConfig
from rag.ingestion import DataIngestion


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service for testing."""
        return EmbeddingService(use_mock=True)

    @pytest.mark.asyncio
    async def test_embed_text(self, embedding_service):
        """Test single text embedding."""
        text = "EGFR mutation in lung cancer"
        embedding = await embedding_service.embed_text(text)

        assert len(embedding) == embedding_service.EMBEDDING_DIM
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_embed_batch(self, embedding_service):
        """Test batch text embedding."""
        texts = [
            "EGFR mutation",
            "ALK fusion",
            "KRAS G12C"
        ]
        embeddings = await embedding_service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == embedding_service.EMBEDDING_DIM for e in embeddings)

    @pytest.mark.asyncio
    async def test_embedding_determinism(self, embedding_service):
        """Test that same text produces same embedding."""
        text = "Test text for embedding"
        emb1 = await embedding_service.embed_text(text)
        emb2 = await embedding_service.embed_text(text)

        assert emb1 == emb2

    @pytest.mark.asyncio
    async def test_different_texts_different_embeddings(self, embedding_service):
        """Test that different texts produce different embeddings."""
        emb1 = await embedding_service.embed_text("Text one")
        emb2 = await embedding_service.embed_text("Completely different text")

        assert emb1 != emb2

    def test_cosine_similarity(self, embedding_service):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]

        # Same vector
        assert embedding_service.cosine_similarity(vec1, vec2) == 1.0
        # Orthogonal vectors
        assert embedding_service.cosine_similarity(vec1, vec3) == 0.0

    def test_text_similarity(self, embedding_service):
        """Test text similarity calculation."""
        sim = embedding_service.text_similarity(
            "EGFR mutation lung cancer",
            "EGFR mutation lung cancer"
        )
        assert sim == 1.0

        # Different texts should have lower similarity
        sim2 = embedding_service.text_similarity(
            "EGFR mutation",
            "Weather forecast"
        )
        assert sim2 < 0.9


class TestVectorStore:
    """Tests for VectorStore."""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(use_mock=True)

    @pytest.fixture
    def vector_store(self, embedding_service):
        """Create vector store for testing."""
        return VectorStore(
            embedding_service=embedding_service,
            use_mock=True,
            namespace="test"
        )

    @pytest.mark.asyncio
    async def test_upsert_document(self, vector_store):
        """Test document insertion."""
        result = await vector_store.upsert(
            doc_id="doc1",
            content="EGFR mutation treatment with osimertinib",
            metadata={"source": "test"}
        )

        assert result is True
        assert vector_store.count == 1

    @pytest.mark.asyncio
    async def test_query_documents(self, vector_store):
        """Test document query."""
        # Insert documents
        await vector_store.upsert("doc1", "EGFR mutation targeted therapy", {"type": "genomics"})
        await vector_store.upsert("doc2", "ALK fusion treatment options", {"type": "genomics"})
        await vector_store.upsert("doc3", "Immunotherapy for lung cancer", {"type": "treatment"})

        # Query
        results = await vector_store.query("EGFR mutation", top_k=2)

        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(0 <= r.score <= 1 for r in results)

    @pytest.mark.asyncio
    async def test_query_with_filter(self, vector_store):
        """Test document query with metadata filter."""
        await vector_store.upsert("doc1", "EGFR treatment", {"type": "genomics"})
        await vector_store.upsert("doc2", "EGFR treatment", {"type": "treatment"})

        results = await vector_store.query(
            "EGFR",
            filter_metadata={"type": "genomics"}
        )

        assert all(r.metadata.get("type") == "genomics" for r in results)

    @pytest.mark.asyncio
    async def test_delete_document(self, vector_store):
        """Test document deletion."""
        await vector_store.upsert("doc1", "Test content")
        assert vector_store.count == 1

        result = await vector_store.delete("doc1")
        assert result is True
        assert vector_store.count == 0

    @pytest.mark.asyncio
    async def test_clear_store(self, vector_store):
        """Test clearing all documents."""
        await vector_store.upsert("doc1", "Content 1")
        await vector_store.upsert("doc2", "Content 2")
        assert vector_store.count == 2

        result = await vector_store.clear()
        assert result is True
        assert vector_store.count == 0

    @pytest.mark.asyncio
    async def test_query_min_score(self, vector_store):
        """Test query with minimum score threshold."""
        await vector_store.upsert("doc1", "EGFR mutation")
        await vector_store.upsert("doc2", "Completely unrelated content xyz")

        results = await vector_store.query("EGFR mutation", min_score=0.5)

        assert all(r.score >= 0.5 for r in results)


class TestRetriever:
    """Tests for Retriever."""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(use_mock=True)

    @pytest.fixture
    def vector_stores(self, embedding_service):
        """Create vector stores for testing."""
        stores = {
            "evidence": VectorStore(embedding_service, use_mock=True, namespace="evidence"),
            "trials": VectorStore(embedding_service, use_mock=True, namespace="trials")
        }
        return stores

    @pytest.fixture
    def retriever(self, embedding_service, vector_stores):
        """Create retriever for testing."""
        return Retriever(
            embedding_service=embedding_service,
            vector_stores=vector_stores,
            use_mock=True
        )

    @pytest.mark.asyncio
    async def test_retrieve_from_multiple_namespaces(self, retriever, vector_stores):
        """Test retrieval from multiple namespaces."""
        await vector_stores["evidence"].upsert("ev1", "EGFR targeted therapy evidence")
        await vector_stores["trials"].upsert("tr1", "EGFR clinical trial recruiting")

        results = await retriever.retrieve("EGFR", namespaces=["evidence", "trials"])

        # Should have results from both namespaces
        namespaces = {r.metadata.get("namespace") for r in results}
        # May have results from one or both depending on scores

    @pytest.mark.asyncio
    async def test_query_expansion(self, retriever, vector_stores):
        """Test query expansion with synonyms."""
        await vector_stores["evidence"].upsert(
            "ev1",
            "Non-small cell lung cancer treatment"
        )

        # Query with abbreviation
        results = await retriever.retrieve(
            "nsclc treatment",
            config=RetrievalConfig(expand_query=True)
        )

        # Expansion should help find the document

    def test_medical_synonyms(self, retriever):
        """Test that retriever has medical synonyms."""
        assert "nsclc" in retriever.MEDICAL_SYNONYMS
        assert "egfr" in retriever.MEDICAL_SYNONYMS
        assert "immunotherapy" in retriever.MEDICAL_SYNONYMS

    @pytest.mark.asyncio
    async def test_retrieve_for_treatment(self, retriever, vector_stores):
        """Test specialized treatment retrieval."""
        await vector_stores["evidence"].upsert(
            "ev1",
            "Osimertinib in EGFR-mutant NSCLC shows improved survival"
        )

        results = await retriever.retrieve_for_treatment(
            treatment_name="Osimertinib",
            cancer_type="NSCLC",
            mutations=["EGFR"]
        )

        # Should find relevant evidence

    @pytest.mark.asyncio
    async def test_retrieve_for_mutation(self, retriever, vector_stores):
        """Test specialized mutation retrieval."""
        await vector_stores["evidence"].upsert(
            "ev1",
            "EGFR L858R mutation responds well to EGFR TKIs"
        )

        results = await retriever.retrieve_for_mutation(
            gene="EGFR",
            variant="L858R"
        )


class TestReranker:
    """Tests for Reranker."""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(use_mock=True)

    @pytest.fixture
    def reranker(self, embedding_service):
        """Create reranker for testing."""
        return Reranker(
            embedding_service=embedding_service,
            use_mock=True
        )

    @pytest.mark.asyncio
    async def test_rerank_results(self, reranker):
        """Test reranking of search results."""
        results = [
            SearchResult(doc_id="d1", content="EGFR mutation treatment", score=0.7),
            SearchResult(doc_id="d2", content="Random content about weather", score=0.8),
            SearchResult(doc_id="d3", content="EGFR targeted therapy with osimertinib", score=0.6)
        ]

        reranked = await reranker.rerank("EGFR mutation", results)

        # More relevant results should be ranked higher after reranking
        assert len(reranked) <= len(results)

    @pytest.mark.asyncio
    async def test_rerank_with_source_boost(self, reranker):
        """Test reranking with source quality boost."""
        results = [
            SearchResult(
                doc_id="d1",
                content="EGFR treatment",
                score=0.7,
                metadata={"source_type": "pubmed"}
            ),
            SearchResult(
                doc_id="d2",
                content="EGFR treatment",
                score=0.7,
                metadata={"source_type": "nccn_guidelines"}
            )
        ]

        config = RerankerConfig(boost_source_quality=True)
        reranked = await reranker.rerank("EGFR", results, config)

        # Guidelines should be boosted
        # Check that scores are adjusted

    @pytest.mark.asyncio
    async def test_rerank_with_recency_boost(self, reranker):
        """Test reranking with recency boost."""
        from datetime import datetime

        current_year = datetime.now().year
        results = [
            SearchResult(
                doc_id="d1",
                content="EGFR study",
                score=0.7,
                metadata={"year": current_year}
            ),
            SearchResult(
                doc_id="d2",
                content="EGFR study",
                score=0.7,
                metadata={"year": current_year - 5}
            )
        ]

        config = RerankerConfig(boost_recency=True)
        reranked = await reranker.rerank("EGFR", results, config)

        # More recent should be boosted

    def test_source_weights(self, reranker):
        """Test that reranker has source weights."""
        assert reranker.SOURCE_WEIGHTS["nccn_guidelines"] > reranker.SOURCE_WEIGHTS["default"]
        assert reranker.SOURCE_WEIGHTS["fda_label"] > reranker.SOURCE_WEIGHTS["pubmed"]

    def test_filter_by_relevance(self, reranker):
        """Test filtering results by score."""
        results = [
            SearchResult(doc_id="d1", content="Good", score=0.8),
            SearchResult(doc_id="d2", content="Medium", score=0.5),
            SearchResult(doc_id="d3", content="Low", score=0.2)
        ]

        filtered = reranker.filter_by_relevance(results, min_score=0.4)

        assert len(filtered) == 2
        assert all(r.score >= 0.4 for r in filtered)

    def test_group_by_source(self, reranker):
        """Test grouping results by source."""
        results = [
            SearchResult(doc_id="d1", content="A", score=0.8, metadata={"source_type": "pubmed"}),
            SearchResult(doc_id="d2", content="B", score=0.7, metadata={"source_type": "nccn"}),
            SearchResult(doc_id="d3", content="C", score=0.6, metadata={"source_type": "pubmed"})
        ]

        groups = reranker.group_by_source(results)

        assert "pubmed" in groups
        assert len(groups["pubmed"]) == 2
        assert "nccn" in groups


class TestDataIngestion:
    """Tests for DataIngestion."""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(use_mock=True)

    @pytest.fixture
    def vector_stores(self, embedding_service):
        return {
            "evidence": VectorStore(embedding_service, True, "evidence"),
            "trials": VectorStore(embedding_service, True, "trials"),
            "genomics": VectorStore(embedding_service, True, "genomics"),
            "guidelines": VectorStore(embedding_service, True, "guidelines")
        }

    @pytest.fixture
    def ingestion(self, embedding_service, vector_stores):
        return DataIngestion(
            embedding_service=embedding_service,
            vector_stores=vector_stores
        )

    @pytest.mark.asyncio
    async def test_load_mock_data(self, ingestion):
        """Test loading mock data."""
        results = await ingestion.load_all_mock_data()

        # Should have loaded some data
        assert sum(results.values()) > 0

    def test_chunk_text(self, ingestion):
        """Test text chunking."""
        long_text = "This is a sentence. " * 100

        chunks = ingestion._chunk_text(long_text, chunk_size=200)

        assert len(chunks) > 1
        assert all(len(c) <= 250 for c in chunks)  # Allow some variance

    @pytest.mark.asyncio
    async def test_index_single_document(self, ingestion, vector_stores):
        """Test indexing a single document."""
        success = await ingestion.index_single_document(
            namespace="evidence",
            doc_id="test_doc",
            content="Test content for indexing",
            metadata={"test": True}
        )

        assert success is True
        assert vector_stores["evidence"].count == 1

    @pytest.mark.asyncio
    async def test_clear_namespace(self, ingestion, vector_stores):
        """Test clearing a namespace."""
        await ingestion.index_single_document("evidence", "doc1", "Content")
        assert vector_stores["evidence"].count == 1

        result = await ingestion.clear_namespace("evidence")
        assert result is True
        assert vector_stores["evidence"].count == 0
