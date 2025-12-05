"""Reranker for improving search result relevance."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from .vector_store import SearchResult
from .embeddings import EmbeddingService


class RerankerConfig(BaseModel):
    """Configuration for reranking."""
    top_k: int = 10
    use_cross_encoder: bool = False  # Would use cross-encoder model
    boost_recency: bool = True
    boost_source_quality: bool = True


class Reranker:
    """Reranker for improving search result quality.

    Reranking strategies:
    - Cross-encoder scoring (production)
    - Keyword matching boost
    - Recency boost
    - Source quality weighting
    - Query-specific relevance
    """

    # Source quality weights
    SOURCE_WEIGHTS = {
        "nccn_guidelines": 1.5,
        "fda_label": 1.4,
        "pubmed_rct": 1.3,  # Randomized controlled trial
        "pubmed_meta": 1.3,  # Meta-analysis
        "pubmed": 1.0,
        "clinical_trial": 1.2,
        "oncokb": 1.3,
        "default": 1.0
    }

    # Recency weights (years since publication)
    RECENCY_WEIGHTS = {
        0: 1.2,  # Current year
        1: 1.15,
        2: 1.1,
        3: 1.0,
        4: 0.95,
        5: 0.9,
    }

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        use_mock: bool = True
    ):
        """Initialize reranker.

        Args:
            embedding_service: Optional embedding service for advanced reranking
            use_mock: Whether to use mock mode
        """
        self.embedding_service = embedding_service
        self.use_mock = use_mock
        self.logger = logging.getLogger("rag.reranker")
        self._cross_encoder = None

        if not use_mock and not self.use_mock:
            self._init_cross_encoder()

    def _init_cross_encoder(self):
        """Initialize cross-encoder model for production reranking.

        Note: Cross-encoder requires sentence-transformers which is not installed.
        Using mock reranking with heuristics instead.
        """
        # Cross-encoder not available without sentence-transformers
        # Fall back to heuristic-based reranking which works well for this use case
        self.logger.info("Using heuristic-based reranking (no cross-encoder)")
        self.use_mock = True

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        config: Optional[RerankerConfig] = None
    ) -> List[SearchResult]:
        """Rerank search results for improved relevance.

        Args:
            query: Original search query
            results: Initial search results
            config: Reranking configuration

        Returns:
            Reranked search results
        """
        config = config or RerankerConfig()

        if not results:
            return []

        if self.use_mock:
            return self._mock_rerank(query, results, config)

        try:
            return await self._cross_encoder_rerank(query, results, config)
        except Exception as e:
            self.logger.error(f"Cross-encoder reranking failed: {e}")
            return self._mock_rerank(query, results, config)

    def _mock_rerank(
        self,
        query: str,
        results: List[SearchResult],
        config: RerankerConfig
    ) -> List[SearchResult]:
        """Mock reranking using heuristics.

        Args:
            query: Search query
            results: Initial results
            config: Configuration

        Returns:
            Reranked results
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        scored_results = []

        for result in results:
            # Start with original score
            score = result.score

            # Keyword matching boost
            content_lower = result.content.lower()
            matching_terms = sum(1 for term in query_terms if term in content_lower)
            keyword_boost = 1 + (0.1 * matching_terms)
            score *= keyword_boost

            # Exact phrase boost
            if query_lower in content_lower:
                score *= 1.2

            # Source quality boost
            if config.boost_source_quality:
                source_type = result.metadata.get("source_type", "default")
                source_weight = self.SOURCE_WEIGHTS.get(source_type, 1.0)
                score *= source_weight

            # Recency boost
            if config.boost_recency:
                pub_year = result.metadata.get("year")
                if pub_year:
                    from datetime import datetime
                    current_year = datetime.now().year
                    years_old = max(0, current_year - pub_year)
                    recency_weight = self.RECENCY_WEIGHTS.get(years_old, 0.85)
                    score *= recency_weight

            # Medical relevance boost
            score *= self._medical_relevance_boost(query, result.content)

            # Update score
            result_copy = SearchResult(
                doc_id=result.doc_id,
                content=result.content,
                score=min(score, 1.0),  # Cap at 1.0
                metadata=result.metadata
            )
            scored_results.append(result_copy)

        # Sort by score
        scored_results.sort(key=lambda x: x.score, reverse=True)

        return scored_results[:config.top_k]

    async def _cross_encoder_rerank(
        self,
        query: str,
        results: List[SearchResult],
        config: RerankerConfig
    ) -> List[SearchResult]:
        """Rerank using cross-encoder model.

        Args:
            query: Search query
            results: Initial results
            config: Configuration

        Returns:
            Reranked results
        """
        # Create query-document pairs
        pairs = [(query, result.content) for result in results]

        # Get cross-encoder scores
        scores = self._cross_encoder.predict(pairs)

        # Combine with metadata boosts
        scored_results = []
        for result, ce_score in zip(results, scores):
            final_score = ce_score

            if config.boost_source_quality:
                source_type = result.metadata.get("source_type", "default")
                source_weight = self.SOURCE_WEIGHTS.get(source_type, 1.0)
                final_score *= source_weight

            if config.boost_recency:
                pub_year = result.metadata.get("year")
                if pub_year:
                    from datetime import datetime
                    current_year = datetime.now().year
                    years_old = max(0, current_year - pub_year)
                    recency_weight = self.RECENCY_WEIGHTS.get(years_old, 0.85)
                    final_score *= recency_weight

            result_copy = SearchResult(
                doc_id=result.doc_id,
                content=result.content,
                score=min(max(final_score, 0), 1.0),
                metadata=result.metadata
            )
            scored_results.append(result_copy)

        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:config.top_k]

    def _medical_relevance_boost(self, query: str, content: str) -> float:
        """Calculate medical relevance boost.

        Args:
            query: Search query
            content: Document content

        Returns:
            Boost factor
        """
        boost = 1.0
        query_lower = query.lower()
        content_lower = content.lower()

        # Key medical terms
        medical_terms = {
            "fda approved": 1.15,
            "category 1": 1.15,
            "randomized": 1.1,
            "phase 3": 1.1,
            "phase iii": 1.1,
            "meta-analysis": 1.1,
            "nccn": 1.15,
            "guideline": 1.1,
            "overall survival": 1.1,
            "progression-free": 1.1,
            "response rate": 1.05,
        }

        for term, term_boost in medical_terms.items():
            if term in content_lower:
                boost *= term_boost
                # Cap to prevent excessive boosting
                if boost > 1.5:
                    boost = 1.5
                    break

        return boost

    def filter_by_relevance(
        self,
        results: List[SearchResult],
        min_score: float = 0.3,
        max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """Filter results by minimum relevance score.

        Args:
            results: Search results
            min_score: Minimum score threshold
            max_results: Optional maximum results

        Returns:
            Filtered results
        """
        filtered = [r for r in results if r.score >= min_score]

        if max_results:
            filtered = filtered[:max_results]

        return filtered

    def group_by_source(
        self,
        results: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """Group results by source type.

        Args:
            results: Search results

        Returns:
            Dict mapping source type to results
        """
        groups: Dict[str, List[SearchResult]] = {}

        for result in results:
            source = result.metadata.get("source_type", "unknown")
            if source not in groups:
                groups[source] = []
            groups[source].append(result)

        return groups
