"""Treatment Procedures API Router - Track daily procedures within treatment cycles."""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from sqlalchemy import select, desc, and_

from models.patient import (
    TreatmentProcedure, TreatmentProcedureCreate, TreatmentProcedureUpdate,
    ProcedureStatus, ProcedureComplete, ProcedureCancel, PatientEvent,
    GenerateProceduresRequest
)
from models.db_models import TreatmentProcedureDB, TreatmentCycleDB, PatientDB, PatientEventDB
from database import async_session_maker

router = APIRouter()


def _db_to_model(proc: TreatmentProcedureDB) -> TreatmentProcedure:
    """Convert database model to Pydantic model."""
    return TreatmentProcedure(
        id=proc.id,
        treatment_cycle_id=proc.treatment_cycle_id,
        patient_id=proc.patient_id,
        procedure_type=proc.procedure_type,
        procedure_name=proc.procedure_name,
        day_number=proc.day_number,
        scheduled_date=proc.scheduled_date,
        scheduled_time=proc.scheduled_time,
        location=proc.location,
        status=proc.status,
        actual_date=proc.actual_date,
        actual_dose=proc.actual_dose,
        administered_by=proc.administered_by,
        administration_notes=proc.administration_notes,
        adverse_events=proc.adverse_events or [],
        lab_results=proc.lab_results,
        imaging_results=proc.imaging_results,
        created_at=proc.created_at,
        updated_at=proc.updated_at
    )


@router.post("/treatment-cycles/{cycle_id}/procedures", response_model=TreatmentProcedure)
async def create_procedure(cycle_id: str, procedure_data: TreatmentProcedureCreate):
    """Create a new procedure within a treatment cycle.

    Args:
        cycle_id: The treatment cycle ID
        procedure_data: Procedure details

    Returns:
        Created procedure

    Raises:
        404: Treatment cycle not found
    """
    try:
        async with async_session_maker() as db:
            # Verify cycle exists and get patient_id
            result = await db.execute(
                select(TreatmentCycleDB).where(TreatmentCycleDB.id == cycle_id)
            )
            cycle = result.scalar_one_or_none()
            if not cycle:
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            procedure_id = str(uuid.uuid4())
            now = datetime.now()

            # Create procedure
            procedure = TreatmentProcedureDB(
                id=procedure_id,
                treatment_cycle_id=cycle_id,
                patient_id=cycle.patient_id,
                procedure_type=procedure_data.procedure_type.value,
                procedure_name=procedure_data.procedure_name,
                day_number=procedure_data.day_number,
                scheduled_date=procedure_data.scheduled_date,
                scheduled_time=procedure_data.scheduled_time,
                location=procedure_data.location,
                status="scheduled",
                created_at=now,
                updated_at=now
            )
            db.add(procedure)
            await db.commit()
            await db.refresh(procedure)

            return _db_to_model(procedure)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treatment-cycles/{cycle_id}/procedures", response_model=List[TreatmentProcedure])
async def get_cycle_procedures(
    cycle_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all procedures for a treatment cycle.

    Args:
        cycle_id: The treatment cycle ID
        status: Optional status filter
        limit: Maximum procedures to return

    Returns:
        List of procedures
    """
    try:
        async with async_session_maker() as db:
            # Verify cycle exists
            result = await db.execute(
                select(TreatmentCycleDB.id).where(TreatmentCycleDB.id == cycle_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            # Build query
            query = select(TreatmentProcedureDB).where(
                TreatmentProcedureDB.treatment_cycle_id == cycle_id
            )

            if status:
                query = query.where(TreatmentProcedureDB.status == status)

            query = query.order_by(TreatmentProcedureDB.day_number).limit(limit)

            result = await db.execute(query)
            procedures = result.scalars().all()

            return [_db_to_model(p) for p in procedures]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/procedures/{procedure_id}", response_model=TreatmentProcedure)
async def get_procedure(procedure_id: str):
    """Get a specific procedure.

    Args:
        procedure_id: The procedure ID

    Returns:
        Procedure details
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentProcedureDB).where(TreatmentProcedureDB.id == procedure_id)
            )
            procedure = result.scalar_one_or_none()

            if not procedure:
                raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")

            return _db_to_model(procedure)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/procedures/{procedure_id}", response_model=TreatmentProcedure)
async def update_procedure(procedure_id: str, update_data: TreatmentProcedureUpdate):
    """Update a procedure.

    Args:
        procedure_id: The procedure ID
        update_data: Fields to update

    Returns:
        Updated procedure
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentProcedureDB).where(TreatmentProcedureDB.id == procedure_id)
            )
            procedure = result.scalar_one_or_none()

            if not procedure:
                raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")

            now = datetime.now()

            # Update fields
            if update_data.status is not None:
                procedure.status = update_data.status.value
            if update_data.actual_date is not None:
                procedure.actual_date = update_data.actual_date
            if update_data.actual_dose is not None:
                procedure.actual_dose = update_data.actual_dose
            if update_data.administered_by is not None:
                procedure.administered_by = update_data.administered_by
            if update_data.administration_notes is not None:
                procedure.administration_notes = update_data.administration_notes
            if update_data.adverse_events is not None:
                procedure.adverse_events = [ae.model_dump() for ae in update_data.adverse_events]
            if update_data.lab_results is not None:
                procedure.lab_results = update_data.lab_results
            if update_data.imaging_results is not None:
                procedure.imaging_results = update_data.imaging_results.model_dump() if update_data.imaging_results else None
            if update_data.scheduled_time is not None:
                procedure.scheduled_time = update_data.scheduled_time
            if update_data.location is not None:
                procedure.location = update_data.location

            procedure.updated_at = now

            await db.commit()
            await db.refresh(procedure)

            return _db_to_model(procedure)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/procedures/{procedure_id}", status_code=204)
async def delete_procedure(procedure_id: str):
    """Delete a procedure.

    Args:
        procedure_id: The procedure ID
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentProcedureDB).where(TreatmentProcedureDB.id == procedure_id)
            )
            procedure = result.scalar_one_or_none()

            if not procedure:
                raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")

            await db.delete(procedure)
            await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/procedures", response_model=List[TreatmentProcedure])
async def get_patient_procedures(
    patient_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    procedure_type: Optional[str] = Query(None, description="Filter by procedure type"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all procedures for a patient across all cycles.

    Args:
        patient_id: The patient ID
        status: Optional status filter
        procedure_type: Optional procedure type filter
        limit: Maximum procedures to return

    Returns:
        List of procedures
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
            query = select(TreatmentProcedureDB).where(
                TreatmentProcedureDB.patient_id == patient_id
            )

            if status:
                query = query.where(TreatmentProcedureDB.status == status)
            if procedure_type:
                query = query.where(TreatmentProcedureDB.procedure_type == procedure_type)

            query = query.order_by(desc(TreatmentProcedureDB.scheduled_date)).limit(limit)

            result = await db.execute(query)
            procedures = result.scalars().all()

            return [_db_to_model(p) for p in procedures]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/procedures/upcoming", response_model=List[TreatmentProcedure])
async def get_upcoming_procedures(
    patient_id: str,
    days_ahead: int = Query(14, ge=1, le=90, description="Days to look ahead")
):
    """Get upcoming scheduled procedures for a patient.

    Args:
        patient_id: The patient ID
        days_ahead: Number of days to look ahead

    Returns:
        List of upcoming procedures
    """
    try:
        async with async_session_maker() as db:
            # Verify patient exists
            result = await db.execute(
                select(PatientDB.id).where(PatientDB.id == patient_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)

            query = select(TreatmentProcedureDB).where(
                and_(
                    TreatmentProcedureDB.patient_id == patient_id,
                    TreatmentProcedureDB.status == "scheduled",
                    TreatmentProcedureDB.scheduled_date >= now,
                    TreatmentProcedureDB.scheduled_date <= end_date
                )
            ).order_by(TreatmentProcedureDB.scheduled_date)

            result = await db.execute(query)
            procedures = result.scalars().all()

            return [_db_to_model(p) for p in procedures]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/procedures/calendar", response_model=Dict[str, List[TreatmentProcedure]])
async def get_patient_calendar(
    patient_id: str,
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2020, le=2100, description="Year")
):
    """Get procedures organized by date for calendar view.

    Args:
        patient_id: The patient ID
        month: Month (1-12)
        year: Year

    Returns:
        Dict mapping date strings (YYYY-MM-DD) to procedures
    """
    try:
        async with async_session_maker() as db:
            # Verify patient exists
            result = await db.execute(
                select(PatientDB.id).where(PatientDB.id == patient_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            # Calculate date range for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            query = select(TreatmentProcedureDB).where(
                and_(
                    TreatmentProcedureDB.patient_id == patient_id,
                    TreatmentProcedureDB.scheduled_date >= start_date,
                    TreatmentProcedureDB.scheduled_date < end_date
                )
            ).order_by(TreatmentProcedureDB.scheduled_date)

            result = await db.execute(query)
            procedures = result.scalars().all()

            # Group by date
            calendar: Dict[str, List[TreatmentProcedure]] = {}
            for proc in procedures:
                date_key = proc.scheduled_date.strftime("%Y-%m-%d")
                if date_key not in calendar:
                    calendar[date_key] = []
                calendar[date_key].append(_db_to_model(proc))

            return calendar

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/procedures/{procedure_id}/complete", response_model=TreatmentProcedure)
async def complete_procedure(procedure_id: str, details: Optional[ProcedureComplete] = None):
    """Mark a procedure as completed with optional details.

    Args:
        procedure_id: The procedure ID
        details: Optional completion details

    Returns:
        Updated procedure
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentProcedureDB).where(TreatmentProcedureDB.id == procedure_id)
            )
            procedure = result.scalar_one_or_none()

            if not procedure:
                raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")

            now = datetime.now()

            # Update status and details
            procedure.status = "completed"
            procedure.actual_date = details.actual_date if details and details.actual_date else now
            procedure.updated_at = now

            if details:
                if details.actual_dose:
                    procedure.actual_dose = details.actual_dose
                if details.administered_by:
                    procedure.administered_by = details.administered_by
                if details.administration_notes:
                    procedure.administration_notes = details.administration_notes
                if details.adverse_events:
                    procedure.adverse_events = [ae.model_dump() for ae in details.adverse_events]
                if details.lab_results:
                    procedure.lab_results = details.lab_results
                if details.imaging_results:
                    procedure.imaging_results = details.imaging_results.model_dump()

            # Create patient event
            event = PatientEventDB(
                id=str(uuid.uuid4()),
                patient_id=procedure.patient_id,
                event_type="procedure_completed",
                event_date=procedure.actual_date,
                title=f"Completed: {procedure.procedure_name}",
                description=f"Type: {procedure.procedure_type}. {procedure.administration_notes or ''}".strip(),
                reference_type="procedure",
                reference_id=procedure_id,
                created_at=now
            )
            db.add(event)

            await db.commit()
            await db.refresh(procedure)

            return _db_to_model(procedure)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/procedures/{procedure_id}/cancel", response_model=TreatmentProcedure)
async def cancel_procedure(procedure_id: str, cancel_data: Optional[ProcedureCancel] = None):
    """Cancel a scheduled procedure.

    Args:
        procedure_id: The procedure ID
        cancel_data: Optional cancellation reason

    Returns:
        Updated procedure
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(TreatmentProcedureDB).where(TreatmentProcedureDB.id == procedure_id)
            )
            procedure = result.scalar_one_or_none()

            if not procedure:
                raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")

            now = datetime.now()

            procedure.status = "cancelled"
            procedure.updated_at = now
            if cancel_data and cancel_data.reason:
                procedure.administration_notes = f"Cancelled: {cancel_data.reason}"

            await db.commit()
            await db.refresh(procedure)

            return _db_to_model(procedure)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/treatment-cycles/{cycle_id}/procedures/generate", response_model=List[TreatmentProcedure])
async def generate_cycle_procedures(
    cycle_id: str,
    request: GenerateProceduresRequest
):
    """Generate procedures for a cycle based on a schedule pattern.

    Args:
        cycle_id: The treatment cycle ID
        request: Generation request with schedule_days, procedure_type, start_time, location

    Returns:
        List of created procedures
    """
    try:
        async with async_session_maker() as db:
            # Get cycle details
            result = await db.execute(
                select(TreatmentCycleDB).where(TreatmentCycleDB.id == cycle_id)
            )
            cycle = result.scalar_one_or_none()
            if not cycle:
                raise HTTPException(status_code=404, detail=f"Treatment cycle {cycle_id} not found")

            now = datetime.now()
            created_procedures = []

            for day in request.schedule_days:
                # Calculate scheduled date based on cycle start
                scheduled_date = cycle.start_date + timedelta(days=day - 1)

                procedure_id = str(uuid.uuid4())
                procedure_name = f"Day {day} {request.procedure_type.replace('_', ' ').title()}"

                procedure = TreatmentProcedureDB(
                    id=procedure_id,
                    treatment_cycle_id=cycle_id,
                    patient_id=cycle.patient_id,
                    procedure_type=request.procedure_type,
                    procedure_name=procedure_name,
                    day_number=day,
                    scheduled_date=scheduled_date,
                    scheduled_time=request.start_time,
                    location=request.location,
                    status="scheduled",
                    created_at=now,
                    updated_at=now
                )
                db.add(procedure)
                created_procedures.append(procedure)

            await db.commit()

            # Refresh all procedures
            for proc in created_procedures:
                await db.refresh(proc)

            return [_db_to_model(p) for p in created_procedures]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
