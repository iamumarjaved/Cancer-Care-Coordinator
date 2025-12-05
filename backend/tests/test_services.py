"""Tests for service layer."""

import pytest
from datetime import date

from services.llm_service import LLMService
from services.patient_service import PatientService
from services.analysis_service import AnalysisService
from services.vector_store_service import VectorStoreService
from models.messages import AnalysisRequest


class TestLLMService:
    """Tests for LLMService."""

    @pytest.fixture
    def llm_service(self):
        """Create LLM service for testing."""
        return LLMService(use_mock=True)

    @pytest.mark.asyncio
    async def test_complete_returns_string(self, llm_service):
        """Test that complete returns a string response."""
        response = await llm_service.complete(
            prompt="What is the treatment for EGFR+ NSCLC?",
            system_prompt="You are a medical assistant."
        )

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_complete_with_context(self, llm_service):
        """Test complete with additional context."""
        response = await llm_service.complete(
            prompt="Summarize the patient case",
            system_prompt="You are a medical assistant.",
            context={"patient_id": "P001", "diagnosis": "NSCLC"}
        )

        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_complete_with_temperature(self, llm_service):
        """Test complete with temperature setting."""
        response = await llm_service.complete(
            prompt="Generate treatment options",
            temperature=0.7
        )

        assert isinstance(response, str)

    def test_mock_mode_enabled(self, llm_service):
        """Test that mock mode is properly set."""
        assert llm_service._use_mock is True


class TestPatientService:
    """Tests for PatientService."""

    @pytest.fixture
    def patient_service(self):
        """Create patient service for testing."""
        return PatientService()

    @pytest.mark.asyncio
    async def test_get_all_patients(self, patient_service):
        """Test getting all patients."""
        patients = await patient_service.get_all()

        assert isinstance(patients, list)
        assert len(patients) >= 3  # We have 3 mock patients

    @pytest.mark.asyncio
    async def test_get_patient_by_id(self, patient_service):
        """Test getting patient by ID."""
        patient = await patient_service.get_by_id("P001")

        assert patient is not None
        assert patient.patient_id == "P001"

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, patient_service):
        """Test getting non-existent patient."""
        patient = await patient_service.get_by_id("NONEXISTENT")

        assert patient is None

    @pytest.mark.asyncio
    async def test_get_patients_with_cancer_type_filter(self, patient_service):
        """Test filtering patients by cancer type."""
        patients = await patient_service.get_all(cancer_type="NSCLC")

        assert all("nsclc" in p.cancer_details.cancer_type.lower() for p in patients)

    @pytest.mark.asyncio
    async def test_get_patients_with_status_filter(self, patient_service):
        """Test filtering patients by status."""
        patients = await patient_service.get_all(status="Active Treatment")

        assert all(p.status == "Active Treatment" for p in patients)

    @pytest.mark.asyncio
    async def test_get_patient_summary(self, patient_service):
        """Test getting patient summary."""
        summary = await patient_service.get_patient_summary("P001")

        assert summary is not None
        assert summary.patient_id == "P001"
        assert summary.name is not None

    @pytest.mark.asyncio
    async def test_get_genomic_report(self, patient_service):
        """Test getting genomic report."""
        report = await patient_service.get_genomic_report("P001")

        assert report is not None
        assert report.patient_id == "P001"

    @pytest.mark.asyncio
    async def test_search_patients(self, patient_service):
        """Test searching patients."""
        results = await patient_service.search("chen")

        assert len(results) >= 1
        # Should find patient with last name Chen


class TestAnalysisService:
    """Tests for AnalysisService."""

    @pytest.fixture
    def analysis_service(self, patient_service):
        """Create analysis service for testing."""
        llm_service = LLMService(use_mock=True)
        return AnalysisService(
            llm_service=llm_service,
            patient_service=patient_service,
            use_mock=True
        )

    @pytest.mark.asyncio
    async def test_start_analysis(self, analysis_service):
        """Test starting an analysis."""
        request = AnalysisRequest(
            patient_id="P001",
            include_trials=True,
            include_evidence=True
        )

        request_id = await analysis_service.start_analysis(request)

        assert request_id is not None
        assert "REQ-" in request_id
        assert "P001" in request_id

    @pytest.mark.asyncio
    async def test_get_status(self, analysis_service):
        """Test getting analysis status."""
        request = AnalysisRequest(patient_id="P001")
        request_id = await analysis_service.start_analysis(request)

        status = await analysis_service.get_status(request_id)

        assert status is not None
        assert status.request_id == request_id

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, analysis_service):
        """Test getting status for non-existent request."""
        status = await analysis_service.get_status("NONEXISTENT")

        assert status is None

    @pytest.mark.asyncio
    async def test_run_analysis_complete(self, analysis_service):
        """Test running analysis to completion."""
        request = AnalysisRequest(
            patient_id="P001",
            include_trials=True,
            include_evidence=True
        )

        request_id = await analysis_service.start_analysis(request)
        result = await analysis_service.run_analysis(request_id)

        assert result is not None
        assert result.patient_id == "P001"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_run_analysis_patient_not_found(self, analysis_service):
        """Test running analysis for non-existent patient."""
        request = AnalysisRequest(patient_id="NONEXISTENT")

        request_id = await analysis_service.start_analysis(request)
        result = await analysis_service.run_analysis(request_id)

        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_stream_progress(self, analysis_service):
        """Test streaming analysis progress."""
        request = AnalysisRequest(patient_id="P001")
        request_id = await analysis_service.start_analysis(request)

        progress_updates = []
        async for progress in analysis_service.stream_progress(request_id):
            progress_updates.append(progress)

        # Should have multiple progress updates
        assert len(progress_updates) > 1

        # Progress should increase
        progress_values = [p.progress_percent for p in progress_updates]
        assert progress_values[-1] >= progress_values[0]

    @pytest.mark.asyncio
    async def test_get_results(self, analysis_service):
        """Test getting analysis results."""
        request = AnalysisRequest(patient_id="P001")
        request_id = await analysis_service.start_analysis(request)

        # Run to completion
        await analysis_service.run_analysis(request_id)

        # Get results
        result = await analysis_service.get_results(request_id)

        assert result is not None
        assert result.patient_id == "P001"

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, analysis_service):
        """Test getting results for non-existent request."""
        result = await analysis_service.get_results("NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_active_analyses(self, analysis_service):
        """Test listing active analyses."""
        # Start some analyses
        await analysis_service.start_analysis(AnalysisRequest(patient_id="P001"))
        await analysis_service.start_analysis(AnalysisRequest(patient_id="P002"))

        active = analysis_service.list_active_analyses()

        assert len(active) >= 2


class TestVectorStoreService:
    """Tests for VectorStoreService."""

    @pytest.fixture
    def vector_service(self):
        """Create vector store service for testing."""
        return VectorStoreService(use_mock=True)

    @pytest.mark.asyncio
    async def test_initialize(self, vector_service):
        """Test initializing vector stores."""
        results = await vector_service.initialize()

        assert isinstance(results, dict)
        # Should have initialized default namespaces
        assert "evidence" in results
        assert "trials" in results

    @pytest.mark.asyncio
    async def test_index_document(self, vector_service):
        """Test indexing a document."""
        success = await vector_service.index_document(
            namespace="evidence",
            doc_id="test_doc",
            content="EGFR mutation treatment with osimertinib",
            metadata={"source": "test"}
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_index_document_invalid_namespace(self, vector_service):
        """Test indexing to invalid namespace."""
        success = await vector_service.index_document(
            namespace="invalid",
            doc_id="test_doc",
            content="Test content"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_search(self, vector_service):
        """Test searching documents."""
        # Initialize with mock data
        await vector_service.initialize()

        results = await vector_service.search(
            query="EGFR mutation treatment",
            namespaces=["evidence"],
            top_k=5
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_all_namespaces(self, vector_service):
        """Test searching all namespaces."""
        await vector_service.initialize()

        results = await vector_service.search(
            query="lung cancer",
            namespaces=None,  # All namespaces
            top_k=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_evidence(self, vector_service):
        """Test searching for treatment evidence."""
        await vector_service.initialize()

        results = await vector_service.search_evidence(
            treatment="osimertinib",
            cancer_type="NSCLC",
            mutations=["EGFR"]
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_trials(self, vector_service):
        """Test searching for clinical trials."""
        await vector_service.initialize()

        results = await vector_service.search_trials(
            cancer_type="NSCLC",
            mutations=["EGFR"],
            status="Recruiting"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_mutations(self, vector_service):
        """Test searching for mutation information."""
        await vector_service.initialize()

        results = await vector_service.search_mutations(
            gene="EGFR",
            variant="L858R"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_delete_document(self, vector_service):
        """Test deleting a document."""
        # Index a document first
        await vector_service.index_document(
            namespace="evidence",
            doc_id="to_delete",
            content="Temporary content"
        )

        # Delete it
        success = await vector_service.delete_document("evidence", "to_delete")

        assert success is True

    @pytest.mark.asyncio
    async def test_clear_namespace(self, vector_service):
        """Test clearing a namespace."""
        # Index some documents
        await vector_service.index_document("evidence", "doc1", "Content 1")
        await vector_service.index_document("evidence", "doc2", "Content 2")

        # Clear namespace
        success = await vector_service.clear_namespace("evidence")

        assert success is True
        counts = vector_service.get_document_counts()
        assert counts["evidence"] == 0

    def test_get_document_counts(self, vector_service):
        """Test getting document counts."""
        counts = vector_service.get_document_counts()

        assert isinstance(counts, dict)
        assert "evidence" in counts
        assert "trials" in counts

    def test_add_namespace(self, vector_service):
        """Test adding a new namespace."""
        success = vector_service.add_namespace("custom")

        assert success is True
        assert "custom" in vector_service.vector_stores

    def test_add_existing_namespace(self, vector_service):
        """Test adding an existing namespace."""
        success = vector_service.add_namespace("evidence")

        assert success is False  # Already exists

    @pytest.mark.asyncio
    async def test_health_check(self, vector_service):
        """Test health check."""
        health = await vector_service.health_check()

        assert health["status"] == "healthy"
        assert "namespaces" in health
        assert "document_counts" in health
