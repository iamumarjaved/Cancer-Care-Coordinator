"""Vector Store Service for managing RAG vector stores."""

from typing import Dict, List, Optional, Any
import logging

from rag.embeddings import EmbeddingService
from rag.vector_store import VectorStore, SearchResult
from rag.retriever import Retriever, RetrievalConfig
from rag.reranker import Reranker, RerankerConfig
from rag.ingestion import DataIngestion


class VectorStoreService:
    """Service for managing vector stores and retrieval.

    Provides a unified interface for:
    - Creating and managing vector stores by namespace
    - Indexing documents
    - Searching with retrieval and reranking
    - Managing mock data
    """

    # Default namespaces
    DEFAULT_NAMESPACES = ["evidence", "trials", "genomics", "guidelines", "procedures"]

    def __init__(self, use_mock: bool = True):
        """Initialize vector store service.

        Args:
            use_mock: Whether to use mock mode
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger("service.vector_store")

        # Initialize embedding service
        self.embedding_service = EmbeddingService(use_mock=use_mock)

        # Initialize vector stores for each namespace
        self.vector_stores: Dict[str, VectorStore] = {}
        for namespace in self.DEFAULT_NAMESPACES:
            self.vector_stores[namespace] = VectorStore(
                embedding_service=self.embedding_service,
                use_mock=use_mock,
                namespace=namespace
            )

        # Initialize retriever
        self.retriever = Retriever(
            embedding_service=self.embedding_service,
            vector_stores=self.vector_stores,
            use_mock=use_mock
        )

        # Initialize reranker
        self.reranker = Reranker(
            embedding_service=self.embedding_service,
            use_mock=use_mock
        )

        # Initialize data ingestion
        self.ingestion = DataIngestion(
            embedding_service=self.embedding_service,
            vector_stores=self.vector_stores
        )

        self._initialized = False

    async def initialize(self) -> Dict[str, int]:
        """Initialize vector stores with mock data.

        Returns:
            Dict mapping namespace to document count
        """
        if self._initialized:
            self.logger.info("Vector stores already initialized")
            return self.get_document_counts()

        self.logger.info("Initializing vector stores with mock data...")
        results = await self.ingestion.load_all_mock_data()
        self._initialized = True

        self.logger.info(f"Initialized vector stores: {results}")
        return results

    async def index_document(
        self,
        namespace: str,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Index a document in a namespace.

        Args:
            namespace: Vector store namespace
            doc_id: Document ID
            content: Document content
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if namespace not in self.vector_stores:
            self.logger.error(f"Unknown namespace: {namespace}")
            return False

        return await self.vector_stores[namespace].upsert(doc_id, content, metadata)

    async def search(
        self,
        query: str,
        namespaces: Optional[List[str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        filter_metadata: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query
            namespaces: Namespaces to search (None = all)
            top_k: Maximum results
            min_score: Minimum score threshold
            filter_metadata: Optional metadata filter
            rerank: Whether to rerank results

        Returns:
            List of search results
        """
        # Configure retrieval
        retrieval_config = RetrievalConfig(
            top_k=top_k * 2 if rerank else top_k,  # Get more for reranking
            expand_query=True,
            min_score=min_score * 0.7,  # Lower threshold before reranking
            diversity_factor=0.1
        )

        # Retrieve results
        results = await self.retriever.retrieve(
            query=query,
            namespaces=namespaces,
            config=retrieval_config,
            filter_metadata=filter_metadata
        )

        # Rerank if requested
        if rerank and len(results) > 0:
            reranker_config = RerankerConfig(
                top_k=top_k,
                boost_recency=True,
                boost_source_quality=True
            )
            results = await self.reranker.rerank(query, results, reranker_config)

        # Filter by final score threshold
        results = [r for r in results if r.score >= min_score]

        return results[:top_k]

    async def search_evidence(
        self,
        treatment: str,
        cancer_type: Optional[str] = None,
        mutations: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for treatment evidence.

        Args:
            treatment: Treatment name
            cancer_type: Optional cancer type
            mutations: Optional mutations

        Returns:
            Relevant evidence
        """
        query_parts = [treatment]
        if cancer_type:
            query_parts.append(cancer_type)
        if mutations:
            query_parts.extend(mutations[:2])

        query = " ".join(query_parts)

        return await self.search(
            query=query,
            namespaces=["evidence", "guidelines"],
            top_k=15
        )

    async def search_trials(
        self,
        cancer_type: str,
        mutations: Optional[List[str]] = None,
        status: str = "Recruiting"
    ) -> List[SearchResult]:
        """Search for clinical trials.

        Args:
            cancer_type: Cancer type
            mutations: Optional mutations
            status: Trial status filter

        Returns:
            Matching trials
        """
        query_parts = [cancer_type, "clinical trial", status]
        if mutations:
            query_parts.extend(mutations[:3])

        query = " ".join(query_parts)

        return await self.search(
            query=query,
            namespaces=["trials"],
            top_k=20,
            filter_metadata={"status": status} if status else None
        )

    async def search_mutations(
        self,
        gene: str,
        variant: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for mutation information.

        Args:
            gene: Gene name
            variant: Optional variant

        Returns:
            Mutation information
        """
        query = f"{gene} {variant or ''} mutation targeted therapy"

        return await self.search(
            query=query,
            namespaces=["genomics"],
            top_k=10
        )

    async def delete_document(
        self,
        namespace: str,
        doc_id: str
    ) -> bool:
        """Delete a document.

        Args:
            namespace: Vector store namespace
            doc_id: Document ID

        Returns:
            True if deleted
        """
        if namespace not in self.vector_stores:
            return False

        return await self.vector_stores[namespace].delete(doc_id)

    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all documents in a namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            True if successful
        """
        if namespace not in self.vector_stores:
            return False

        return await self.vector_stores[namespace].clear()

    def get_document_counts(self) -> Dict[str, int]:
        """Get document counts for all namespaces.

        Returns:
            Dict mapping namespace to count
        """
        return {
            namespace: store.count
            for namespace, store in self.vector_stores.items()
        }

    def add_namespace(self, namespace: str) -> bool:
        """Add a new namespace.

        Args:
            namespace: Namespace name

        Returns:
            True if added
        """
        if namespace in self.vector_stores:
            return False

        self.vector_stores[namespace] = VectorStore(
            embedding_service=self.embedding_service,
            use_mock=self.use_mock,
            namespace=namespace
        )

        return True

    async def index_analysis_results(
        self,
        patient_id: str,
        analysis_id: str,
        analysis_data: dict
    ) -> Dict[str, int]:
        """Index analysis results for RAG retrieval.

        This indexes genomic findings, treatment recommendations, and trial matches
        so chat can retrieve relevant context for patient questions.

        Args:
            patient_id: The patient ID
            analysis_id: The analysis result ID
            analysis_data: The analysis result data dict

        Returns:
            Dict with count of documents indexed per category
        """
        indexed = {"genomic": 0, "treatment": 0, "trials": 0, "summary": 0}

        try:
            # Index genomic findings
            genomic_report = analysis_data.get("genomic_report", {})
            if genomic_report:
                mutations = genomic_report.get("mutations", [])
                for i, mutation in enumerate(mutations):
                    doc_id = f"{analysis_id}_genomic_{i}"
                    content = self._format_mutation_for_indexing(mutation)
                    if content:
                        await self.index_document(
                            namespace="genomics",
                            doc_id=doc_id,
                            content=content,
                            metadata={
                                "patient_id": patient_id,
                                "analysis_id": analysis_id,
                                "type": "mutation",
                                "gene": mutation.get("gene", "")
                            }
                        )
                        indexed["genomic"] += 1

                # Index immunotherapy markers
                markers = genomic_report.get("immunotherapy_markers", {})
                if markers:
                    doc_id = f"{analysis_id}_markers"
                    content = self._format_markers_for_indexing(markers)
                    if content:
                        await self.index_document(
                            namespace="genomics",
                            doc_id=doc_id,
                            content=content,
                            metadata={
                                "patient_id": patient_id,
                                "analysis_id": analysis_id,
                                "type": "immunotherapy_markers"
                            }
                        )
                        indexed["genomic"] += 1

            # Index treatment plan
            treatment_plan = analysis_data.get("treatment_plan", {})
            if treatment_plan:
                options = treatment_plan.get("treatment_options", [])
                for i, option in enumerate(options):
                    doc_id = f"{analysis_id}_treatment_{i}"
                    content = self._format_treatment_for_indexing(option)
                    if content:
                        await self.index_document(
                            namespace="evidence",
                            doc_id=doc_id,
                            content=content,
                            metadata={
                                "patient_id": patient_id,
                                "analysis_id": analysis_id,
                                "type": "treatment_recommendation",
                                "treatment_name": option.get("name", "")
                            }
                        )
                        indexed["treatment"] += 1

            # Index matched trials
            matched_trials = analysis_data.get("matched_trials", [])
            for i, trial in enumerate(matched_trials):
                doc_id = f"{analysis_id}_trial_{i}"
                content = self._format_trial_for_indexing(trial)
                if content:
                    await self.index_document(
                        namespace="trials",
                        doc_id=doc_id,
                        content=content,
                        metadata={
                            "patient_id": patient_id,
                            "analysis_id": analysis_id,
                            "type": "matched_trial",
                            "nct_id": trial.get("nct_id", "")
                        }
                    )
                    indexed["trials"] += 1

            # Index overall summary
            summary = analysis_data.get("summary", "")
            key_findings = analysis_data.get("key_findings", [])
            recommendations = analysis_data.get("recommendations", [])

            if summary or key_findings or recommendations:
                doc_id = f"{analysis_id}_summary"
                content = f"""Patient Analysis Summary:
{summary}

Key Findings:
{chr(10).join('- ' + f for f in key_findings) if key_findings else 'None'}

Recommendations:
{chr(10).join('- ' + r for r in recommendations) if recommendations else 'None'}"""

                await self.index_document(
                    namespace="evidence",
                    doc_id=doc_id,
                    content=content,
                    metadata={
                        "patient_id": patient_id,
                        "analysis_id": analysis_id,
                        "type": "analysis_summary"
                    }
                )
                indexed["summary"] += 1

            self.logger.info(f"Indexed analysis results for patient {patient_id}: {indexed}")
            return indexed

        except Exception as e:
            self.logger.error(f"Failed to index analysis results: {e}")
            return indexed

    def _format_mutation_for_indexing(self, mutation: dict) -> str:
        """Format mutation data for vector indexing."""
        gene = mutation.get("gene", "")
        variant = mutation.get("variant", "")
        classification = mutation.get("classification", "")
        therapies = mutation.get("fda_approved_therapies", [])

        if not gene:
            return ""

        return f"""Genetic Mutation: {gene} {variant}
Classification: {classification}
FDA-Approved Therapies: {', '.join(therapies) if therapies else 'None'}
Clinical Significance: This mutation may affect treatment response and therapy selection."""

    def _format_markers_for_indexing(self, markers: dict) -> str:
        """Format immunotherapy markers for vector indexing."""
        pdl1 = markers.get("pdl1_expression", "Unknown")
        tmb = markers.get("tmb", "Unknown")
        msi = markers.get("msi_status", "Unknown")

        return f"""Immunotherapy Markers:
PD-L1 Expression: {pdl1}%
Tumor Mutational Burden (TMB): {tmb} mutations/Mb
MSI Status: {msi}
These markers help determine eligibility for immunotherapy treatments."""

    def _format_treatment_for_indexing(self, treatment: dict) -> str:
        """Format treatment recommendation for vector indexing."""
        name = treatment.get("name", "")
        category = treatment.get("category", "")
        rationale = treatment.get("rationale", "")
        confidence = treatment.get("confidence_score", 0)

        if not name:
            return ""

        return f"""Treatment Recommendation: {name}
Category: {category}
Confidence Score: {confidence:.0%}
Rationale: {rationale}"""

    def _format_trial_for_indexing(self, trial: dict) -> str:
        """Format clinical trial for vector indexing."""
        nct_id = trial.get("nct_id", "")
        title = trial.get("title", "")
        phase = trial.get("phase", "")
        match_score = trial.get("match_score", 0)
        eligibility = trial.get("eligibility_summary", "")

        if not nct_id:
            return ""

        return f"""Clinical Trial: {title}
NCT ID: {nct_id}
Phase: {phase}
Match Score: {match_score:.0%}
Eligibility: {eligibility}"""

    async def search_patient_context(
        self,
        patient_id: str,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Search for patient-specific context.

        Args:
            patient_id: Filter results to this patient
            query: Search query
            top_k: Max results

        Returns:
            Relevant patient-specific results
        """
        results = await self.search(
            query=query,
            namespaces=["evidence", "genomics", "trials"],
            top_k=top_k * 2,  # Get more, then filter
            filter_metadata={"patient_id": patient_id}
        )

        # Filter to patient-specific results
        patient_results = [r for r in results if r.metadata.get("patient_id") == patient_id]

        return patient_results[:top_k]

    async def health_check(self) -> Dict[str, Any]:
        """Check health of vector store service.

        Returns:
            Health status
        """
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "use_mock": self.use_mock,
            "namespaces": list(self.vector_stores.keys()),
            "document_counts": self.get_document_counts()
        }

    async def index_treatment_procedures(
        self,
        patient_id: str,
        procedures: List[dict]
    ) -> Dict[str, int]:
        """Index treatment procedures for RAG retrieval.

        This indexes procedure details, administration records, and adverse events
        so chat and analysis can retrieve relevant context.

        Args:
            patient_id: The patient ID
            procedures: List of procedure dicts

        Returns:
            Dict with count of documents indexed per category
        """
        indexed = {"procedures": 0, "adverse_events": 0}

        try:
            for proc in procedures:
                # Index procedure details
                proc_id = proc.get("id", "")
                if not proc_id:
                    continue

                content = self._format_procedure_for_indexing(proc)
                if content:
                    await self.index_document(
                        namespace="procedures",
                        doc_id=f"proc_{proc_id}",
                        content=content,
                        metadata={
                            "patient_id": patient_id,
                            "procedure_id": proc_id,
                            "procedure_type": proc.get("procedure_type", ""),
                            "status": proc.get("status", ""),
                            "type": "procedure"
                        }
                    )
                    indexed["procedures"] += 1

                # Index adverse events separately for better retrieval
                adverse_events = proc.get("adverse_events", [])
                for i, ae in enumerate(adverse_events):
                    ae_content = f"""Adverse Event during {proc.get('procedure_name', 'procedure')}:
Event: {ae.get('event', 'Unknown')}
Grade: {ae.get('grade', 'N/A')} (CTCAE)
Notes: {ae.get('notes', 'None')}
Date: {proc.get('actual_date', proc.get('scheduled_date', 'Unknown'))}"""

                    await self.index_document(
                        namespace="procedures",
                        doc_id=f"proc_{proc_id}_ae_{i}",
                        content=ae_content,
                        metadata={
                            "patient_id": patient_id,
                            "procedure_id": proc_id,
                            "type": "adverse_event",
                            "event": ae.get("event", ""),
                            "grade": ae.get("grade")
                        }
                    )
                    indexed["adverse_events"] += 1

            self.logger.info(f"Indexed procedures for patient {patient_id}: {indexed}")
            return indexed

        except Exception as e:
            self.logger.error(f"Failed to index procedures: {e}")
            return indexed

    def _format_procedure_for_indexing(self, proc: dict) -> str:
        """Format procedure data for vector indexing."""
        procedure_name = proc.get("procedure_name", "")
        procedure_type = proc.get("procedure_type", "")
        status = proc.get("status", "")
        day_number = proc.get("day_number", "")
        scheduled_date = proc.get("scheduled_date", "")
        actual_date = proc.get("actual_date", "")
        actual_dose = proc.get("actual_dose", "")
        notes = proc.get("administration_notes", "")

        if not procedure_name:
            return ""

        content = f"""Treatment Procedure: {procedure_name}
Type: {procedure_type}
Cycle Day: Day {day_number}
Status: {status}
Scheduled Date: {scheduled_date}"""

        if status == "completed":
            content += f"\nCompleted Date: {actual_date or scheduled_date}"
            if actual_dose:
                content += f"\nDose Administered: {actual_dose}"
            if notes:
                content += f"\nNotes: {notes}"

        # Add lab results summary if present
        lab_results = proc.get("lab_results")
        if lab_results:
            content += "\nLab Results: "
            lab_items = []
            for test, result in lab_results.items():
                if isinstance(result, dict):
                    lab_items.append(f"{test}: {result.get('value', 'N/A')} {result.get('unit', '')} ({result.get('flag', 'normal')})")
                else:
                    lab_items.append(f"{test}: {result}")
            content += ", ".join(lab_items)

        # Add imaging results summary if present
        imaging_results = proc.get("imaging_results")
        if imaging_results:
            content += f"\nImaging ({imaging_results.get('modality', 'Unknown')}): {imaging_results.get('impression', imaging_results.get('findings', 'No findings'))}"

        return content

    async def search_patient_procedures(
        self,
        patient_id: str,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Search patient procedures for RAG.

        Args:
            patient_id: Filter results to this patient
            query: Search query
            top_k: Max results

        Returns:
            Relevant procedure results
        """
        return await self.search(
            query=query,
            namespaces=["procedures"],
            top_k=top_k,
            filter_metadata={"patient_id": patient_id}
        )

    async def index_single_procedure(
        self,
        patient_id: str,
        procedure: dict
    ) -> bool:
        """Index a single procedure after creation/update.

        Args:
            patient_id: The patient ID
            procedure: Procedure dict

        Returns:
            True if indexed successfully
        """
        result = await self.index_treatment_procedures(patient_id, [procedure])
        return result.get("procedures", 0) > 0
