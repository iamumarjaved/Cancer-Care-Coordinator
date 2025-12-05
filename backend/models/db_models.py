"""SQLAlchemy ORM models for database persistence."""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class CancerTypeEnum(str, enum.Enum):
    """Cancer types."""
    NSCLC = "NSCLC"
    SCLC = "SCLC"
    BREAST = "Breast"
    COLORECTAL = "Colorectal"
    PANCREATIC = "Pancreatic"
    MELANOMA = "Melanoma"
    OTHER = "Other"


class CancerStageEnum(str, enum.Enum):
    """Cancer stages."""
    STAGE_I = "Stage I"
    STAGE_II = "Stage II"
    STAGE_IIIA = "Stage IIIA"
    STAGE_IIIB = "Stage IIIB"
    STAGE_IIIC = "Stage IIIC"
    STAGE_IV = "Stage IV"


class PatientDB(Base):
    """Patient database model."""
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String(20), nullable=False)  # ISO format date
    sex = Column(String(20), default="Unknown")
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)

    # Cancer details (stored as JSON for flexibility)
    cancer_details = Column(JSON, nullable=True)

    # Medical data (stored as JSON)
    comorbidities = Column(JSON, default=list)
    organ_function = Column(JSON, default=list)
    ecog_status = Column(Integer, nullable=True)
    current_medications = Column(JSON, default=list)
    allergies = Column(JSON, default=list)

    # Smoking history
    smoking_status = Column(String(50), nullable=True)
    pack_years = Column(Integer, nullable=True)

    # Genomic data
    genomic_report_id = Column(String(100), nullable=True)

    # Clinical notes
    clinical_notes = Column(JSON, default=list)

    # Patient status and closure
    status = Column(String(20), default="active")  # "active" or "closed"
    closure_reason = Column(String(100), nullable=True)  # deceased, cured, remission, transferred, etc.
    closure_notes = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_messages = relationship("ChatMessageDB", back_populates="patient", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResultDB", back_populates="patient", cascade="all, delete-orphan")
    treatment_cycles = relationship("TreatmentCycleDB", back_populates="patient", cascade="all, delete-orphan")
    treatment_procedures = relationship("TreatmentProcedureDB", back_populates="patient", cascade="all, delete-orphan")
    events = relationship("PatientEventDB", back_populates="patient", cascade="all, delete-orphan")
    clinical_notes_records = relationship("ClinicalNoteDB", back_populates="patient", cascade="all, delete-orphan")


class ChatMessageDB(Base):
    """Chat message database model."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    escalate_to_human = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    suggested_followup = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("PatientDB", back_populates="chat_messages")


class AnalysisResultDB(Base):
    """Analysis result database model."""
    __tablename__ = "analysis_results"

    id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # "comprehensive", "genomics", "trials", etc.
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed

    # Results stored as JSON
    result_data = Column(JSON, nullable=True)
    sources_used = Column(JSON, default=list)

    # Metadata
    confidence_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("PatientDB", back_populates="analysis_results")


class DocumentDB(Base):
    """Document metadata for RAG system."""
    __tablename__ = "documents"

    id = Column(String(100), primary_key=True)
    namespace = Column(String(50), nullable=False)  # "nccn", "pubmed", "trials", "oncokb"
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)

    # Document metadata (renamed from 'metadata' which is reserved)
    doc_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TreatmentCycleDB(Base):
    """Treatment cycle tracking for longitudinal patient care."""
    __tablename__ = "treatment_cycles"

    id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)

    # Treatment details
    treatment_name = Column(String(200), nullable=False)  # e.g., "Osimertinib", "Carboplatin + Pemetrexed"
    treatment_type = Column(String(50), nullable=False)  # chemotherapy, targeted, immunotherapy, radiation, surgery
    regimen = Column(String(200), nullable=True)  # e.g., "Cisplatin + Pemetrexed q3w"

    # Cycle tracking
    cycle_number = Column(Integer, default=1)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # Dosing
    dose = Column(String(100), nullable=True)  # e.g., "80mg daily", "175mg/m2"
    dose_modification = Column(String(200), nullable=True)  # e.g., "Reduced to 60mg due to rash"

    # Response tracking (RECIST criteria)
    response = Column(String(50), nullable=True)  # CR, PR, SD, PD (Complete Response, Partial Response, Stable Disease, Progressive Disease)
    response_notes = Column(Text, nullable=True)  # Clinical assessment notes

    # Side effects
    side_effects = Column(JSON, default=list)  # List of side effects with grade

    # Status
    status = Column(String(20), default="ongoing")  # ongoing, completed, discontinued
    discontinuation_reason = Column(String(200), nullable=True)  # toxicity, progression, patient choice, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("PatientDB", back_populates="treatment_cycles")
    procedures = relationship("TreatmentProcedureDB", back_populates="treatment_cycle", cascade="all, delete-orphan")


class TreatmentProcedureDB(Base):
    """Daily treatment procedure tracking within a treatment cycle."""
    __tablename__ = "treatment_procedures"

    id = Column(String(50), primary_key=True)
    treatment_cycle_id = Column(String(50), ForeignKey("treatment_cycles.id"), nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)

    # Procedure details
    procedure_type = Column(String(50), nullable=False)  # infusion, lab_check, imaging, injection, etc.
    procedure_name = Column(String(200), nullable=False)  # e.g., "Day 1 Infusion", "Day 8 Lab Check"
    day_number = Column(Integer, nullable=False)  # Day within cycle (1, 8, 15, etc.)

    # Scheduling
    scheduled_date = Column(DateTime, nullable=False)
    scheduled_time = Column(String(10), nullable=True)  # e.g., "09:00"
    location = Column(String(200), nullable=True)  # e.g., "Infusion Center Room 3"

    # Status tracking
    status = Column(String(20), default="scheduled")  # scheduled, completed, missed, cancelled
    actual_date = Column(DateTime, nullable=True)  # When actually performed

    # Administration details (when completed)
    actual_dose = Column(String(100), nullable=True)  # e.g., "75mg" (may differ from planned)
    administered_by = Column(String(100), nullable=True)
    administration_notes = Column(Text, nullable=True)

    # Results
    adverse_events = Column(JSON, default=list)  # List of {event, grade, notes}
    lab_results = Column(JSON, nullable=True)  # {test_name: {value, unit, flag}}
    imaging_results = Column(JSON, nullable=True)  # {modality, findings, impression}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    treatment_cycle = relationship("TreatmentCycleDB", back_populates="procedures")
    patient = relationship("PatientDB", back_populates="treatment_procedures")


class PatientEventDB(Base):
    """Patient event timeline for longitudinal tracking."""
    __tablename__ = "patient_events"

    id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)  # analysis, treatment_start, treatment_end, status_change, note, imaging, lab
    event_date = Column(DateTime, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Reference to related records
    reference_type = Column(String(50), nullable=True)  # analysis, treatment_cycle
    reference_id = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("PatientDB", back_populates="events")


class ClinicalNoteDB(Base):
    """Clinical notes for longitudinal patient updates."""
    __tablename__ = "clinical_notes"

    id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.id"), nullable=False)

    # Note content
    note_text = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, lab_result, imaging, treatment_response, side_effect

    # Metadata
    created_by = Column(String(100), nullable=True)  # Doctor name or ID

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    patient = relationship("PatientDB", back_populates="clinical_notes_records")
