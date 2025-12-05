"""Treatment Cycles API Router - Track patient treatments and responses."""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy import select, desc

from models.patient import (
    TreatmentCycle, TreatmentCycleCreate, TreatmentCycleUpdate,
    TreatmentCycleStatus, PatientEvent
)
from models.db_models import TreatmentCycleDB, PatientEventDB, PatientDB
from database import async_session_maker

router = APIRouter()


@router.post("/treatment-cycles/patients/{patient_id}", response_model=TreatmentCycle)
async def create_treatment_cycle(patient_id: str, cycle_data: TreatmentCycleCreate):
    """Start a new treatment cycle for a patient.

    Args:
        patient_id: The patient ID
        cycle_data: Treatment cycle details

    Returns:
        Created treatment cycle

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

            cycle_id = str(uuid.uuid4())
            now = datetime.now()

            # Create treatment cycle
            cycle = TreatmentCycleDB(
                id=cycle_id,
                patient_id=patient_id,
                treatment_name=cycle_data.treatment_name,
                treatment_type=cycle_data.treatment_type.value,
                regimen=cycle_data.regimen,
                cycle_number=cycle_data.cycle_number,
                start_date=cycle_data.start_date,
                dose=cycle_data.dose,
                status="ongoing",
                created_at=now,
                updated_at=now
            )
            db.add(cycle)

            # Create patient event
            event = PatientEventDB(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                event_type="treatment_start",
                event_date=cycle_data.start_date,
                title=f"Started {cycle_data.treatment_name} - Cycle {cycle_data.cycle_number}",
                description=f"Treatment type: {cycle_data.treatment_type.value}. Regimen: {cycle_data.regimen or 'N/A'}. Dose: {cycle_data.dose or 'N/A'}",
                reference_type="treatment_cycle",
                reference_id=cycle_id,
                created_at=now
            )
            db.add(event)

            await db.commit()
            await db.refresh(cycle)

            return TreatmentCycle(
                id=cycle.id,
                patient_id=cycle.patient_id,
                treatment_name=cycle.treatment_name,
                treatment_type=cycle.treatment_type,
                regimen=cycle.regimen,
                cycle_number=cycle.cycle_number,
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                dose=cycle.dose,
                dose_modification=cycle.dose_modification,
                response=cycle.response,
                response_notes=cycle.response_notes,
                side_effects=cycle.side_effects or [],
                status=cycle.status,
                discontinuation_reason=cycle.discontinuation_reason,
                created_at=cycle.created_at,
                updated_at=cycle.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treatment-cycles/patients/{patient_id}", response_model=List[TreatmentCycle])
async def get_treatment_cycles(
    patient_id: str,
    status: Optional[str] = Query(None, description="Filter by status: ongoing, completed, discontinued"),
    limit: int = Query(50, ge=1, le=200, description="Maximum cycles to return")
):
    """Get all treatment cycles for a patient.

    Args:
        patient_id: The patient ID
        status: Optional status filter
        limit: Maximum cycles to return

    Returns:
        List of treatment cycles

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

            # Build query
            query = select(TreatmentCycleDB).where(TreatmentCycleDB.patient_id == patient_id)

            if status:
                query = query.where(TreatmentCycleDB.status == status)

            query = query.order_by(desc(TreatmentCycleDB.start_date)).limit(limit)

            result = await db.execute(query)
            cycles = result.scalars().all()

            return [
                TreatmentCycle(
                    id=c.id,
                    patient_id=c.patient_id,
                    treatment_name=c.treatment_name,
                    treatment_type=c.treatment_type,
                    regimen=c.regimen,
                    cycle_number=c.cycle_number,
                    start_date=c.start_date,
                    end_date=c.end_date,
                    dose=c.dose,
                    dose_modification=c.dose_modification,
                    response=c.response,
                    response_notes=c.response_notes,
                    side_effects=c.side_effects or [],
                    status=c.status,
                    discontinuation_reason=c.discontinuation_reason,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in cycles
            ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treatment-cycles/{cycle_id}", response_model=TreatmentCycle)
async def get_treatment_cycle(cycle_id: str):
    """Get a specific treatment cycle.

    Args:
        cycle_id: The treatment cycle ID

    Returns:
        Treatment cycle details

    Raises:
        404: Treatment cycle not found
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentCycleDB).where(TreatmentCycleDB.id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            return TreatmentCycle(
                id=cycle.id,
                patient_id=cycle.patient_id,
                treatment_name=cycle.treatment_name,
                treatment_type=cycle.treatment_type,
                regimen=cycle.regimen,
                cycle_number=cycle.cycle_number,
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                dose=cycle.dose,
                dose_modification=cycle.dose_modification,
                response=cycle.response,
                response_notes=cycle.response_notes,
                side_effects=cycle.side_effects or [],
                status=cycle.status,
                discontinuation_reason=cycle.discontinuation_reason,
                created_at=cycle.created_at,
                updated_at=cycle.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/treatment-cycles/{cycle_id}", response_model=TreatmentCycle)
async def update_treatment_cycle(cycle_id: str, update_data: TreatmentCycleUpdate):
    """Update a treatment cycle (add response, end, modify dose, etc.).

    Args:
        cycle_id: The treatment cycle ID
        update_data: Fields to update

    Returns:
        Updated treatment cycle

    Raises:
        404: Treatment cycle not found
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentCycleDB).where(TreatmentCycleDB.id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            now = datetime.now()

            # Update fields
            if update_data.end_date is not None:
                cycle.end_date = update_data.end_date
            if update_data.dose_modification is not None:
                cycle.dose_modification = update_data.dose_modification
            if update_data.response is not None:
                cycle.response = update_data.response.value
            if update_data.response_notes is not None:
                cycle.response_notes = update_data.response_notes
            if update_data.side_effects is not None:
                cycle.side_effects = update_data.side_effects
            if update_data.status is not None:
                cycle.status = update_data.status.value
            if update_data.discontinuation_reason is not None:
                cycle.discontinuation_reason = update_data.discontinuation_reason

            cycle.updated_at = now

            # Create event if treatment ended or discontinued
            if update_data.status in [TreatmentCycleStatus.COMPLETED, TreatmentCycleStatus.DISCONTINUED]:
                status_text = "completed" if update_data.status == TreatmentCycleStatus.COMPLETED else "discontinued"
                response_text = f", Response: {cycle.response}" if cycle.response else ""
                reason_text = f" - {update_data.discontinuation_reason}" if update_data.discontinuation_reason else ""

                event = PatientEventDB(
                    id=str(uuid.uuid4()),
                    patient_id=cycle.patient_id,
                    event_type="treatment_end",
                    event_date=update_data.end_date or now,
                    title=f"Ended {cycle.treatment_name} - Cycle {cycle.cycle_number} ({status_text}){reason_text}",
                    description=f"Treatment {status_text}{response_text}. {cycle.response_notes or ''}".strip(),
                    reference_type="treatment_cycle",
                    reference_id=cycle_id,
                    created_at=now
                )
                db.add(event)

            await db.commit()
            await db.refresh(cycle)

            return TreatmentCycle(
                id=cycle.id,
                patient_id=cycle.patient_id,
                treatment_name=cycle.treatment_name,
                treatment_type=cycle.treatment_type,
                regimen=cycle.regimen,
                cycle_number=cycle.cycle_number,
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                dose=cycle.dose,
                dose_modification=cycle.dose_modification,
                response=cycle.response,
                response_notes=cycle.response_notes,
                side_effects=cycle.side_effects or [],
                status=cycle.status,
                discontinuation_reason=cycle.discontinuation_reason,
                created_at=cycle.created_at,
                updated_at=cycle.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/treatment-cycles/{cycle_id}", status_code=204)
async def delete_treatment_cycle(cycle_id: str):
    """Delete a treatment cycle.

    Args:
        cycle_id: The treatment cycle ID

    Raises:
        404: Treatment cycle not found
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentCycleDB).where(TreatmentCycleDB.id == cycle_id)
            )
            cycle = result.scalar_one_or_none()

            if not cycle:
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            await db.delete(cycle)
            await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
