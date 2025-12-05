"""Clinical Notes API Router - Track doctor updates and observations."""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from sqlalchemy import select, desc

from models.clinical_note import ClinicalNote, ClinicalNoteCreate, ClinicalNotesResponse
from models.db_models import ClinicalNoteDB, PatientDB
from database import async_session_maker

router = APIRouter()


def _db_to_model(note: ClinicalNoteDB) -> ClinicalNote:
    """Convert database model to Pydantic model."""
    return ClinicalNote(
        id=note.id,
        patient_id=note.patient_id,
        note_text=note.note_text,
        note_type=note.note_type,
        created_by=note.created_by,
        created_at=note.created_at
    )


@router.get("/patients/{patient_id}/clinical-notes", response_model=ClinicalNotesResponse)
async def get_clinical_notes(
    patient_id: str,
    note_type: Optional[str] = Query(None, description="Filter by note type"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all clinical notes for a patient.

    Args:
        patient_id: The patient ID
        note_type: Optional filter by note type
        limit: Maximum notes to return

    Returns:
        List of clinical notes ordered by created_at desc
    """
    try:
        async with async_session_maker() as db:
            # Verify patient exists
            result = await db.execute(
                select(PatientDB.id).where(PatientDB.id == patient_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            # Build query
            query = select(ClinicalNoteDB).where(
                ClinicalNoteDB.patient_id == patient_id
            )

            if note_type:
                query = query.where(ClinicalNoteDB.note_type == note_type)

            query = query.order_by(desc(ClinicalNoteDB.created_at)).limit(limit)

            result = await db.execute(query)
            notes = result.scalars().all()

            return ClinicalNotesResponse(
                notes=[_db_to_model(n) for n in notes],
                total=len(notes)
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patients/{patient_id}/clinical-notes", response_model=ClinicalNote)
async def create_clinical_note(patient_id: str, note_data: ClinicalNoteCreate):
    """Create a new clinical note for a patient.

    Args:
        patient_id: The patient ID
        note_data: Note details

    Returns:
        Created clinical note

    Raises:
        404: Patient not found
    """
    try:
        async with async_session_maker() as db:
            # Verify patient exists
            result = await db.execute(
                select(PatientDB.id).where(PatientDB.id == patient_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            note_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Create clinical note
            note = ClinicalNoteDB(
                id=note_id,
                patient_id=patient_id,
                note_text=note_data.note_text,
                note_type=note_data.note_type,
                created_by=note_data.created_by,
                created_at=now
            )
            db.add(note)
            await db.commit()
            await db.refresh(note)

            return _db_to_model(note)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clinical-notes/{note_id}", response_model=ClinicalNote)
async def get_clinical_note(note_id: str):
    """Get a specific clinical note.

    Args:
        note_id: The note ID

    Returns:
        Clinical note

    Raises:
        404: Note not found
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(ClinicalNoteDB).where(ClinicalNoteDB.id == note_id)
            )
            note = result.scalar_one_or_none()

            if not note:
                raise HTTPException(status_code=404, detail=f"Clinical note {note_id} not found")

            return _db_to_model(note)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/patients/{patient_id}/clinical-notes/{note_id}")
async def delete_clinical_note(patient_id: str, note_id: str):
    """Delete a clinical note.

    Args:
        patient_id: The patient ID
        note_id: The note ID

    Returns:
        Success message

    Raises:
        404: Note not found
    """
    try:
        async with async_session_maker() as db:
            # Find the note
            result = await db.execute(
                select(ClinicalNoteDB).where(
                    ClinicalNoteDB.id == note_id,
                    ClinicalNoteDB.patient_id == patient_id
                )
            )
            note = result.scalar_one_or_none()

            if not note:
                raise HTTPException(status_code=404, detail=f"Clinical note {note_id} not found")

            await db.delete(note)
            await db.commit()

            return {"message": "Clinical note deleted successfully", "id": note_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
