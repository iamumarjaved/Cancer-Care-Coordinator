"""Tests for Orchestrator Agent."""

import pytest
from datetime import date

from agents.orchestrator_agent import (
    OrchestratorAgent, OrchestratorInput, AnalysisStep
)
from services.llm_service import LLMService
from services.patient_service import PatientService


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent."""

    @pytest.fixture
    def orchestrator(self, patient_service):
        """Create orchestrator agent for testing."""
        llm_service = LLMService(use_mock=True)
        return OrchestratorAgent(
            llm_service=llm_service,
            patient_service=patient_service,
            use_mock=True
        )

    @pytest.mark.asyncio
    async def test_run_analysis_success(self, orchestrator):
        """Test successful analysis run."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True,
            include_evidence=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result is not None
        assert result.result.patient_id == "P001"
        assert result.result.status == "completed"
        assert result.state.progress_percent == 100

    @pytest.mark.asyncio
    async def test_run_analysis_patient_not_found(self, orchestrator):
        """Test analysis with non-existent patient."""
        input_data = OrchestratorInput(
            patient_id="NONEXISTENT",
            include_trials=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.status == "error"
        assert "not found" in result.result.summary.lower()

    @pytest.mark.asyncio
    async def test_run_analysis_without_trials(self, orchestrator):
        """Test analysis without clinical trials."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=False,
            include_evidence=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.status == "completed"
        # Trials step should be skipped
        assert "clinical_trials (skipped)" in result.state.steps_completed

    @pytest.mark.asyncio
    async def test_run_analysis_state_progression(self, orchestrator):
        """Test that state progresses through all steps."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True,
            include_evidence=True
        )

        result = await orchestrator.run_analysis(input_data)

        # All steps should be completed
        expected_steps = {"medical_history", "genomics", "clinical_trials", "evidence", "treatment", "synthesizing"}
        completed = set(result.state.steps_completed)

        assert expected_steps.issubset(completed)
        assert len(result.state.steps_remaining) == 0

    @pytest.mark.asyncio
    async def test_run_streaming(self, orchestrator):
        """Test streaming progress updates."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True
        )

        progress_updates = []
        async for progress in orchestrator.run_streaming(input_data):
            progress_updates.append(progress)

        # Should have received multiple updates
        assert len(progress_updates) > 1

        # Progress should increase over time
        progress_values = [p.progress_percent for p in progress_updates]
        assert progress_values[-1] >= progress_values[0]

        # Final update should be completed
        assert progress_updates[-1].status == "completed"

    @pytest.mark.asyncio
    async def test_analysis_result_contains_key_findings(self, orchestrator):
        """Test that result contains key findings."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.key_findings is not None
        assert len(result.result.key_findings) > 0

    @pytest.mark.asyncio
    async def test_analysis_result_contains_recommendations(self, orchestrator):
        """Test that result contains recommendations."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.recommendations is not None
        assert len(result.result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analysis_result_contains_treatment_plan(self, orchestrator):
        """Test that result contains treatment plan."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.treatment_plan is not None
        assert result.result.treatment_plan["patient_id"] == "P001"

    @pytest.mark.asyncio
    async def test_analysis_result_contains_clinical_trials(self, orchestrator):
        """Test that result contains clinical trials when requested."""
        input_data = OrchestratorInput(
            patient_id="P001",
            include_trials=True
        )

        result = await orchestrator.run_analysis(input_data)

        assert result.result.clinical_trials is not None
        # May or may not have trials depending on patient profile

    @pytest.mark.asyncio
    async def test_get_patient_context(self, orchestrator):
        """Test getting patient context for chat."""
        context = await orchestrator.get_patient_context("P001")

        assert "patient_summary" in context
        assert "key_findings" in context
        assert "treatment_considerations" in context

    @pytest.mark.asyncio
    async def test_get_patient_context_not_found(self, orchestrator):
        """Test getting context for non-existent patient."""
        context = await orchestrator.get_patient_context("NONEXISTENT")

        assert context == {}

    def test_step_weights_sum_to_100(self, orchestrator):
        """Test that step weights sum to approximately 100."""
        total = sum(orchestrator.STEP_WEIGHTS.values())
        assert 95 <= total <= 105  # Allow small variance


class TestOrchestratorState:
    """Tests for orchestrator state management."""

    @pytest.fixture
    def orchestrator(self, patient_service):
        """Create orchestrator for testing."""
        llm_service = LLMService(use_mock=True)
        return OrchestratorAgent(
            llm_service=llm_service,
            patient_service=patient_service,
            use_mock=True
        )

    @pytest.mark.asyncio
    async def test_state_tracks_intermediate_outputs(self, orchestrator):
        """Test that state tracks all intermediate agent outputs."""
        input_data = OrchestratorInput(patient_id="P001")

        result = await orchestrator.run_analysis(input_data)

        state = result.state
        assert state.medical_history_output is not None
        assert state.genomics_output is not None
        assert state.treatment_output is not None

    @pytest.mark.asyncio
    async def test_state_has_request_id(self, orchestrator):
        """Test that state has unique request ID."""
        input_data = OrchestratorInput(patient_id="P001")

        result = await orchestrator.run_analysis(input_data)

        assert result.state.request_id is not None
        assert "REQ-" in result.state.request_id
        assert "P001" in result.state.request_id
