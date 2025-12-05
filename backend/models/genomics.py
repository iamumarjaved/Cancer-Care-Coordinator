"""Genomics data models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MutationClassification(str, Enum):
    """Mutation pathogenicity classification."""
    PATHOGENIC_ACTIONABLE = "pathogenic_actionable"
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class Therapy(BaseModel):
    """Targeted therapy for a mutation."""
    drug_name: Optional[str] = None
    drug: Optional[str] = None  # Alias for drug_name
    brand_name: Optional[str] = None
    fda_approved: bool = True
    expected_response_rate: Optional[float] = None
    response_rate: Optional[float] = None  # Alias
    evidence_level: Optional[str] = None
    indication: Optional[str] = None
    notes: Optional[str] = None

    def __init__(self, **data):
        # Allow 'drug' as alias for 'drug_name'
        if 'drug' in data and 'drug_name' not in data:
            data['drug_name'] = data['drug']
        if 'response_rate' in data and 'expected_response_rate' not in data:
            data['expected_response_rate'] = data['response_rate']
        super().__init__(**data)


class Mutation(BaseModel):
    """Genetic mutation found in tumor."""
    gene: Optional[str] = "Unknown"
    variant: Optional[str] = "Unknown"  # e.g., "exon19del", "L858R", "T790M"
    variant_detail: Optional[str] = None  # e.g., "p.E746_A750del"
    classification: Optional[MutationClassification] = MutationClassification.UNCERTAIN
    allele_frequency: Optional[float] = None
    tier: Optional[str] = None  # "Tier I", "Tier II", "Tier III", "Tier IV"
    therapies: List[Therapy] = Field(default_factory=list)
    preferred_therapy: Optional[str] = None
    resistance_to: List[str] = Field(default_factory=list)
    prognostic_impact: Optional[str] = None  # "favorable", "unfavorable", "neutral"


class ImmunotherapyMarkers(BaseModel):
    """Markers that predict immunotherapy response."""
    pdl1_expression: Optional[float] = None  # Percentage (0-100)
    pdl1_interpretation: Optional[str] = None  # "high", "moderate", "low", "negative"
    pdl1_method: Optional[str] = None  # e.g., "22C3 pharmDx"
    tmb: Optional[float] = None  # Tumor Mutational Burden (mut/Mb)
    tmb_interpretation: Optional[str] = None  # "high", "intermediate", "low"
    tmb_unit: Optional[str] = None  # e.g., "mutations/Mb"
    msi_status: Optional[str] = None  # "MSI-H", "MSI-L", "MSS"
    immunotherapy_likely_benefit: bool = False
    reasoning: Optional[str] = None


class GenomicReport(BaseModel):
    """Complete genomic analysis report."""
    report_id: Optional[str] = None
    id: Optional[str] = None  # Alias for report_id
    patient_id: Optional[str] = "unknown"
    test_date: Optional[str] = "Unknown"
    test_type: Optional[str] = "NGS Panel"  # "NGS Panel", "Whole Exome", "RNA-seq"
    lab_name: Optional[str] = None
    specimen_type: Optional[str] = "Tumor tissue"  # "Tumor tissue", "Liquid biopsy"

    # Findings - support both 'mutations' and 'actionable_mutations'
    mutations: List[Mutation] = Field(default_factory=list)
    actionable_mutations: List[Mutation] = Field(default_factory=list)
    other_mutations: List[Mutation] = Field(default_factory=list)
    immunotherapy_markers: Optional[ImmunotherapyMarkers] = None

    # Summary
    summary: Optional[str] = None
    primary_recommendation: Optional[str] = None
    confidence_level: Optional[str] = None  # "high", "moderate", "low"

    # Raw data reference
    raw_report_url: Optional[str] = None

    def __init__(self, **data):
        # Allow 'id' as alias for 'report_id'
        if 'id' in data and 'report_id' not in data:
            data['report_id'] = data['id']
        # If mutations provided, also populate actionable_mutations
        if 'mutations' in data and not data.get('actionable_mutations'):
            data['actionable_mutations'] = data['mutations']
        super().__init__(**data)


class GenomicAnalysisResult(BaseModel):
    """Output from Genomics Analysis Agent."""
    patient_id: Optional[str] = "unknown"
    report: Optional[GenomicReport] = None
    summary: Optional[str] = "No genomic summary available"
    targeted_therapy_candidates: List[str] = Field(default_factory=list)
    immunotherapy_candidate: bool = False
    key_findings: List[str] = Field(default_factory=list)
    treatment_implications: List[str] = Field(default_factory=list)
