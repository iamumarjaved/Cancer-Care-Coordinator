"""Treatment API Router - Returns AI-generated analysis results."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models.db_models import AnalysisResultDB

router = APIRouter()
logger = logging.getLogger(__name__)


class TreatmentPlanResponse(BaseModel):
    """Response containing treatment plan from AI analysis."""
    plan: dict
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ApproveRequest(BaseModel):
    """Request to approve a treatment option."""
    treatment_option_id: str
    approved_by: str
    notes: Optional[str] = None


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


@router.get("/patients/{patient_id}/treatment", response_model=TreatmentPlanResponse)
async def get_treatment_plan(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get treatment plan for a patient from AI analysis.

    Args:
        patient_id: The patient ID

    Returns:
        Treatment plan with recommendations from AI analysis

    Raises:
        404: No completed analysis found
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}. Run an analysis first."
        )

    treatment_plan = analysis_data.get("treatment_plan")

    if not treatment_plan:
        # Return empty plan if not available
        return TreatmentPlanResponse(
            plan={
                "id": f"TP-{patient_id}",
                "patient_id": patient_id,
                "status": "pending",
                "summary": "No treatment plan generated. Run a comprehensive analysis to generate treatment recommendations.",
                "primary_recommendation": None,
                "alternative_options": [],
                "discussion_points": analysis_data.get("discussion_points", [])
            },
            requires_approval=False
        )

    # Add summary and discussion points from main analysis
    if not treatment_plan.get("summary"):
        treatment_plan["summary"] = analysis_data.get("summary", "")
    if not treatment_plan.get("discussion_points"):
        treatment_plan["discussion_points"] = analysis_data.get("discussion_points", [])

    return TreatmentPlanResponse(
        plan=treatment_plan,
        requires_approval=treatment_plan.get("status", "pending") == "pending" or treatment_plan.get("status") == "pending_review",
        approved_by=treatment_plan.get("approved_by"),
        approved_at=treatment_plan.get("approved_at")
    )


@router.post("/patients/{patient_id}/treatment/approve")
async def approve_treatment(patient_id: str, request: ApproveRequest, db: AsyncSession = Depends(get_db)):
    """Approve a treatment recommendation.

    Note: In production, this would update the database. Currently returns success.

    Args:
        patient_id: The patient ID
        request: Approval details

    Returns:
        Updated treatment plan status
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}"
        )

    treatment_plan = analysis_data.get("treatment_plan", {})

    # Get the treatment option name
    option_name = "Unknown"
    primary = treatment_plan.get("primary_recommendation", {})
    if primary and (primary.get("id") == request.treatment_option_id or request.treatment_option_id == "primary"):
        option_name = primary.get("name", primary.get("treatment_name", "Primary Recommendation"))
    else:
        for alt in treatment_plan.get("alternative_options", []):
            if alt.get("id") == request.treatment_option_id:
                option_name = alt.get("name", alt.get("treatment_name", "Alternative"))
                break

    return {
        "patient_id": patient_id,
        "status": "approved",
        "approved_treatment": option_name,
        "approved_by": request.approved_by,
        "approved_at": datetime.now().isoformat(),
        "notes": request.notes
    }


@router.get("/patients/{patient_id}/treatment/options")
async def get_treatment_options(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get all treatment options for a patient from AI analysis.

    Args:
        patient_id: The patient ID

    Returns:
        List of all treatment options
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}"
        )

    treatment_plan = analysis_data.get("treatment_plan", {})

    all_options = []

    primary = treatment_plan.get("primary_recommendation")
    if primary:
        all_options.append(primary)

    alternatives = treatment_plan.get("alternative_options", [])
    all_options.extend(alternatives)

    return {
        "patient_id": patient_id,
        "total_options": len(all_options),
        "options": all_options
    }


@router.get("/patients/{patient_id}/treatment/evidence")
async def get_treatment_evidence(patient_id: str, treatment_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get evidence supporting treatment recommendations from AI analysis.

    Args:
        patient_id: The patient ID
        treatment_id: Optional specific treatment to get evidence for

    Returns:
        Evidence supporting recommendations
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}"
        )

    treatment_plan = analysis_data.get("treatment_plan", {})
    evidence_summary = analysis_data.get("evidence_summary", {})

    all_options = []
    primary = treatment_plan.get("primary_recommendation")
    if primary:
        all_options.append(primary)
    all_options.extend(treatment_plan.get("alternative_options", []))

    if treatment_id:
        option = next((o for o in all_options if o.get("id") == treatment_id), None)
        if not option:
            raise HTTPException(
                status_code=404,
                detail=f"Treatment option {treatment_id} not found"
            )
        options = [option]
    else:
        options = all_options

    evidence = []
    for opt in options:
        evidence.append({
            "treatment_id": opt.get("id"),
            "treatment_name": opt.get("name", opt.get("treatment_name")),
            "evidence_level": opt.get("evidence_level"),
            "supporting_evidence": opt.get("supporting_evidence", opt.get("key_trials", [])),
            "expected_outcomes": opt.get("expected_outcomes", {}),
            "rationale": opt.get("rationale")
        })

    # Add evidence from evidence_summary if available
    evidence_summaries = evidence_summary.get("evidence_summaries", []) if evidence_summary else []

    return {
        "patient_id": patient_id,
        "evidence": evidence,
        "evidence_summaries": evidence_summaries,
        "sources_used": analysis_data.get("sources_used", [])
    }
