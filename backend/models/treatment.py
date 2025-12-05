"""Treatment and clinical trial models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class RecommendationLevel(str, Enum):
    """Treatment recommendation strength."""
    STRONGLY_RECOMMENDED = "strongly_recommended"
    RECOMMENDED = "recommended"
    CONSIDER = "consider"
    NOT_RECOMMENDED = "not_recommended"
    CONTRAINDICATED = "contraindicated"


class EvidenceLevel(str, Enum):
    """Evidence strength level."""
    LEVEL_1 = "Level 1 - High-quality evidence"
    LEVEL_2 = "Level 2 - Moderate evidence"
    LEVEL_3 = "Level 3 - Low-level evidence"
    CATEGORY_1 = "Category 1 - High-level evidence, uniform consensus"
    CATEGORY_2A = "Category 2A - Lower-level evidence, uniform consensus"
    CATEGORY_2B = "Category 2B - Lower-level evidence, non-uniform consensus"
    CATEGORY_3 = "Category 3 - Any level evidence, major disagreement"


class TreatmentOption(BaseModel):
    """A treatment option with reasoning."""
    id: Optional[str] = None
    rank: int = 1
    treatment_name: Optional[str] = None
    name: Optional[str] = None  # Alias for treatment_name
    treatment_type: Optional[str] = None  # "targeted_therapy", "chemotherapy", "immunotherapy", "surgery", "radiation"
    category: Optional[str] = None  # Alias for treatment_type
    drugs: List[str] = Field(default_factory=list)
    dosing: Optional[str] = None
    schedule: Optional[str] = None
    description: Optional[str] = None

    # Recommendation - support both field names
    recommendation: Optional[RecommendationLevel] = None
    recommendation_level: Optional[RecommendationLevel] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)

    # Expected outcomes - support both dict and individual fields
    expected_outcomes: Optional[dict] = None
    expected_response_rate: Optional[float] = None
    expected_pfs_months: Optional[float] = None  # Progression-free survival
    expected_os_months: Optional[float] = None  # Overall survival

    # Reasoning
    rationale: Optional[str] = None
    why_recommended: List[str] = Field(default_factory=list)
    why_not_recommended: List[str] = Field(default_factory=list)
    considerations: List[str] = Field(default_factory=list)

    # Evidence
    evidence_level: Optional[EvidenceLevel] = None
    key_trials: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)  # Alias for key_trials
    guideline_references: List[str] = Field(default_factory=list)

    # Side effects
    common_side_effects: List[str] = Field(default_factory=list)
    serious_side_effects: List[str] = Field(default_factory=list)

    # Patient-specific adjustments
    dose_adjustments: List[str] = Field(default_factory=list)
    monitoring_required: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        # Handle aliases
        if 'name' in data and 'treatment_name' not in data:
            data['treatment_name'] = data['name']
        if 'category' in data and 'treatment_type' not in data:
            data['treatment_type'] = data['category']
        if 'recommendation_level' in data and 'recommendation' not in data:
            data['recommendation'] = data['recommendation_level']
        if 'confidence_score' in data and 'confidence' not in data:
            data['confidence'] = data['confidence_score']
        if 'supporting_evidence' in data and not data.get('key_trials'):
            data['key_trials'] = data['supporting_evidence']
        super().__init__(**data)


class ClinicalTrialPhase(str, Enum):
    """Clinical trial phases."""
    PHASE_1 = "Phase I"
    PHASE_1_2 = "Phase I/II"
    PHASE_2 = "Phase II"
    PHASE_2_3 = "Phase II/III"
    PHASE_3 = "Phase III"
    PHASE_4 = "Phase IV"
    NOT_APPLICABLE = "N/A"
    EARLY_PHASE_1 = "Early Phase 1"


# Alias for backward compatibility
TrialPhase = ClinicalTrialPhase


class TrialStatus(str, Enum):
    """Clinical trial status."""
    RECRUITING = "Recruiting"
    ACTIVE = "Active, not recruiting"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"
    NOT_YET_RECRUITING = "Not yet recruiting"
    WITHDRAWN = "Withdrawn"
    UNKNOWN = "Unknown"
    ENROLLING_BY_INVITATION = "Enrolling by invitation"
    AVAILABLE = "Available"


class EligibilityCriterion(BaseModel):
    """Single eligibility criterion."""
    criterion: Optional[str] = "Unspecified criterion"
    inclusion: bool = True  # Whether this is inclusion (True) or exclusion (False) criterion
    patient_meets: Optional[bool] = None  # Whether patient meets this criterion
    details: Optional[str] = None


class ClinicalTrial(BaseModel):
    """Clinical trial match."""
    nct_id: Optional[str] = "Unknown"
    title: Optional[str] = "Unknown Trial"
    phase: Optional[ClinicalTrialPhase] = ClinicalTrialPhase.NOT_APPLICABLE
    status: Optional[TrialStatus] = TrialStatus.UNKNOWN
    sponsor: Optional[str] = None

    # Treatment info
    intervention: Optional[str] = None
    intervention_type: Optional[str] = None  # "Drug", "Combination", "Device"
    interventions: List[str] = Field(default_factory=list)  # List of interventions
    description: Optional[str] = None
    brief_summary: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)

    # Location
    locations: List[str] = Field(default_factory=list)
    nearest_location: Optional[str] = None
    distance_miles: Optional[float] = None

    # Eligibility
    match_score: float = Field(ge=0, le=1, default=0.0)
    eligibility_criteria: List[EligibilityCriterion] = Field(default_factory=list)
    meets_criteria_count: int = 0
    does_not_meet_count: int = 0
    unknown_count: int = 0

    # Why consider
    rationale: Optional[str] = None
    match_rationale: Optional[str] = None  # Alias for rationale
    potential_benefits: List[str] = Field(default_factory=list)
    potential_drawbacks: List[str] = Field(default_factory=list)

    # Contact
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class TreatmentPlan(BaseModel):
    """Complete treatment plan output."""
    id: Optional[str] = None
    patient_id: Optional[str] = "unknown"
    generated_at: Optional[str] = None  # Can be str or datetime
    status: Optional[str] = None  # "pending_review", "approved", "rejected"

    # Treatment options - support both structures
    primary_recommendation: Optional[TreatmentOption] = None
    treatment_options: List[TreatmentOption] = Field(default_factory=list)
    alternative_options: List[TreatmentOption] = Field(default_factory=list)

    clinical_trials: List[ClinicalTrial] = Field(default_factory=list)
    discussion_points: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    def __init__(self, **data):
        # Handle datetime for generated_at
        if 'generated_at' in data:
            from datetime import datetime
            if isinstance(data['generated_at'], datetime):
                data['generated_at'] = data['generated_at'].isoformat()
        super().__init__(**data)


class EvidenceSummary(BaseModel):
    """Summary of evidence for a treatment."""
    treatment: Optional[str] = "Unknown treatment"
    key_trials: List[dict] = Field(default_factory=list)
    guideline_recommendations: List[dict] = Field(default_factory=list)
    guideline_recommendation: Optional[str] = None  # Single string version
    meta_analyses: List[dict] = Field(default_factory=list)
    recent_updates: List[str] = Field(default_factory=list)
    evidence_strength: Optional[str] = "Category 2A - Lower-level evidence, uniform consensus"
    applicability_to_patient: Optional[str] = "Requires clinical evaluation"
    summary: Optional[str] = "No summary available"
