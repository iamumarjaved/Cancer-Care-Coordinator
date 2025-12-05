#!/usr/bin/env python3
"""Database seeding script for production deployment."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from database import AsyncSessionLocal, init_db_async
from models.db_models import PatientDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_patients():
    """Seed patients from JSON file into the database."""
    # Initialize database tables first
    await init_db_async()

    async with AsyncSessionLocal() as session:
        # Check if patients already exist
        result = await session.execute(select(func.count(PatientDB.id)))
        count = result.scalar()

        if count > 0:
            logger.info(f"Database already has {count} patients, skipping seed")
            return

        # Load from JSON file
        data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"

        if not data_path.exists():
            logger.error(f"Seed data file not found: {data_path}")
            return

        with open(data_path, "r") as f:
            data = json.load(f)

        patients = data.get("patients", [])

        for patient_data in patients:
            patient_db = PatientDB(
                id=patient_data["id"],
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                date_of_birth=patient_data["date_of_birth"],
                sex=patient_data.get("sex", "Unknown"),
                email=patient_data.get("email"),
                phone=patient_data.get("phone"),
                cancer_details=patient_data.get("cancer_details"),
                comorbidities=patient_data.get("comorbidities", []),
                organ_function=patient_data.get("organ_function", []),
                ecog_status=patient_data.get("ecog_status"),
                current_medications=patient_data.get("current_medications", []),
                allergies=patient_data.get("allergies", []),
                smoking_status=patient_data.get("smoking_status"),
                pack_years=patient_data.get("pack_years"),
                genomic_report_id=patient_data.get("genomic_report_id"),
                clinical_notes=patient_data.get("clinical_notes", [])
            )
            session.add(patient_db)

        await session.commit()
        logger.info(f"Successfully seeded {len(patients)} patients")


if __name__ == "__main__":
    asyncio.run(seed_patients())
