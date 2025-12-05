"""Tests for Pydantic models."""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from models.patient import (
    Patient, CancerDetails, CancerType, CancerStage, ECOGStatus,
    Comorbidity, OrganFunction, PatientSummary
)
from models.genomics import (
    GenomicReport, Mutation, MutationClassification,
    ImmunotherapyMarkers, Therapy
)
from models.treatment import (
    TreatmentPlan, TreatmentOption, RecommendationLevel, EvidenceLevel,
    ClinicalTrial, TrialPhase, TrialStatus, EligibilityCriterion
)
from models.messages import (
    AgentType, MessageType, AgentStatus, AgentMessage, AgentResponse,
    AnalysisRequest, AnalysisProgress, AnalysisResult,
    ChatMessage, ChatRequest, ChatResponse
)


class TestPatientModels:
    """Tests for patient-related models."""

    def test_patient_creation(self, mock_patient):
        """Test creating a valid patient."""
        assert mock_patient.id == "TEST001"
        assert mock_patient.first_name == "John"
        assert mock_patient.last_name == "Doe"
        assert mock_patient.full_name == "John Doe"

    def test_patient_age_calculation(self, mock_patient):
        """Test patient age calculation."""
        # Patient born in 1960
        age = mock_patient.age
        assert age >= 64  # Will be at least 64 in 2024

    def test_patient_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Patient(
                id="TEST",
                first_name="John"
                # Missing required fields
            )

    def test_cancer_details_creation(self):
        """Test creating cancer details."""
        cancer = CancerDetails(
            cancer_type=CancerType.NSCLC,
            stage=CancerStage.STAGE_IIIA,
            primary_site="Lung"
        )
        assert cancer.cancer_type == CancerType.NSCLC
        assert cancer.stage == CancerStage.STAGE_IIIA

    def test_comorbidity_creation(self):
        """Test creating comorbidity."""
        comorb = Comorbidity(
            condition="Diabetes",
            severity="moderate",
            treatment_implications=["Monitor glucose"]
        )
        assert comorb.condition == "Diabetes"
        assert len(comorb.treatment_implications) == 1

    def test_ecog_status_values(self):
        """Test ECOG status enum values."""
        assert ECOGStatus.FULLY_ACTIVE.value == 0
        assert ECOGStatus.RESTRICTED.value == 1
        assert ECOGStatus.DISABLED.value == 4

    def test_patient_summary_creation(self, mock_patient):
        """Test creating patient summary."""
        summary = PatientSummary(
            demographics={"age": 63, "sex": "Male"},
            cancer=mock_patient.cancer_details,
            comorbidities=mock_patient.comorbidities,
            organ_function=mock_patient.organ_function,
            ecog_status=ECOGStatus.RESTRICTED,
            current_medications=mock_patient.current_medications,
            allergies=mock_patient.allergies,
            treatment_implications=["Renal dosing required"]
        )
        assert summary.ecog_status == ECOGStatus.RESTRICTED


class TestGenomicsModels:
    """Tests for genomics-related models."""

    def test_mutation_creation(self):
        """Test creating a mutation."""
        mutation = Mutation(
            gene="EGFR",
            variant="L858R",
            classification=MutationClassification.PATHOGENIC_ACTIONABLE,
            allele_frequency=0.45,
            tier="Tier I"
        )
        assert mutation.gene == "EGFR"
        assert mutation.classification == MutationClassification.PATHOGENIC_ACTIONABLE

    def test_mutation_with_therapies(self):
        """Test mutation with associated therapies."""
        therapy = Therapy(
            drug="Osimertinib",
            evidence_level="FDA Approved",
            response_rate=0.80,
            indication="EGFR+ NSCLC"
        )
        mutation = Mutation(
            gene="EGFR",
            variant="Exon 19 del",
            classification=MutationClassification.PATHOGENIC_ACTIONABLE,
            allele_frequency=0.34,
            therapies=[therapy]
        )
        assert len(mutation.therapies) == 1
        assert mutation.therapies[0].drug == "Osimertinib"

    def test_immunotherapy_markers(self):
        """Test immunotherapy markers creation."""
        markers = ImmunotherapyMarkers(
            pdl1_expression=50.0,
            tmb=12.0,
            msi_status="MSI-H"
        )
        assert markers.pdl1_expression == 50.0
        assert markers.msi_status == "MSI-H"

    def test_genomic_report_creation(self, mock_genomic_report):
        """Test creating a genomic report."""
        assert mock_genomic_report.id == "GR-TEST001"
        assert len(mock_genomic_report.mutations) == 2
        assert mock_genomic_report.immunotherapy_markers.msi_status == "MSS"


class TestTreatmentModels:
    """Tests for treatment-related models."""

    def test_treatment_option_creation(self):
        """Test creating a treatment option."""
        option = TreatmentOption(
            id="TO-001",
            rank=1,
            name="Osimertinib",
            category="Targeted Therapy",
            recommendation_level=RecommendationLevel.STRONGLY_RECOMMENDED,
            confidence_score=0.95
        )
        assert option.rank == 1
        assert option.recommendation_level == RecommendationLevel.STRONGLY_RECOMMENDED

    def test_evidence_level_values(self):
        """Test evidence level enum values."""
        assert "Level 1" in EvidenceLevel.LEVEL_1.value
        assert "Level 2" in EvidenceLevel.LEVEL_2.value

    def test_clinical_trial_creation(self, mock_clinical_trial):
        """Test creating a clinical trial."""
        assert mock_clinical_trial.nct_id == "NCT12345678"
        assert mock_clinical_trial.phase == TrialPhase.PHASE_3
        assert mock_clinical_trial.match_score == 0.90

    def test_eligibility_criterion(self):
        """Test eligibility criterion creation."""
        criterion = EligibilityCriterion(
            criterion="ECOG 0-1",
            inclusion=True,
            patient_meets=True
        )
        assert criterion.inclusion is True
        assert criterion.patient_meets is True

    def test_treatment_plan_creation(self, mock_treatment_plan):
        """Test creating a treatment plan."""
        assert mock_treatment_plan.id == "TP-TEST001"
        assert mock_treatment_plan.status == "pending_review"
        assert mock_treatment_plan.primary_recommendation is not None


class TestMessageModels:
    """Tests for message-related models."""

    def test_agent_type_values(self):
        """Test agent type enum values."""
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
        assert AgentType.GENOMICS.value == "genomics"

    def test_agent_message_creation(self):
        """Test creating an agent message."""
        msg = AgentMessage(
            id="MSG-001",
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.MEDICAL_HISTORY,
            message_type=MessageType.REQUEST,
            task="analyze_history"
        )
        assert msg.sender == AgentType.ORCHESTRATOR
        assert msg.message_type == MessageType.REQUEST

    def test_analysis_request_creation(self, mock_analysis_request):
        """Test creating an analysis request."""
        assert mock_analysis_request.patient_id == "TEST001"
        assert mock_analysis_request.analysis_type == "full"
        assert mock_analysis_request.include_trials is True

    def test_analysis_progress_creation(self):
        """Test creating analysis progress."""
        progress = AnalysisProgress(
            request_id="REQ-001",
            patient_id="TEST001",
            status="in_progress",
            current_step="genomics_analysis",
            progress_percent=50
        )
        assert progress.progress_percent == 50
        assert progress.current_step == "genomics_analysis"

    def test_chat_message_creation(self, mock_chat_message):
        """Test creating a chat message."""
        assert mock_chat_message.role == "patient"
        assert "treatment" in mock_chat_message.content.lower()

    def test_chat_response_creation(self):
        """Test creating a chat response."""
        response = ChatResponse(
            patient_id="TEST001",
            response="Here are your treatment options...",
            sources_used=["NCCN Guidelines"],
            escalate_to_human=False
        )
        assert response.escalate_to_human is False
        assert len(response.sources_used) == 1


class TestModelSerialization:
    """Tests for model serialization."""

    def test_patient_to_dict(self, mock_patient):
        """Test patient serialization to dict."""
        data = mock_patient.model_dump()
        assert data["id"] == "TEST001"
        assert "cancer_details" in data

    def test_patient_to_json(self, mock_patient):
        """Test patient serialization to JSON."""
        json_str = mock_patient.model_dump_json()
        assert "TEST001" in json_str
        assert "John" in json_str

    def test_genomic_report_to_dict(self, mock_genomic_report):
        """Test genomic report serialization."""
        data = mock_genomic_report.model_dump()
        assert len(data["mutations"]) == 2

    def test_treatment_plan_to_dict(self, mock_treatment_plan):
        """Test treatment plan serialization."""
        data = mock_treatment_plan.model_dump()
        assert data["status"] == "pending_review"
