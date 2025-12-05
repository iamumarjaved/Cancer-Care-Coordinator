"""Clinical Trials API Router - Returns AI-generated analysis results."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models.db_models import AnalysisResultDB

router = APIRouter()
logger = logging.getLogger(__name__)


class TrialMatchResponse(BaseModel):
    """Response containing matched trials from AI analysis."""
    patient_id: str
    total_trials_searched: int
    matched_trials: int
    trials: List[dict]


class TrialDetailResponse(BaseModel):
    """Detailed trial information."""
    trial: dict
    eligibility_summary: dict


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


@router.get("/patients/{patient_id}/trials", response_model=TrialMatchResponse)
async def get_matched_trials(
    patient_id: str,
    phase: Optional[str] = Query(None, description="Filter by trial phase"),
    status: Optional[str] = Query(None, description="Filter by trial status"),
    min_match_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum match score"),
    db: AsyncSession = Depends(get_db)
):
    """Get clinical trials matched for a patient from AI analysis.

    Args:
        patient_id: The patient ID
        phase: Optional phase filter
        status: Optional status filter
        min_match_score: Minimum match score threshold

    Returns:
        List of matched clinical trials from AI analysis
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}. Run an analysis first."
        )

    clinical_trials = analysis_data.get("clinical_trials")

    if not clinical_trials:
        # Return empty list if no trials in analysis
        return TrialMatchResponse(
            patient_id=patient_id,
            total_trials_searched=0,
            matched_trials=0,
            trials=[]
        )

    # Handle different formats - could be a dict with 'trials' key or a list
    if isinstance(clinical_trials, dict):
        trials = clinical_trials.get("matched_trials", []) or clinical_trials.get("trials", [])
    elif isinstance(clinical_trials, list):
        trials = clinical_trials
    else:
        trials = []

    # Apply filters
    if phase:
        trials = [t for t in trials if t.get("phase") == phase]
    if status:
        trials = [t for t in trials if t.get("status") == status]
    if min_match_score > 0:
        trials = [t for t in trials if (t.get("match_score") or 0) >= min_match_score]

    # Sort by match score
    trials.sort(key=lambda t: t.get("match_score", 0), reverse=True)

    return TrialMatchResponse(
        patient_id=patient_id,
        total_trials_searched=clinical_trials.get("total_searched", len(trials)) if isinstance(clinical_trials, dict) else len(trials),
        matched_trials=len(trials),
        trials=trials
    )


@router.get("/trials/{nct_id}", response_model=TrialDetailResponse)
async def get_trial_details(nct_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a clinical trial.

    Args:
        nct_id: The NCT identifier

    Returns:
        Detailed trial information

    Raises:
        404: Trial not found
    """
    # Search all patient analyses for this trial
    result = await db.execute(
        select(AnalysisResultDB)
        .where(AnalysisResultDB.status == "completed")
        .order_by(desc(AnalysisResultDB.completed_at))
    )
    analyses = result.scalars().all()

    for analysis in analyses:
        if not analysis.result_data:
            continue

        clinical_trials = analysis.result_data.get("clinical_trials")
        if not clinical_trials:
            continue

        # Handle different formats
        if isinstance(clinical_trials, dict):
            trials = clinical_trials.get("matched_trials", []) or clinical_trials.get("trials", [])
        elif isinstance(clinical_trials, list):
            trials = clinical_trials
        else:
            continue

        trial = next((t for t in trials if t.get("nct_id") == nct_id), None)

        if trial:
            # Calculate eligibility summary
            criteria = trial.get("eligibility_criteria", [])
            met = sum(1 for c in criteria if c.get("patient_meets") is True)
            not_met = sum(1 for c in criteria if c.get("patient_meets") is False)
            unknown = sum(1 for c in criteria if c.get("patient_meets") is None)

            return TrialDetailResponse(
                trial=trial,
                eligibility_summary={
                    "criteria_met": met,
                    "criteria_not_met": not_met,
                    "criteria_unknown": unknown,
                    "total_criteria": len(criteria),
                    "eligibility_score": met / len(criteria) if criteria else 0
                }
            )

    raise HTTPException(
        status_code=404,
        detail=f"Trial {nct_id} not found in any patient analysis"
    )


@router.get("/trials")
async def search_trials(
    condition: Optional[str] = Query(None, description="Cancer type or condition"),
    intervention: Optional[str] = Query(None, description="Drug or intervention"),
    phase: Optional[str] = Query(None, description="Trial phase"),
    status: str = Query("recruiting", description="Trial status"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """Search clinical trials across all patient analyses.

    Args:
        condition: Cancer type or condition to search
        intervention: Drug or intervention to search
        phase: Trial phase filter
        status: Trial status filter
        limit: Maximum number of results

    Returns:
        List of matching trials from all analyses
    """
    # Collect trials from all analyses
    result = await db.execute(
        select(AnalysisResultDB)
        .where(AnalysisResultDB.status == "completed")
        .order_by(desc(AnalysisResultDB.completed_at))
    )
    analyses = result.scalars().all()

    all_trials = []
    seen_nct_ids = set()

    for analysis in analyses:
        if not analysis.result_data:
            continue

        clinical_trials = analysis.result_data.get("clinical_trials")
        if not clinical_trials:
            continue

        # Handle different formats
        if isinstance(clinical_trials, dict):
            trials = clinical_trials.get("matched_trials", []) or clinical_trials.get("trials", [])
        elif isinstance(clinical_trials, list):
            trials = clinical_trials
        else:
            continue

        for trial in trials:
            nct_id = trial.get("nct_id")
            if nct_id and nct_id not in seen_nct_ids:
                seen_nct_ids.add(nct_id)
                all_trials.append(trial)

    # Apply filters
    if condition:
        condition_lower = condition.lower()
        all_trials = [
            t for t in all_trials
            if any(condition_lower in c.lower() for c in t.get("conditions", []))
        ]

    if intervention:
        intervention_lower = intervention.lower()
        all_trials = [
            t for t in all_trials
            if any(intervention_lower in i.lower() for i in t.get("interventions", []))
        ]

    if phase:
        all_trials = [t for t in all_trials if t.get("phase") == phase]

    if status:
        all_trials = [t for t in all_trials if t.get("status", "").lower() == status.lower()]

    return {
        "total_results": len(all_trials),
        "trials": all_trials[:limit]
    }
