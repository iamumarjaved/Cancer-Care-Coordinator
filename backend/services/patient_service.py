"""Patient Service - Handles patient data operations with database persistence."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.patient import Patient, CancerDetails, CancerType, CancerStage, ECOGStatus, Comorbidity, OrganFunction
from models.db_models import PatientDB
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class PatientService:
    """Service for patient data operations with database persistence."""

    def __init__(self):
        """Initialize patient service."""
        pass

    def _db_to_model(self, db_patient: PatientDB) -> Patient:
        """Convert database model to Pydantic model.

        Args:
            db_patient: Database patient record

        Returns:
            Patient Pydantic model
        """
        # Parse cancer details from JSON
        cancer_details = None
        if db_patient.cancer_details:
            cd = db_patient.cancer_details
            try:
                cancer_details = CancerDetails(
                    cancer_type=CancerType(cd.get("cancer_type", "Other")),
                    subtype=cd.get("subtype"),
                    stage=CancerStage(cd.get("stage", "Stage I")) if cd.get("stage") else None,
                    tnm_staging=cd.get("tnm_staging"),
                    primary_site=cd.get("primary_site", "Unknown"),
                    tumor_size_cm=cd.get("tumor_size_cm"),
                    metastases=cd.get("metastases", []),
                    histology=cd.get("histology"),
                    grade=cd.get("grade"),
                    diagnosis_date=date.fromisoformat(cd["diagnosis_date"]) if cd.get("diagnosis_date") else None
                )
            except Exception as e:
                logger.warning(f"Error parsing cancer details for patient {db_patient.id}: {e}")

        # Parse comorbidities from JSON
        comorbidities = []
        for comorb in (db_patient.comorbidities or []):
            try:
                comorbidities.append(Comorbidity(
                    condition=comorb.get("condition", "Unknown"),
                    severity=comorb.get("severity", "mild"),
                    treatment_implications=comorb.get("treatment_implications", [])
                ))
            except Exception as e:
                logger.warning(f"Error parsing comorbidity: {e}")

        # Parse organ function from JSON
        organ_function = []
        for organ in (db_patient.organ_function or []):
            try:
                organ_function.append(OrganFunction(
                    organ=organ.get("organ", "Unknown"),
                    status=organ.get("status", "normal"),
                    key_values=organ.get("key_values", {}),
                    notes=organ.get("notes")
                ))
            except Exception as e:
                logger.warning(f"Error parsing organ function: {e}")

        # Parse ECOG status
        ecog_status = None
        if db_patient.ecog_status is not None:
            ecog_map = {
                0: ECOGStatus.FULLY_ACTIVE,
                1: ECOGStatus.RESTRICTED,
                2: ECOGStatus.AMBULATORY,
                3: ECOGStatus.LIMITED_SELF_CARE,
                4: ECOGStatus.DISABLED,
            }
            ecog_status = ecog_map.get(db_patient.ecog_status, ECOGStatus.RESTRICTED)

        return Patient(
            id=db_patient.id,
            first_name=db_patient.first_name,
            last_name=db_patient.last_name,
            date_of_birth=date.fromisoformat(db_patient.date_of_birth) if isinstance(db_patient.date_of_birth, str) else db_patient.date_of_birth,
            sex=db_patient.sex or "Unknown",
            email=db_patient.email,
            phone=db_patient.phone,
            cancer_details=cancer_details,
            comorbidities=comorbidities,
            organ_function=organ_function,
            ecog_status=ecog_status,
            current_medications=db_patient.current_medications or [],
            allergies=db_patient.allergies or [],
            smoking_status=db_patient.smoking_status,
            pack_years=db_patient.pack_years,
            genomic_report_id=db_patient.genomic_report_id,
            clinical_notes=db_patient.clinical_notes or [],
            status=db_patient.status or "active",
            closure_reason=db_patient.closure_reason,
            closure_notes=db_patient.closure_notes,
            closed_at=db_patient.closed_at
        )

    def _model_to_db_dict(self, patient: Patient) -> Dict[str, Any]:
        """Convert Pydantic model to database dict.

        Args:
            patient: Pydantic Patient model

        Returns:
            Dict for database insertion
        """
        # Convert cancer details to JSON-serializable dict
        cancer_details_dict = None
        if patient.cancer_details:
            cd = patient.cancer_details
            cancer_details_dict = {
                "cancer_type": cd.cancer_type.value if cd.cancer_type else None,
                "subtype": cd.subtype,
                "stage": cd.stage.value if cd.stage else None,
                "tnm_staging": cd.tnm_staging,
                "primary_site": cd.primary_site,
                "tumor_size_cm": cd.tumor_size_cm,
                "metastases": cd.metastases or [],
                "histology": cd.histology,
                "grade": cd.grade,
                "diagnosis_date": cd.diagnosis_date.isoformat() if cd.diagnosis_date else None
            }

        # Convert comorbidities to JSON-serializable list
        comorbidities_list = []
        for c in (patient.comorbidities or []):
            comorbidities_list.append({
                "condition": c.condition,
                "severity": c.severity,
                "treatment_implications": c.treatment_implications or []
            })

        # Convert organ function to JSON-serializable list
        organ_function_list = []
        for o in (patient.organ_function or []):
            organ_function_list.append({
                "organ": o.organ,
                "status": o.status,
                "key_values": o.key_values or {},
                "notes": o.notes
            })

        # Convert ECOG status to int
        ecog_int = None
        if patient.ecog_status:
            ecog_map = {
                ECOGStatus.FULLY_ACTIVE: 0,
                ECOGStatus.RESTRICTED: 1,
                ECOGStatus.AMBULATORY: 2,
                ECOGStatus.LIMITED_SELF_CARE: 3,
                ECOGStatus.DISABLED: 4,
            }
            ecog_int = ecog_map.get(patient.ecog_status)

        return {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if isinstance(patient.date_of_birth, date) else patient.date_of_birth,
            "sex": patient.sex,
            "email": patient.email,
            "phone": patient.phone,
            "cancer_details": cancer_details_dict,
            "comorbidities": comorbidities_list,
            "organ_function": organ_function_list,
            "ecog_status": ecog_int,
            "current_medications": patient.current_medications or [],
            "allergies": patient.allergies or [],
            "smoking_status": patient.smoking_status,
            "pack_years": patient.pack_years,
            "genomic_report_id": patient.genomic_report_id,
            "clinical_notes": patient.clinical_notes or []
        }

    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Patient]:
        """Get all patients with optional filtering.

        Args:
            filters: Optional filter criteria

        Returns:
            List of matching patients
        """
        async with AsyncSessionLocal() as session:
            query = select(PatientDB)

            # Apply filters
            if filters:
                if filters.get("search"):
                    search = f"%{filters['search'].lower()}%"
                    query = query.where(
                        or_(
                            func.lower(PatientDB.first_name).like(search),
                            func.lower(PatientDB.last_name).like(search),
                            func.lower(PatientDB.id).like(search)
                        )
                    )

            query = query.order_by(PatientDB.last_name, PatientDB.first_name)
            result = await session.execute(query)
            db_patients = result.scalars().all()

            patients = [self._db_to_model(p) for p in db_patients]

            # Apply in-memory filters for complex JSON fields
            if filters:
                if filters.get("cancer_type"):
                    patients = [
                        p for p in patients
                        if p.cancer_details and p.cancer_details.cancer_type.value == filters["cancer_type"]
                    ]
                if filters.get("stage"):
                    patients = [
                        p for p in patients
                        if p.cancer_details and p.cancer_details.stage and p.cancer_details.stage.value == filters["stage"]
                    ]

            return patients

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID.

        Args:
            patient_id: The patient ID

        Returns:
            Patient or None if not found
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.id == patient_id)
            )
            db_patient = result.scalar_one_or_none()

            if db_patient:
                return self._db_to_model(db_patient)
            return None

    async def create(self, patient: Patient) -> Patient:
        """Create a new patient.

        Args:
            patient: Patient to create

        Returns:
            Created patient

        Raises:
            ValueError: If patient with ID already exists
        """
        async with AsyncSessionLocal() as session:
            # Check if patient already exists
            existing = await session.execute(
                select(PatientDB).where(PatientDB.id == patient.id)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Patient with ID {patient.id} already exists")

            # Create database record
            db_dict = self._model_to_db_dict(patient)
            db_patient = PatientDB(**db_dict)

            session.add(db_patient)
            await session.commit()
            await session.refresh(db_patient)

            logger.info(f"Created patient: {patient.id}")
            return self._db_to_model(db_patient)

    async def update(self, patient_id: str, data: Dict[str, Any]) -> Optional[Patient]:
        """Update a patient.

        Args:
            patient_id: The patient ID
            data: Fields to update

        Returns:
            Updated patient or None if not found
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.id == patient_id)
            )
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                return None

            # Update simple fields
            simple_fields = ["first_name", "last_name", "date_of_birth", "sex", "email", "phone",
                          "smoking_status", "pack_years", "genomic_report_id"]
            for field in simple_fields:
                if field in data:
                    setattr(db_patient, field, data[field])

            # Update JSON fields
            if "cancer_details" in data:
                db_patient.cancer_details = data["cancer_details"]
            if "comorbidities" in data:
                db_patient.comorbidities = data["comorbidities"]
            if "organ_function" in data:
                db_patient.organ_function = data["organ_function"]
            if "ecog_status" in data:
                db_patient.ecog_status = data["ecog_status"]
            if "current_medications" in data:
                db_patient.current_medications = data["current_medications"]
            if "allergies" in data:
                db_patient.allergies = data["allergies"]
            if "clinical_notes" in data:
                db_patient.clinical_notes = data["clinical_notes"]

            await session.commit()
            await session.refresh(db_patient)

            logger.info(f"Updated patient: {patient_id}")
            return self._db_to_model(db_patient)

    async def delete(self, patient_id: str) -> bool:
        """Delete a patient.

        Args:
            patient_id: The patient ID

        Returns:
            True if deleted, False if not found
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.id == patient_id)
            )
            db_patient = result.scalar_one_or_none()

            if not db_patient:
                return False

            await session.delete(db_patient)
            await session.commit()

            logger.info(f"Deleted patient: {patient_id}")
            return True

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count of patients.

        Args:
            filters: Optional filter criteria

        Returns:
            Count of matching patients
        """
        patients = await self.get_all(filters)
        return len(patients)
