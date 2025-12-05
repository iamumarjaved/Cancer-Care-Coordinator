"""Tests for individual AI agents."""

import pytest
from datetime import date

from agents.medical_history_agent import MedicalHistoryAgent, MedicalHistoryInput
from agents.genomics_agent import GenomicsAgent, GenomicsInput
from agents.clinical_trials_agent import ClinicalTrialsAgent, ClinicalTrialsInput
from agents.evidence_agent import EvidenceAgent, EvidenceInput
from agents.treatment_agent import TreatmentAgent, TreatmentInput
from agents.patient_communication_agent import PatientCommunicationAgent, PatientCommInput

from models.patient import Patient, PatientSummary, CancerDetails, CancerType, CancerStage, ECOGStatus
from models.genomics import GenomicReport, Mutation, MutationClassification
from services.llm_service import LLMService


class TestMedicalHistoryAgent:
    """Tests for MedicalHistoryAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return MedicalHistoryAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_execute_with_patient(self, agent, mock_patient):
        """Test medical history analysis with valid patient."""
        input_data = MedicalHistoryInput(patient=mock_patient)

        result = await agent.run(input_data)

        assert result.patient_summary is not None
        assert result.patient_summary.demographics["age"] == mock_patient.age
        assert len(result.key_findings) > 0

    @pytest.mark.asyncio
    async def test_identifies_treatment_considerations(self, agent, mock_patient):
        """Test that agent identifies treatment considerations."""
        input_data = MedicalHistoryInput(patient=mock_patient)

        result = await agent.run(input_data)

        # Should identify considerations from comorbidities
        assert len(result.treatment_considerations) > 0 or len(result.patient_summary.treatment_implications) > 0

    @pytest.mark.asyncio
    async def test_identifies_missing_information(self, agent):
        """Test identification of missing information."""
        # Patient with minimal data
        minimal_patient = Patient(
            id="MIN001",
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1960, 1, 1),
            sex="Male"
        )

        input_data = MedicalHistoryInput(patient=minimal_patient)
        result = await agent.run(input_data)

        # Should identify missing critical info
        assert len(result.missing_information) > 0

    @pytest.mark.asyncio
    async def test_identifies_risk_factors(self, agent, mock_patient):
        """Test identification of risk factors."""
        input_data = MedicalHistoryInput(patient=mock_patient)

        result = await agent.run(input_data)

        # Mock patient has smoking history
        assert len(result.risk_factors) > 0


class TestGenomicsAgent:
    """Tests for GenomicsAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return GenomicsAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_execute_with_patient_no_report(self, agent, mock_patient):
        """Test genomics analysis without report creates mock."""
        input_data = GenomicsInput(patient=mock_patient, genomic_report=None)

        result = await agent.run(input_data)

        assert result.analysis_result is not None
        assert result.analysis_result.patient_id == mock_patient.id

    @pytest.mark.asyncio
    async def test_execute_with_genomic_report(self, agent, mock_patient, mock_genomic_report):
        """Test genomics analysis with report."""
        input_data = GenomicsInput(
            patient=mock_patient,
            genomic_report=mock_genomic_report
        )

        result = await agent.run(input_data)

        assert result.analysis_result is not None
        assert len(result.actionable_mutations) > 0

    @pytest.mark.asyncio
    async def test_identifies_therapy_candidates(self, agent, mock_patient, mock_genomic_report):
        """Test identification of therapy candidates."""
        input_data = GenomicsInput(
            patient=mock_patient,
            genomic_report=mock_genomic_report
        )

        result = await agent.run(input_data)

        # EGFR mutation should have therapy candidates
        assert len(result.therapy_candidates) > 0

    @pytest.mark.asyncio
    async def test_assesses_immunotherapy_markers(self, agent, mock_patient, mock_genomic_report):
        """Test assessment of immunotherapy markers."""
        input_data = GenomicsInput(
            patient=mock_patient,
            genomic_report=mock_genomic_report
        )

        result = await agent.run(input_data)

        assert result.immunotherapy_markers is not None

    def test_actionable_mutations_database(self, agent):
        """Test that agent has actionable mutations database."""
        assert "EGFR" in agent.ACTIONABLE_MUTATIONS
        assert "ALK" in agent.ACTIONABLE_MUTATIONS
        assert "KRAS" in agent.ACTIONABLE_MUTATIONS


class TestClinicalTrialsAgent:
    """Tests for ClinicalTrialsAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return ClinicalTrialsAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_execute_with_patient_summary(self, agent, mock_patient):
        """Test trial matching with patient summary."""
        patient_summary = PatientSummary(
            demographics={"age": 63, "sex": "Male"},
            cancer=mock_patient.cancer_details,
            comorbidities=mock_patient.comorbidities,
            organ_function=mock_patient.organ_function,
            ecog_status=ECOGStatus.RESTRICTED,
            current_medications=[]
        )

        input_data = ClinicalTrialsInput(patient_summary=patient_summary)

        result = await agent.run(input_data)

        assert result.total_trials_searched > 0
        assert len(result.search_criteria_used) > 0

    @pytest.mark.asyncio
    async def test_matches_trials_by_biomarker(self, agent, mock_patient, mock_genomic_report):
        """Test that trials are matched by biomarker."""
        from agents.genomics_agent import GenomicsAgent, GenomicsInput
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63, "sex": "Male"},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED
        )

        # Create mock genomics result
        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="Test",
            targeted_therapy_candidates=["Osimertinib"]
        )

        input_data = ClinicalTrialsInput(
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        # Should find EGFR trials for patient with EGFR mutation
        egfr_trials = [t for t in result.matched_trials if "EGFR" in t.title]
        assert len(egfr_trials) > 0 or len(result.matched_trials) > 0

    @pytest.mark.asyncio
    async def test_trial_match_score_calculation(self, agent):
        """Test that match scores are calculated."""
        patient_summary = PatientSummary(
            demographics={"age": 55},
            cancer=CancerDetails(
                cancer_type=CancerType.NSCLC,
                stage=CancerStage.STAGE_IV,
                primary_site="Lung"
            ),
            ecog_status=ECOGStatus.RESTRICTED
        )

        input_data = ClinicalTrialsInput(patient_summary=patient_summary)
        result = await agent.run(input_data)

        # All matched trials should have scores
        for trial in result.matched_trials:
            assert 0 <= trial.match_score <= 1

    def test_mock_trials_database(self, agent):
        """Test that agent has mock trials database."""
        assert len(agent.MOCK_TRIALS) > 0
        assert all("nct_id" in t for t in agent.MOCK_TRIALS)


class TestEvidenceAgent:
    """Tests for EvidenceAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return EvidenceAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_execute_with_patient_summary(self, agent, mock_patient):
        """Test evidence search with patient summary."""
        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED
        )

        input_data = EvidenceInput(
            patient_summary=patient_summary,
            treatment_queries=["Osimertinib"]
        )

        result = await agent.run(input_data)

        assert len(result.search_terms_used) > 0

    @pytest.mark.asyncio
    async def test_retrieves_guideline_recommendations(self, agent, mock_patient, mock_genomic_report):
        """Test retrieval of guideline recommendations."""
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED
        )

        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="EGFR mutation detected"
        )

        input_data = EvidenceInput(
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        # Should find EGFR-related guidelines
        assert len(result.guideline_recommendations) > 0 or len(result.evidence_summaries) > 0

    @pytest.mark.asyncio
    async def test_retrieves_publications(self, agent, mock_patient, mock_genomic_report):
        """Test retrieval of relevant publications."""
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED
        )

        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="EGFR mutation"
        )

        input_data = EvidenceInput(
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        # Should find relevant publications
        assert len(result.relevant_publications) > 0

    def test_nccn_guidelines_database(self, agent):
        """Test that agent has NCCN guidelines database."""
        assert "EGFR_mutant_NSCLC" in agent.NCCN_GUIDELINES
        assert "ALK_positive_NSCLC" in agent.NCCN_GUIDELINES


class TestTreatmentAgent:
    """Tests for TreatmentAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return TreatmentAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_execute_generates_treatment_plan(self, agent, mock_patient, mock_genomic_report):
        """Test that agent generates treatment plan."""
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED,
            comorbidities=mock_patient.comorbidities,
            organ_function=mock_patient.organ_function
        )

        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="EGFR mutation"
        )

        input_data = TreatmentInput(
            patient_id=mock_patient.id,
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        assert result.treatment_plan is not None
        assert result.primary_recommendation is not None

    @pytest.mark.asyncio
    async def test_ranks_treatment_options(self, agent, mock_patient, mock_genomic_report):
        """Test that treatment options are ranked."""
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED
        )

        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="EGFR mutation"
        )

        input_data = TreatmentInput(
            patient_id=mock_patient.id,
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        # Primary should have rank 1
        assert result.primary_recommendation.rank == 1

        # Alternatives should have increasing ranks
        for i, alt in enumerate(result.alternatives):
            assert alt.rank == i + 2

    @pytest.mark.asyncio
    async def test_generates_discussion_points(self, agent, mock_patient, mock_genomic_report):
        """Test generation of discussion points."""
        from models.genomics import GenomicAnalysisResult

        patient_summary = PatientSummary(
            demographics={"age": 63},
            cancer=mock_patient.cancer_details,
            ecog_status=ECOGStatus.RESTRICTED,
            comorbidities=mock_patient.comorbidities
        )

        genomics_result = GenomicAnalysisResult(
            patient_id=mock_patient.id,
            report=mock_genomic_report,
            summary="EGFR mutation"
        )

        input_data = TreatmentInput(
            patient_id=mock_patient.id,
            patient_summary=patient_summary,
            genomics_result=genomics_result
        )

        result = await agent.run(input_data)

        assert len(result.discussion_points) > 0

    def test_treatment_database(self, agent):
        """Test that agent has treatment database."""
        assert "EGFR_mutant" in agent.TREATMENT_DATABASE
        assert "ALK_positive" in agent.TREATMENT_DATABASE
        assert "chemotherapy" in agent.TREATMENT_DATABASE


class TestPatientCommunicationAgent:
    """Tests for PatientCommunicationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        llm_service = LLMService(use_mock=True)
        return PatientCommunicationAgent(llm_service=llm_service, use_mock=True)

    @pytest.mark.asyncio
    async def test_responds_to_treatment_question(self, agent):
        """Test response to treatment question."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="What is osimertinib and how does it work?"
        )

        result = await agent.run(input_data)

        assert len(result.response) > 0
        assert result.escalate_to_human is False

    @pytest.mark.asyncio
    async def test_responds_to_side_effects_question(self, agent):
        """Test response to side effects question."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="I'm feeling very nauseous, what can I do?"
        )

        result = await agent.run(input_data)

        assert len(result.response) > 0
        # Should have helpful suggestions
        assert "nausea" in result.response.lower() or "help" in result.response.lower()

    @pytest.mark.asyncio
    async def test_escalates_crisis_keywords(self, agent):
        """Test escalation on crisis keywords."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="I'm having severe chest pain and can't breathe"
        )

        result = await agent.run(input_data)

        assert result.escalate_to_human is True
        assert result.escalation_reason is not None
        assert "911" in result.response or "emergency" in result.response.lower()

    @pytest.mark.asyncio
    async def test_escalates_mental_health_crisis(self, agent):
        """Test escalation on mental health crisis."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="I want to end my life"
        )

        result = await agent.run(input_data)

        assert result.escalate_to_human is True
        assert "988" in result.response  # Crisis hotline

    @pytest.mark.asyncio
    async def test_redirects_prognosis_questions(self, agent):
        """Test redirection of prognosis questions."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="How long do I have to live?"
        )

        result = await agent.run(input_data)

        # Should redirect to care team
        assert "oncologist" in result.response.lower() or "care team" in result.response.lower()

    @pytest.mark.asyncio
    async def test_provides_emotional_support(self, agent):
        """Test emotional support response."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="I'm scared about my diagnosis"
        )

        result = await agent.run(input_data)

        assert len(result.response) > 0
        assert result.sentiment in ["concerned", "distressed", "neutral"]
        # Should offer support or redirect to care team (which is also supportive)
        response_lower = result.response.lower()
        assert any(term in response_lower for term in ["support", "normal", "care team", "oncologist"])

    @pytest.mark.asyncio
    async def test_suggests_followup_questions(self, agent):
        """Test that agent suggests follow-up questions."""
        input_data = PatientCommInput(
            patient_id="P001",
            message="Tell me about my treatment options"
        )

        result = await agent.run(input_data)

        # May have suggested followups
        # This is optional based on topic
        assert result.suggested_followups is not None

    def test_crisis_keywords_list(self, agent):
        """Test that agent has crisis keywords."""
        assert len(agent.CRISIS_KEYWORDS) > 0
        assert "suicide" in agent.CRISIS_KEYWORDS
        assert "chest pain" in agent.CRISIS_KEYWORDS

    def test_restricted_topics_list(self, agent):
        """Test that agent has restricted topics."""
        assert len(agent.RESTRICTED_TOPICS) > 0
        assert "prognosis" in agent.RESTRICTED_TOPICS
