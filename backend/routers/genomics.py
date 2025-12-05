"""Genomics API Router - Returns AI-generated analysis results."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models.db_models import AnalysisResultDB

router = APIRouter()
logger = logging.getLogger(__name__)


class GenomicReportResponse(BaseModel):
    """Response containing genomic analysis from AI."""
    report: dict
    has_actionable_mutations: bool
    actionable_mutation_count: int


class MutationsResponse(BaseModel):
    """Response containing mutations from analysis."""
    patient_id: str
    total_mutations: int
    mutations: List[dict]


class TherapiesResponse(BaseModel):
    """Response containing targeted therapies from analysis."""
    patient_id: str
    total_therapies: int
    therapies: List[dict]


async def get_latest_analysis(patient_id: str, db: AsyncSession) -> Optional[dict]:
    """Get the latest completed analysis for a patient."""
    result = await db.execute(
        select(AnalysisResultDB)
        .where(AnalysisResultDB.patient_id == patient_id)
        .where(AnalysisResultDB.status == "completed")
        .order_by(desc(AnalysisResultDB.completed_at))
        .limit(1)
    )
    analysis = result.scalar_one_or_none()
    if analysis and analysis.result_data:
        return analysis.result_data
    return None


@router.get("/patients/{patient_id}/genomics", response_model=GenomicReportResponse)
async def get_patient_genomics(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get genomic analysis for a patient from AI-generated results.

    Args:
        patient_id: The patient ID

    Returns:
        Genomic analysis and summary from the AI

    Raises:
        404: No completed analysis found
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}. Run an analysis first."
        )

    genomic_analysis = analysis_data.get("genomic_analysis")

    if not genomic_analysis:
        # Return empty genomics structure if not available
        return GenomicReportResponse(
            report={
                "patient_id": patient_id,
                "summary": "No genomic data available. Upload genomic test results to enable genomic analysis.",
                "mutations": [],
                "immunotherapy_markers": None
            },
            has_actionable_mutations=False,
            actionable_mutation_count=0
        )

    # Extract report from genomic_analysis
    report = genomic_analysis.get("report")

    # If report is None, use the genomic_analysis itself or return empty
    if not report:
        # Check if genomic_analysis has mutations directly
        report = genomic_analysis if genomic_analysis.get("mutations") or genomic_analysis.get("actionable_mutations") else {
            "patient_id": patient_id,
            "summary": genomic_analysis.get("summary", "No genomic data available"),
            "mutations": [],
            "actionable_mutations": [],
            "immunotherapy_markers": None
        }

    # Count actionable mutations
    mutations = report.get("mutations", []) or report.get("actionable_mutations", []) or []
    actionable = [m for m in mutations if m and (m.get("classification") == "pathogenic_actionable" or m.get("actionable"))]

    return GenomicReportResponse(
        report=report,
        has_actionable_mutations=len(actionable) > 0,
        actionable_mutation_count=len(actionable)
    )


@router.get("/patients/{patient_id}/genomics/mutations")
async def get_patient_mutations(
    patient_id: str,
    actionable_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get mutations for a patient from AI analysis.

    Args:
        patient_id: The patient ID
        actionable_only: If True, only return actionable mutations

    Returns:
        List of mutations from analysis
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}"
        )

    genomic_analysis = analysis_data.get("genomic_analysis") or {}
    report = genomic_analysis.get("report") if genomic_analysis else None
    if not report:
        report = genomic_analysis if genomic_analysis else {}

    mutations = (report.get("mutations") or report.get("actionable_mutations") or []) if report else []

    if actionable_only:
        mutations = [
            m for m in mutations
            if m.get("classification") == "pathogenic_actionable" or m.get("actionable")
        ]

    return MutationsResponse(
        patient_id=patient_id,
        total_mutations=len(mutations),
        mutations=mutations
    )


@router.get("/patients/{patient_id}/genomics/therapies")
async def get_patient_targeted_therapies(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get targeted therapies based on AI genomic analysis.

    Args:
        patient_id: The patient ID

    Returns:
        List of potential targeted therapies from analysis
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}"
        )

    genomic_analysis = analysis_data.get("genomic_analysis") or {}
    report = genomic_analysis.get("report") if genomic_analysis else None
    if not report:
        report = genomic_analysis if genomic_analysis else {}

    # Collect therapies from mutations (check both 'mutations' and 'actionable_mutations')
    therapies = []
    mutations = (report.get("mutations") or report.get("actionable_mutations") or []) if report else []

    for mutation in mutations:
        mutation_therapies = mutation.get("therapies", [])
        for therapy in mutation_therapies:
            therapies.append({
                "drug": therapy.get("drug") or therapy.get("drug_name") or therapy.get("name") or "Unknown",
                "evidence_level": therapy.get("evidence_level") or "Unknown",
                "response_rate": therapy.get("response_rate") or therapy.get("expected_response_rate"),
                "indication": therapy.get("indication") or "",
                "target_mutation": f"{mutation.get('gene', '')} {mutation.get('variant', '')}"
            })

    # Also check treatment_plan for targeted therapy recommendations
    treatment_plan = analysis_data.get("treatment_plan") or {}
    if treatment_plan:
        primary = treatment_plan.get("primary_recommendation") or {}
        if primary and (primary.get("category") == "Targeted Therapy" or primary.get("treatment_type") == "Targeted Therapy"):
            expected_outcomes = primary.get("expected_outcomes") or {}
            therapies.append({
                "drug": primary.get("name") or primary.get("treatment_name") or "Unknown",
                "evidence_level": primary.get("evidence_level") or "Unknown",
                "response_rate": expected_outcomes.get("response_rate"),
                "indication": primary.get("rationale") or "",
                "target_mutation": "Based on tumor profile"
            })

    return TherapiesResponse(
        patient_id=patient_id,
        total_therapies=len(therapies),
        therapies=therapies
    )
