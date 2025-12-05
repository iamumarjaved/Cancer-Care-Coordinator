"""Patients API Router."""

import math
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import select, desc

from models.patient import (
    Patient, CancerDetails, PatientStatus, ClosureReason,
    PatientClosure, PatientStatusUpdate, PatientEvent
)
from models.db_models import PatientDB, PatientEventDB
from services.patient_service import PatientService
from database import async_session_maker

router = APIRouter()

# Service instance (will be replaced with dependency injection)
_patient_service: Optional[PatientService] = None


def get_patient_service() -> PatientService:
    """Get or create patient service instance."""
    global _patient_service
    if _patient_service is None:
        _patient_service = PatientService()
    return _patient_service


# Response models
class PatientListResponse(BaseModel):
    """Response for patient list endpoint."""
    items: List[Patient]
    total: int
    page: int
    page_size: int
    total_pages: int


class CancerDetailsRequest(BaseModel):
    """Cancer details for patient creation/update."""
    cancer_type: str
    subtype: Optional[str] = None
    stage: Optional[str] = None
    tnm_staging: Optional[str] = None
    primary_site: Optional[str] = None
    metastases: Optional[List[str]] = None
    diagnosis_date: Optional[str] = None


class ComorbidityRequest(BaseModel):
    """Comorbidity for patient creation/update."""
    condition: str
    severity: Optional[str] = "moderate"
    treatment_implications: Optional[List[str]] = None


class PatientCreateRequest(BaseModel):
    """Request to create a patient."""
    id: str
    first_name: str
    last_name: str
    date_of_birth: str  # ISO format
    sex: str
    email: Optional[str] = None
    phone: Optional[str] = None
    cancer_details: Optional[CancerDetailsRequest] = None
    comorbidities: Optional[List[ComorbidityRequest]] = None
    ecog_status: Optional[int] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    smoking_status: Optional[str] = None
    pack_years: Optional[int] = None


class PatientUpdateRequest(BaseModel):
    """Request to update a patient."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cancer_details: Optional[CancerDetailsRequest] = None
    comorbidities: Optional[List[ComorbidityRequest]] = None
    ecog_status: Optional[int] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    smoking_status: Optional[str] = None
    pack_years: Optional[int] = None


class PopulateTestDataResponse(BaseModel):
    """Response for test data population."""
    success: bool
    message: str
    patients_created: int
    patient_ids: List[str]


# =====================================================
# SPECIFIC ROUTES (must come before parameterized routes)
# =====================================================

@router.get("/patients", response_model=PatientListResponse)
async def list_patients(
    search: Optional[str] = Query(None, description="Search by name or ID"),
    cancer_type: Optional[str] = Query(None, description="Filter by cancer type"),
    stage: Optional[str] = Query(None, description="Filter by cancer stage"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """List all patients with optional filtering and pagination.

    Args:
        search: Search term for name or ID
        cancer_type: Filter by cancer type
        stage: Filter by cancer stage
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of patients
    """
    service = get_patient_service()

    filters = {}
    if search:
        filters["search"] = search
    if cancer_type:
        filters["cancer_type"] = cancer_type
    if stage:
        filters["stage"] = stage

    all_patients = await service.get_all(filters)
    total = len(all_patients)

    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_patients[start:end]

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PatientListResponse(
        items=paginated,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/patients", response_model=Patient, status_code=201)
async def create_patient(request: PatientCreateRequest):
    """Create a new patient.

    Args:
        request: Patient creation data

    Returns:
        Created patient

    Raises:
        400: Invalid data or patient already exists
    """
    from datetime import date
    from models.patient import (
        CancerDetails, CancerType, CancerStage,
        ECOGStatus, Comorbidity
    )

    service = get_patient_service()

    try:
        # Parse cancer details if provided
        cancer_details = None
        if request.cancer_details and request.cancer_details.cancer_type:
            cd = request.cancer_details
            # Map cancer type string to enum
            cancer_type_map = {
                "NSCLC": CancerType.NSCLC,
                "SCLC": CancerType.SCLC,
                "Breast": CancerType.BREAST,
                "Colorectal": CancerType.COLORECTAL,
                "Melanoma": CancerType.MELANOMA,
                "Pancreatic": CancerType.PANCREATIC,
            }
            cancer_type = cancer_type_map.get(cd.cancer_type, CancerType.OTHER)

            # Map stage string to enum
            stage_map = {
                "Stage I": CancerStage.STAGE_I,
                "Stage II": CancerStage.STAGE_II,
                "Stage IIIA": CancerStage.STAGE_IIIA,
                "Stage IIIB": CancerStage.STAGE_IIIB,
                "Stage IIIC": CancerStage.STAGE_IIIC,
                "Stage IV": CancerStage.STAGE_IV,
            }
            stage = stage_map.get(cd.stage, CancerStage.STAGE_I) if cd.stage else None

            cancer_details = CancerDetails(
                cancer_type=cancer_type,
                subtype=cd.subtype,
                stage=stage,
                tnm_staging=cd.tnm_staging,
                primary_site=cd.primary_site or "Unknown",
                metastases=cd.metastases or [],
                diagnosis_date=date.fromisoformat(cd.diagnosis_date) if cd.diagnosis_date else None
            )

        # Parse comorbidities if provided
        comorbidities = []
        if request.comorbidities:
            for comorb in request.comorbidities:
                comorbidities.append(Comorbidity(
                    condition=comorb.condition,
                    severity=comorb.severity or "moderate",
                    treatment_implications=comorb.treatment_implications or []
                ))

        # Map ECOG status
        ecog_value = request.ecog_status if request.ecog_status is not None else 1
        ecog_map = {
            0: ECOGStatus.FULLY_ACTIVE,
            1: ECOGStatus.RESTRICTED,
            2: ECOGStatus.AMBULATORY,
            3: ECOGStatus.LIMITED_SELF_CARE,
            4: ECOGStatus.DISABLED,
        }
        ecog_status = ecog_map.get(ecog_value, ECOGStatus.RESTRICTED)

        patient = Patient(
            id=request.id,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=date.fromisoformat(request.date_of_birth),
            sex=request.sex,
            email=request.email,
            phone=request.phone,
            cancer_details=cancer_details,
            comorbidities=comorbidities,
            ecog_status=ecog_status,
            current_medications=request.current_medications or [],
            allergies=request.allergies or [],
            smoking_status=request.smoking_status,
            pack_years=request.pack_years
        )
        created = await service.create(patient)
        return created

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/patients/populate-test-data", response_model=PopulateTestDataResponse)
async def populate_test_data():
    """Populate the database with comprehensive test patients.

    Creates 12 diverse test patients covering:
    - NSCLC (EGFR, ALK, KRAS mutations)
    - Breast Cancer (HER2+, TNBC, HR+)
    - Colorectal Cancer (MSI-H, BRAF, RAS WT)
    - Melanoma (BRAF, NRAS)
    - Pancreatic Cancer (BRCA2)

    Returns:
        List of created patient IDs
    """
    from datetime import date
    from data.test_patients import get_test_patients
    from models.patient import (
        Patient, CancerDetails, CancerType, CancerStage,
        ECOGStatus, Comorbidity, OrganFunction
    )

    service = get_patient_service()
    test_patients = get_test_patients()
    created_ids = []

    for patient_data in test_patients:
        try:
            # Check if patient already exists
            existing = await service.get_by_id(patient_data["id"])
            if existing:
                # Skip if already exists
                continue

            # Parse cancer details
            cd = patient_data.get("cancer_details", {})
            cancer_type_str = cd.get("cancer_type", "Other")
            # Map to enum
            cancer_type_map = {
                "NSCLC": CancerType.NSCLC,
                "Breast": CancerType.BREAST,
                "Colorectal": CancerType.COLORECTAL,
                "Melanoma": CancerType.MELANOMA,
                "Pancreatic": CancerType.PANCREATIC,
            }
            cancer_type = cancer_type_map.get(cancer_type_str, CancerType.OTHER)

            # Map stage
            stage_str = cd.get("stage", "Stage I")
            stage_map = {
                "Stage I": CancerStage.STAGE_I,
                "Stage II": CancerStage.STAGE_II,
                "Stage IIIA": CancerStage.STAGE_IIIA,
                "Stage IIIB": CancerStage.STAGE_IIIB,
                "Stage IIIC": CancerStage.STAGE_IIIC,
                "Stage IV": CancerStage.STAGE_IV,
            }
            stage = stage_map.get(stage_str, CancerStage.STAGE_I)

            cancer_details = CancerDetails(
                cancer_type=cancer_type,
                subtype=cd.get("subtype"),
                stage=stage,
                tnm_staging=cd.get("tnm_staging"),
                primary_site=cd.get("primary_site", "Unknown"),
                tumor_size_cm=cd.get("tumor_size_cm"),
                metastases=cd.get("metastases", []),
                histology=cd.get("histology"),
                grade=cd.get("grade"),
                diagnosis_date=date.fromisoformat(cd["diagnosis_date"]) if cd.get("diagnosis_date") else None
            )

            # Parse comorbidities
            comorbidities = []
            for comorb in patient_data.get("comorbidities", []):
                comorbidities.append(Comorbidity(
                    condition=comorb.get("condition", "Unknown"),
                    severity=comorb.get("severity", "mild"),
                    treatment_implications=comorb.get("treatment_implications", [])
                ))

            # Parse organ function
            organ_function = []
            for organ in patient_data.get("organ_function", []):
                organ_function.append(OrganFunction(
                    organ=organ.get("organ", "Unknown"),
                    status=organ.get("status", "normal"),
                    key_values=organ.get("key_values", {}),
                    notes=organ.get("notes")
                ))

            # Map ECOG status
            ecog_value = patient_data.get("ecog_status", 0)
            ecog_map = {
                0: ECOGStatus.FULLY_ACTIVE,
                1: ECOGStatus.RESTRICTED,
                2: ECOGStatus.AMBULATORY,
                3: ECOGStatus.LIMITED_SELF_CARE,
                4: ECOGStatus.DISABLED,
            }
            ecog_status = ecog_map.get(ecog_value, ECOGStatus.FULLY_ACTIVE)

            # Create patient
            patient = Patient(
                id=patient_data["id"],
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                date_of_birth=date.fromisoformat(patient_data["date_of_birth"]),
                sex=patient_data.get("sex", "Unknown"),
                email=patient_data.get("email"),
                phone=patient_data.get("phone"),
                cancer_details=cancer_details,
                comorbidities=comorbidities,
                organ_function=organ_function,
                ecog_status=ecog_status,
                current_medications=patient_data.get("current_medications", []),
                allergies=patient_data.get("allergies", []),
                smoking_status=patient_data.get("smoking_status"),
                pack_years=patient_data.get("pack_years"),
                genomic_report_id=patient_data.get("genomic_report_id"),
                clinical_notes=patient_data.get("clinical_notes", [])
            )

            await service.create(patient)
            created_ids.append(patient_data["id"])

        except Exception as e:
            # Log error but continue with other patients
            import logging
            logging.error(f"Error creating test patient {patient_data.get('id')}: {e}")
            continue

    return PopulateTestDataResponse(
        success=True,
        message=f"Successfully created {len(created_ids)} test patients",
        patients_created=len(created_ids),
        patient_ids=created_ids
    )


@router.delete("/patients/clear-test-data", status_code=200)
async def clear_test_data():
    """Clear all test patients (IDs starting with 'TEST').

    Returns:
        Number of patients deleted
    """
    service = get_patient_service()
    all_patients = await service.get_all()

    deleted_count = 0
    for patient in all_patients:
        if patient.id.startswith("TEST"):
            await service.delete(patient.id)
            deleted_count += 1

    return {"success": True, "patients_deleted": deleted_count}


# =====================================================
# PARAMETERIZED ROUTES (must come after specific routes)
# =====================================================

@router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    """Get a patient by ID.

    Args:
        patient_id: The patient ID

    Returns:
        Patient details

    Raises:
        404: Patient not found
    """
    service = get_patient_service()
    patient = await service.get_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return patient


@router.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(patient_id: str, request: PatientUpdateRequest):
    """Update a patient.

    Args:
        patient_id: The patient ID
        request: Fields to update

    Returns:
        Updated patient

    Raises:
        404: Patient not found
    """
    from datetime import date
    from models.patient import (
        CancerDetails, CancerType, CancerStage,
        ECOGStatus, Comorbidity
    )

    service = get_patient_service()

    # Build update data with proper parsing
    update_data = {}

    # Simple fields
    if request.first_name is not None:
        update_data["first_name"] = request.first_name
    if request.last_name is not None:
        update_data["last_name"] = request.last_name
    if request.date_of_birth is not None:
        update_data["date_of_birth"] = date.fromisoformat(request.date_of_birth)
    if request.sex is not None:
        update_data["sex"] = request.sex
    if request.email is not None:
        update_data["email"] = request.email
    if request.phone is not None:
        update_data["phone"] = request.phone
    if request.current_medications is not None:
        update_data["current_medications"] = request.current_medications
    if request.allergies is not None:
        update_data["allergies"] = request.allergies
    if request.smoking_status is not None:
        update_data["smoking_status"] = request.smoking_status
    if request.pack_years is not None:
        update_data["pack_years"] = request.pack_years

    # Parse cancer details if provided
    if request.cancer_details and request.cancer_details.cancer_type:
        cd = request.cancer_details
        # Map cancer type string to enum
        cancer_type_map = {
            "NSCLC": CancerType.NSCLC,
            "SCLC": CancerType.SCLC,
            "Breast": CancerType.BREAST,
            "Colorectal": CancerType.COLORECTAL,
            "Melanoma": CancerType.MELANOMA,
            "Pancreatic": CancerType.PANCREATIC,
        }
        cancer_type = cancer_type_map.get(cd.cancer_type, CancerType.OTHER)

        # Map stage string to enum
        stage_map = {
            "Stage I": CancerStage.STAGE_I,
            "Stage II": CancerStage.STAGE_II,
            "Stage IIIA": CancerStage.STAGE_IIIA,
            "Stage IIIB": CancerStage.STAGE_IIIB,
            "Stage IIIC": CancerStage.STAGE_IIIC,
            "Stage IV": CancerStage.STAGE_IV,
        }
        stage = stage_map.get(cd.stage, CancerStage.STAGE_I) if cd.stage else None

        update_data["cancer_details"] = CancerDetails(
            cancer_type=cancer_type,
            subtype=cd.subtype,
            stage=stage,
            tnm_staging=cd.tnm_staging,
            primary_site=cd.primary_site or "Unknown",
            metastases=cd.metastases or [],
            diagnosis_date=date.fromisoformat(cd.diagnosis_date) if cd.diagnosis_date else None
        )

    # Parse comorbidities if provided
    if request.comorbidities is not None:
        comorbidities = []
        for comorb in request.comorbidities:
            comorbidities.append(Comorbidity(
                condition=comorb.condition,
                severity=comorb.severity or "moderate",
                treatment_implications=comorb.treatment_implications or []
            ))
        update_data["comorbidities"] = comorbidities

    # Map ECOG status if provided
    if request.ecog_status is not None:
        ecog_map = {
            0: ECOGStatus.FULLY_ACTIVE,
            1: ECOGStatus.RESTRICTED,
            2: ECOGStatus.AMBULATORY,
            3: ECOGStatus.LIMITED_SELF_CARE,
            4: ECOGStatus.DISABLED,
        }
        update_data["ecog_status"] = ecog_map.get(request.ecog_status, ECOGStatus.RESTRICTED)

    updated = await service.update(patient_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return updated


@router.delete("/patients/{patient_id}", status_code=204)
async def delete_patient(patient_id: str):
    """Delete a patient.

    Args:
        patient_id: The patient ID

    Raises:
        404: Patient not found
    """
    service = get_patient_service()
    deleted = await service.delete(patient_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")


# =====================================================
# STATUS AND TIMELINE ENDPOINTS
# =====================================================

@router.patch("/patients/{patient_id}/status")
async def update_patient_status(patient_id: str, status_update: PatientStatusUpdate):
    """Update patient status (active/closed).

    Args:
        patient_id: The patient ID
        status_update: Status update with optional closure reason

    Returns:
        Updated patient status info

    Raises:
        404: Patient not found
        400: Invalid status update (e.g., closing without reason)
    """
    try:
        async with async_session_maker() as db:
            # Get patient
            result = await db.execute(
                select(PatientDB).where(PatientDB.id == patient_id)
            )
            patient = result.scalar_one_or_none()

            if not patient:
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            # Update status
            patient.status = status_update.status.value
            now = datetime.now()

            # Handle closure
            if status_update.status == PatientStatus.CLOSED:
                if not status_update.closure:
                    raise HTTPException(
                        status_code=400,
                        detail="Closure reason required when closing patient file"
                    )
                patient.closure_reason = status_update.closure.reason.value
                patient.closure_notes = status_update.closure.notes
                patient.closed_at = now

                # Create status change event
                event = PatientEventDB(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    event_type="status_change",
                    event_date=now,
                    title=f"Patient file closed: {status_update.closure.reason.value}",
                    description=status_update.closure.notes
                )
                db.add(event)
            else:
                # Reopening patient file
                patient.closure_reason = None
                patient.closure_notes = None
                patient.closed_at = None

                # Create status change event
                event = PatientEventDB(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    event_type="status_change",
                    event_date=now,
                    title="Patient file reopened",
                    description="Patient file was reopened for active care"
                )
                db.add(event)

            patient.updated_at = now
            await db.commit()

            return {
                "patient_id": patient_id,
                "status": patient.status,
                "closure_reason": patient.closure_reason,
                "closure_notes": patient.closure_notes,
                "closed_at": patient.closed_at.isoformat() if patient.closed_at else None,
                "updated_at": patient.updated_at.isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/timeline", response_model=List[PatientEvent])
async def get_patient_timeline(
    patient_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """Get patient's complete event timeline.

    Args:
        patient_id: The patient ID
        limit: Maximum events to return
        event_type: Optional filter by event type

    Returns:
        List of patient events in reverse chronological order

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
            query = select(PatientEventDB).where(PatientEventDB.patient_id == patient_id)

            if event_type:
                query = query.where(PatientEventDB.event_type == event_type)

            query = query.order_by(desc(PatientEventDB.event_date)).limit(limit)

            result = await db.execute(query)
            events = result.scalars().all()

            return [
                PatientEvent(
                    id=e.id,
                    patient_id=e.patient_id,
                    event_type=e.event_type,
                    event_date=e.event_date,
                    title=e.title,
                    description=e.description,
                    reference_type=e.reference_type,
                    reference_id=e.reference_id,
                    created_at=e.created_at
                )
                for e in events
            ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/status")
async def get_patient_status(patient_id: str):
    """Get patient's current status.

    Args:
        patient_id: The patient ID

    Returns:
        Patient status information

    Raises:
        404: Patient not found
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(
                    PatientDB.status,
                    PatientDB.closure_reason,
                    PatientDB.closure_notes,
                    PatientDB.closed_at
                ).where(PatientDB.id == patient_id)
            )
            row = result.first()

            if not row:
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

            return {
                "patient_id": patient_id,
                "status": row[0] or "active",
                "closure_reason": row[1],
                "closure_notes": row[2],
                "closed_at": row[3].isoformat() if row[3] else None
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
