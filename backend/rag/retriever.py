"""Retriever for document retrieval with query expansion."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from .embeddings import EmbeddingService
from .vector_store import VectorStore, SearchResult


class RetrievalConfig(BaseModel):
    """Configuration for retrieval."""
    top_k: int = 10
    expand_query: bool = True
    min_score: float = 0.3
    diversity_factor: float = 0.1
    use_mmr: bool = False  # Maximal Marginal Relevance


class Retriever:
    """Document retriever with query expansion and multiple strategies.

    Supports:
    - Query expansion with medical synonyms
    - Hybrid search (keyword + semantic)
    - Maximal Marginal Relevance for diversity
    - Metadata filtering
    """

    # Medical term synonyms for query expansion
    MEDICAL_SYNONYMS = {
        "nsclc": ["non-small cell lung cancer", "lung adenocarcinoma", "lung squamous cell"],
        "egfr": ["epidermal growth factor receptor", "egfr mutation", "erbb1"],
        "alk": ["alk fusion", "alk rearrangement", "anaplastic lymphoma kinase"],
        "immunotherapy": ["checkpoint inhibitor", "pd-1 inhibitor", "pd-l1 inhibitor", "io therapy"],
        "chemotherapy": ["cytotoxic therapy", "chemo", "platinum-based therapy"],
        "targeted therapy": ["molecular therapy", "precision therapy", "tyrosine kinase inhibitor"],
        "mutation": ["variant", "alteration", "genetic change"],
        "side effect": ["adverse event", "toxicity", "adverse reaction"],
        "survival": ["os", "overall survival", "progression free survival", "pfs"],
        "tumor": ["neoplasm", "cancer", "malignancy", "lesion"],
        "metastasis": ["metastatic", "mets", "spread", "secondary tumor"],
        "biopsy": ["tissue sample", "specimen", "pathology"],
        "stage": ["staging", "tnm", "extent of disease"],
    }

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_stores: Dict[str, VectorStore],
        use_mock: bool = True
    ):
        """Initialize retriever.

        Args:
            embedding_service: Service for embeddings
            vector_stores: Dict of namespace -> VectorStore
            use_mock: Whether to use mock mode
        """
        self.embedding_service = embedding_service
        self.vector_stores = vector_stores
        self.use_mock = use_mock
        self.logger = logging.getLogger("rag.retriever")

    async def retrieve(
        self,
        query: str,
        namespaces: Optional[List[str]] = None,
        config: Optional[RetrievalConfig] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: Search query
            namespaces: List of namespaces to search (None = all)
            config: Retrieval configuration
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult objects
        """
        config = config or RetrievalConfig()
        namespaces = namespaces or list(self.vector_stores.keys())

        # Expand query if enabled
        queries = [query]
        if config.expand_query:
            queries.extend(self._expand_query(query))

        # Search each namespace
        all_results: List[SearchResult] = []

        for namespace in namespaces:
            if namespace not in self.vector_stores:
                continue

            store = self.vector_stores[namespace]

            for q in queries:
                results = await store.query(
                    query_text=q,
                    top_k=config.top_k,
                    filter_metadata=filter_metadata,
                    min_score=config.min_score
                )

                # Add namespace to metadata
                for result in results:
                    result.metadata["namespace"] = namespace

                all_results.extend(results)

        # Deduplicate by doc_id, keeping highest score
        unique_results = self._deduplicate_results(all_results)

        # Apply MMR if enabled
        if config.use_mmr:
            unique_results = await self._apply_mmr(
                query, unique_results, config.top_k, config.diversity_factor
            )

        # Sort by score and return top_k
        unique_results.sort(key=lambda x: x.score, reverse=True)
        return unique_results[:config.top_k]

    def _expand_query(self, query: str) -> List[str]:
        """Expand query with medical synonyms.

        Args:
            query: Original query

        Returns:
            List of expanded queries
        """
        expanded = []
        query_lower = query.lower()

        for term, synonyms in self.MEDICAL_SYNONYMS.items():
            if term in query_lower:
                # Replace term with each synonym
                for synonym in synonyms[:2]:  # Limit expansions
                    expanded_query = query_lower.replace(term, synonym)
                    if expanded_query != query_lower:
                        expanded.append(expanded_query)

        return expanded[:3]  # Limit to 3 expanded queries

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Deduplicate results by doc_id, keeping highest score.

        Args:
            results: List of search results

        Returns:
            Deduplicated list
        """
        seen = {}
        for result in results:
            if result.doc_id not in seen or result.score > seen[result.doc_id].score:
                seen[result.doc_id] = result

        return list(seen.values())

    async def _apply_mmr(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int,
        diversity_factor: float
    ) -> List[SearchResult]:
        """Apply Maximal Marginal Relevance for diversity.

        Balances relevance to query with diversity of results.

        Args:
            query: Original query
            results: Candidate results
            top_k: Number of results to select
            diversity_factor: Weight for diversity (0-1)

        Returns:
            Reranked diverse results
        """
        if len(results) <= top_k:
            return results

        # Get query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        selected = []
        candidates = results.copy()

        while len(selected) < top_k and candidates:
            best_score = -1
            best_idx = 0

            for i, candidate in enumerate(candidates):
                # Relevance score (already computed)
                relevance = candidate.score

                # Diversity score (max similarity to already selected)
                diversity = 0
                if selected:
                    # Get candidate embedding
                    cand_embedding = await self.embedding_service.embed_text(candidate.content)

                    for sel in selected:
                        sel_embedding = await self.embedding_service.embed_text(sel.content)
                        sim = EmbeddingService.cosine_similarity(cand_embedding, sel_embedding)
                        diversity = max(diversity, (sim + 1) / 2)

                # MMR score
                mmr_score = (1 - diversity_factor) * relevance - diversity_factor * diversity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            selected.append(candidates.pop(best_idx))

        return selected

    async def retrieve_for_treatment(
        self,
        treatment_name: str,
        cancer_type: str,
        mutations: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Retrieve evidence for a specific treatment.

        Args:
            treatment_name: Name of treatment/drug
            cancer_type: Type of cancer
            mutations: Optional list of mutations

        Returns:
            Relevant search results
        """
        # Build comprehensive query
        query_parts = [treatment_name, cancer_type]
        if mutations:
            query_parts.extend(mutations[:2])

        query = " ".join(query_parts)

        # Search evidence and trials namespaces
        return await self.retrieve(
            query=query,
            namespaces=["evidence", "trials"],
            config=RetrievalConfig(
                top_k=20,
                expand_query=True,
                min_score=0.25
            )
        )

    async def retrieve_for_mutation(
        self,
        gene: str,
        variant: str
    ) -> List[SearchResult]:
        """Retrieve information about a specific mutation.

        Args:
            gene: Gene name (e.g., EGFR)
            variant: Variant name (e.g., L858R)

        Returns:
            Relevant search results
        """
        query = f"{gene} {variant} mutation targeted therapy"

        return await self.retrieve(
            query=query,
            namespaces=["genomics", "evidence"],
            config=RetrievalConfig(
                top_k=15,
                expand_query=True,
                min_score=0.3
            )
        )

    async def retrieve_for_trial_matching(
        self,
        cancer_type: str,
        stage: str,
        mutations: List[str],
        biomarkers: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Retrieve clinical trials for patient matching.

        Args:
            cancer_type: Type of cancer
            stage: Cancer stage
            mutations: List of mutations
            biomarkers: Optional biomarker values

        Returns:
            Matching trial results
        """
        query_parts = [cancer_type, stage] + mutations[:3]
        if biomarkers:
            if biomarkers.get("pdl1_high"):
                query_parts.append("PD-L1 high")
            if biomarkers.get("tmb_high"):
                query_parts.append("TMB high")

        query = " ".join(query_parts) + " clinical trial recruiting"

        return await self.retrieve(
            query=query,
            namespaces=["trials"],
            config=RetrievalConfig(
                top_k=30,
                expand_query=False,  # Trials need exact matching
                min_score=0.2
            )
        )
