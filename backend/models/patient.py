"""Patient data models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date, datetime


class CancerType(str, Enum):
    """Types of cancer."""
    # Values match the keys used in JSON data
    NSCLC = "NSCLC"
    SCLC = "SCLC"
    BREAST = "Breast"
    COLORECTAL = "Colorectal"
    PANCREATIC = "Pancreatic"
    MELANOMA = "Melanoma"
    OTHER = "Other"


class CancerStage(str, Enum):
    """Cancer staging."""
    STAGE_I = "Stage I"
    STAGE_II = "Stage II"
    STAGE_IIIA = "Stage IIIA"
    STAGE_IIIB = "Stage IIIB"
    STAGE_IIIC = "Stage IIIC"
    STAGE_IV = "Stage IV"


class ECOGStatus(int, Enum):
    """ECOG Performance Status (0-5)."""
    FULLY_ACTIVE = 0
    RESTRICTED = 1
    AMBULATORY = 2
    LIMITED_SELF_CARE = 3
    DISABLED = 4
    DEAD = 5


class OrganFunction(BaseModel):
    """Organ function assessment."""
    organ: str
    status: str  # "normal", "mild_impairment", "moderate_impairment", "severe_impairment"
    key_values: dict = Field(default_factory=dict)
    notes: Optional[str] = None


class Comorbidity(BaseModel):
    """Patient comorbidity."""
    condition: str
    severity: str  # "mild", "moderate", "severe"
    treatment_implications: List[str] = Field(default_factory=list)


class CancerDetails(BaseModel):
    """Detailed cancer information."""
    cancer_type: CancerType
    subtype: Optional[str] = None  # e.g., "adenocarcinoma"
    stage: CancerStage
    tnm_staging: Optional[str] = None  # e.g., "T2N2M0"
    primary_site: str
    tumor_size_cm: Optional[float] = None
    metastases: List[str] = Field(default_factory=list)
    histology: Optional[str] = None
    grade: Optional[str] = None
    diagnosis_date: Optional[date] = None


class PatientSummary(BaseModel):
    """Summary of patient medical history."""
    demographics: dict
    cancer: Optional[CancerDetails] = None
    comorbidities: List[Comorbidity] = Field(default_factory=list)
    organ_function: List[OrganFunction] = Field(default_factory=list)
    ecog_status: Optional[ECOGStatus] = ECOGStatus.RESTRICTED  # Default to ECOG 1 if not specified
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    prior_treatments: List[str] = Field(default_factory=list)
    treatment_implications: List[str] = Field(default_factory=list)


class Patient(BaseModel):
    """Complete patient record."""
    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    email: Optional[str] = None
    phone: Optional[str] = None

    # Medical data
    cancer_details: Optional[CancerDetails] = None
    comorbidities: List[Comorbidity] = Field(default_factory=list)
    organ_function: List[OrganFunction] = Field(default_factory=list)
    ecog_status: Optional[ECOGStatus] = None
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)

    # Smoking history
    smoking_status: Optional[str] = None  # "never", "former", "current"
    pack_years: Optional[int] = None

    # Genomic data reference
    genomic_report_id: Optional[str] = None

    # Clinical notes (raw text)
    clinical_notes: List[str] = Field(default_factory=list)

    # Status fields
    status: Optional[str] = "active"
    closure_reason: Optional[str] = None
    closure_notes: Optional[str] = None
    closed_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


# ============= Patient Status & Closure Models =============

class PatientStatus(str, Enum):
    """Patient file status."""
    ACTIVE = "active"
    CLOSED = "closed"


class ClosureReason(str, Enum):
    """Reason for closing patient file."""
    DECEASED = "deceased"
    CURED = "cured"
    REMISSION = "remission"
    TRANSFERRED = "transferred"
    LOST_TO_FOLLOWUP = "lost_to_followup"
    PATIENT_CHOICE = "patient_choice"
    OTHER = "other"


class PatientClosure(BaseModel):
    """Patient file closure details."""
    reason: ClosureReason
    notes: Optional[str] = None


class PatientStatusUpdate(BaseModel):
    """Request to update patient status."""
    status: PatientStatus
    closure: Optional[PatientClosure] = None


# ============= Treatment Cycle Models =============

class TreatmentType(str, Enum):
    """Type of cancer treatment."""
    CHEMOTHERAPY = "chemotherapy"
    TARGETED = "targeted"
    IMMUNOTHERAPY = "immunotherapy"
    RADIATION = "radiation"
    SURGERY = "surgery"
    HORMONE = "hormone"
    OTHER = "other"


class TreatmentResponse(str, Enum):
    """RECIST treatment response criteria."""
    CR = "CR"  # Complete Response
    PR = "PR"  # Partial Response
    SD = "SD"  # Stable Disease
    PD = "PD"  # Progressive Disease


class TreatmentCycleStatus(str, Enum):
    """Treatment cycle status."""
    ONGOING = "ongoing"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"


class TreatmentCycleCreate(BaseModel):
    """Request to create a new treatment cycle."""
    treatment_name: str
    treatment_type: TreatmentType
    regimen: Optional[str] = None
    cycle_number: int = 1
    start_date: datetime
    dose: Optional[str] = None


class TreatmentCycleUpdate(BaseModel):
    """Request to update a treatment cycle."""
    end_date: Optional[datetime] = None
    dose_modification: Optional[str] = None
    response: Optional[TreatmentResponse] = None
    response_notes: Optional[str] = None
    side_effects: Optional[List[str]] = None
    status: Optional[TreatmentCycleStatus] = None
    discontinuation_reason: Optional[str] = None


class TreatmentCycle(BaseModel):
    """Full treatment cycle record."""
    id: str
    patient_id: str
    treatment_name: str
    treatment_type: str
    regimen: Optional[str] = None
    cycle_number: int
    start_date: datetime
    end_date: Optional[datetime] = None
    dose: Optional[str] = None
    dose_modification: Optional[str] = None
    response: Optional[str] = None
    response_notes: Optional[str] = None
    side_effects: List[str] = Field(default_factory=list)
    status: str
    discontinuation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Patient Event Models =============

class EventType(str, Enum):
    """Type of patient event."""
    ANALYSIS = "analysis"
    TREATMENT_START = "treatment_start"
    TREATMENT_END = "treatment_end"
    STATUS_CHANGE = "status_change"
    NOTE = "note"
    IMAGING = "imaging"
    LAB = "lab"


class PatientEventCreate(BaseModel):
    """Request to create a patient event."""
    event_type: EventType
    event_date: datetime
    title: str
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None


class PatientEvent(BaseModel):
    """Full patient event record."""
    id: str
    patient_id: str
    event_type: str
    event_date: datetime
    title: str
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Treatment Procedure Models =============

class ProcedureType(str, Enum):
    """Type of treatment procedure."""
    INFUSION = "infusion"
    LAB_CHECK = "lab_check"
    IMAGING = "imaging"
    INJECTION = "injection"
    ORAL_MEDICATION = "oral_medication"
    RADIATION_SESSION = "radiation_session"
    CONSULTATION = "consultation"
    OTHER = "other"


class ProcedureStatus(str, Enum):
    """Status of a treatment procedure."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class AdverseEvent(BaseModel):
    """Adverse event during procedure."""
    event: str
    grade: Optional[int] = None  # CTCAE grade 1-5
    notes: Optional[str] = None


class LabResult(BaseModel):
    """Single lab result."""
    value: float
    unit: str
    flag: Optional[str] = None  # "normal", "high", "low", "critical"


class ImagingResult(BaseModel):
    """Imaging result from a procedure."""
    modality: str  # CT, MRI, PET, X-ray, etc.
    findings: Optional[str] = None
    impression: Optional[str] = None


class TreatmentProcedureCreate(BaseModel):
    """Request to create a treatment procedure."""
    procedure_type: ProcedureType
    procedure_name: str
    day_number: int
    scheduled_date: datetime
    scheduled_time: Optional[str] = None  # e.g., "09:00"
    location: Optional[str] = None


class TreatmentProcedureUpdate(BaseModel):
    """Request to update a treatment procedure."""
    status: Optional[ProcedureStatus] = None
    actual_date: Optional[datetime] = None
    actual_dose: Optional[str] = None
    administered_by: Optional[str] = None
    administration_notes: Optional[str] = None
    adverse_events: Optional[List[AdverseEvent]] = None
    lab_results: Optional[dict] = None  # {test_name: LabResult}
    imaging_results: Optional[ImagingResult] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None


class TreatmentProcedure(BaseModel):
    """Full treatment procedure record."""
    id: str
    treatment_cycle_id: str
    patient_id: str
    procedure_type: str
    procedure_name: str
    day_number: int
    scheduled_date: datetime
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    status: str
    actual_date: Optional[datetime] = None
    actual_dose: Optional[str] = None
    administered_by: Optional[str] = None
    administration_notes: Optional[str] = None
    adverse_events: List[AdverseEvent] = Field(default_factory=list)
    lab_results: Optional[dict] = None
    imaging_results: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcedureComplete(BaseModel):
    """Request to mark a procedure as completed."""
    actual_date: Optional[datetime] = None
    actual_dose: Optional[str] = None
    administered_by: Optional[str] = None
    administration_notes: Optional[str] = None
    adverse_events: Optional[List[AdverseEvent]] = None
    lab_results: Optional[dict] = None
    imaging_results: Optional[ImagingResult] = None


class ProcedureCancel(BaseModel):
    """Request to cancel a procedure."""
    reason: Optional[str] = None


class GenerateProceduresRequest(BaseModel):
    """Request to generate procedures for a treatment cycle."""
    schedule_days: List[int]  # Days within cycle to schedule (e.g., [1, 8, 15])
    procedure_type: str = "infusion"
    start_time: Optional[str] = None  # e.g., "09:00"
    location: Optional[str] = None
