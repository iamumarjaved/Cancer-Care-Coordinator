"""Pydantic models for Clinical Notes."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClinicalNoteBase(BaseModel):
    """Base clinical note model."""
    note_text: str
    note_type: str = "general"  # general, lab_result, imaging, treatment_response, side_effect
    created_by: Optional[str] = None


class ClinicalNoteCreate(ClinicalNoteBase):
    """Clinical note creation model."""
    pass


class ClinicalNote(ClinicalNoteBase):
    """Clinical note response model."""
    id: str
    patient_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClinicalNotesResponse(BaseModel):
    """Response model for list of clinical notes."""
    notes: list[ClinicalNote]
    total: int
