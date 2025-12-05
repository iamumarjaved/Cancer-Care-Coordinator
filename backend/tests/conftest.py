"""Pytest configuration and fixtures for Cancer Care Coordinator tests."""

import pytest
from fastapi.testclient import TestClient
from datetime import date
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set mock mode for tests BEFORE importing app/services
os.environ["USE_MOCK_LLM"] = "true"
os.environ["USE_MOCK_VECTOR_STORE"] = "true"
os.environ["USE_MOCK_TRIALS_API"] = "true"

from main import app
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
    ClinicalTrial, TrialPhase, TrialStatus
)
from models.messages import (
    AnalysisRequest, AnalysisProgress, AnalysisResult,
    ChatMessage, ChatRequest, ChatResponse
)
from services.patient_service import PatientService
from services.llm_service import LLMService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_patient():
    """Create a mock patient for testing."""
    return Patient(
        id="TEST001",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1960, 6, 15),
        sex="Male",
        email="john.doe@test.com",
        phone="555-0100",
        cancer_details=CancerDetails(
            cancer_type=CancerType.NSCLC,
            subtype="Adenocarcinoma",
            stage=CancerStage.STAGE_IIIA,
            tnm_staging="T2N2M0",
            primary_site="Right upper lobe",
            tumor_size_cm=3.2,
            metastases=["Mediastinal lymph nodes"],
            histology="Adenocarcinoma",
            grade="High",
            diagnosis_date=date(2024, 1, 1)
        ),
        comorbidities=[
            Comorbidity(
                condition="Type 2 Diabetes",
                severity="moderate",
                treatment_implications=["Monitor blood glucose during treatment"]
            ),
            Comorbidity(
                condition="CKD Stage 3",
                severity="moderate",
                treatment_implications=["Dose adjustment may be required"]
            )
        ],
        organ_function=[
            OrganFunction(
                organ="Kidney",
                status="moderate_impairment",
                key_values={"GFR": 58, "Creatinine": 1.4},
                notes="CKD Stage 3"
            )
        ],
        ecog_status=ECOGStatus.RESTRICTED,
        current_medications=["Metformin 1000mg BID", "Lisinopril 10mg daily"],
        allergies=["Penicillin"],
        smoking_status="Former",
        pack_years=30,
        genomic_report_id="GR-TEST001"
    )


@pytest.fixture
def mock_genomic_report():
    """Create a mock genomic report for testing."""
    return GenomicReport(
        id="GR-TEST001",
        patient_id="TEST001",
        test_date="2024-01-15",
        test_type="Foundation One CDx",
        lab_name="Foundation Medicine",
        specimen_type="Tumor tissue",
        mutations=[
            Mutation(
                gene="EGFR",
                variant="Exon 19 deletion (p.E746_A750del)",
                classification=MutationClassification.PATHOGENIC_ACTIONABLE,
                allele_frequency=0.34,
                tier="Tier I",
                therapies=[
                    Therapy(
                        drug="Osimertinib",
                        evidence_level="FDA Approved",
                        response_rate=0.80,
                        indication="EGFR exon 19 deletion NSCLC"
                    )
                ]
            ),
            Mutation(
                gene="TP53",
                variant="R248W",
                classification=MutationClassification.PATHOGENIC,
                allele_frequency=0.28,
                tier="Tier III",
                therapies=[]
            )
        ],
        immunotherapy_markers=ImmunotherapyMarkers(
            pdl1_expression=15.0,
            pdl1_method="22C3 pharmDx",
            tmb=4.0,
            tmb_unit="mutations/Mb",
            msi_status="MSS"
        ),
        summary="EGFR exon 19 deletion detected. Actionable mutation with FDA-approved therapies."
    )


@pytest.fixture
def mock_treatment_plan():
    """Create a mock treatment plan for testing."""
    from datetime import datetime
    return TreatmentPlan(
        id="TP-TEST001",
        patient_id="TEST001",
        generated_at=datetime.now(),
        status="pending_review",
        primary_recommendation=TreatmentOption(
            id="TO-001",
            rank=1,
            name="Osimertinib (Tagrisso)",
            category="Targeted Therapy",
            recommendation_level=RecommendationLevel.STRONGLY_RECOMMENDED,
            confidence_score=0.95,
            evidence_level=EvidenceLevel.LEVEL_1,
            description="Third-generation EGFR TKI",
            dosing="80mg once daily",
            expected_outcomes={
                "response_rate": 0.80,
                "median_pfs_months": 18.9
            },
            supporting_evidence=["FLAURA trial", "NCCN Guidelines"],
            rationale="EGFR exon 19 deletion confirmed"
        ),
        alternative_options=[],
        summary="Osimertinib recommended based on EGFR mutation",
        discussion_points=["Side effects", "Clinical trials"]
    )


@pytest.fixture
def mock_clinical_trial():
    """Create a mock clinical trial for testing."""
    from models.treatment import EligibilityCriterion
    return ClinicalTrial(
        nct_id="NCT12345678",
        title="Test Clinical Trial",
        phase=TrialPhase.PHASE_3,
        status=TrialStatus.RECRUITING,
        brief_summary="A test clinical trial for EGFR-mutant NSCLC",
        sponsor="Test Sponsor",
        conditions=["NSCLC", "EGFR Mutation"],
        interventions=["Test Drug"],
        eligibility_criteria=[
            EligibilityCriterion(
                criterion="EGFR mutation positive",
                inclusion=True,
                patient_meets=True
            )
        ],
        locations=["Test Hospital"],
        match_score=0.90,
        match_rationale="Strong match based on mutation profile"
    )


@pytest.fixture
def mock_analysis_request():
    """Create a mock analysis request for testing."""
    return AnalysisRequest(
        patient_id="TEST001",
        analysis_type="full",
        include_trials=True,
        user_questions=[]
    )


@pytest.fixture
def mock_chat_message():
    """Create a mock chat message for testing."""
    from datetime import datetime
    return ChatMessage(
        id="MSG-001",
        patient_id="TEST001",
        timestamp=datetime.now(),
        role="patient",
        content="What are my treatment options?"
    )


@pytest.fixture
def patient_service():
    """Create a patient service for testing."""
    return PatientService()


@pytest.fixture
def llm_service_mock():
    """Create an LLM service in mock mode for testing."""
    return LLMService(use_mock=True)


@pytest.fixture
def llm_service_real():
    """Create an LLM service in real mode (requires API key)."""
    return LLMService(use_mock=False)


# Async fixtures
@pytest.fixture
def anyio_backend():
    """Backend for async tests."""
    return "asyncio"


# Mark async tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an async test"
    )
