"""Analysis API Router."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, date
import asyncio
import uuid
import logging
import json
from enum import Enum


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and date objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def serialize_for_json(obj):
    """Recursively convert date/datetime/enum objects to JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj

from models.messages import AnalysisRequest, AnalysisProgress, AnalysisResult, AgentStatus
from services.llm_service import LLMService
from services.patient_service import PatientService
from services.vector_store_service import VectorStoreService
from services.email_service import get_email_service
from database import get_db, AsyncSession, async_session_maker
from models.db_models import AnalysisResultDB, PatientEventDB
from sqlalchemy import select
from agents.orchestrator_agent import OrchestratorAgent, OrchestratorInput
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()
patient_service = PatientService()
vector_store_service = VectorStoreService()

# Initialize orchestrator agent (with real LLM mode based on settings)
orchestrator_agent = OrchestratorAgent(
    llm_service=llm_service,
    patient_service=patient_service,
    use_mock=settings.USE_MOCK_LLM
)

# In-memory storage for analysis state (would be Redis/DB in production)
_analyses: Dict[str, Dict[str, Any]] = {}


class RunAnalysisRequest(BaseModel):
    """Request to run an analysis."""
    patient_id: str
    analysis_type: str = "full"
    include_trials: bool = True
    user_questions: list = []
    user_email: Optional[str] = None  # Email for notification


class RunAnalysisResponse(BaseModel):
    """Response after starting an analysis."""
    request_id: str
    patient_id: str
    status: str
    message: str


class AnalysisStatsResponse(BaseModel):
    """Response containing analysis statistics."""
    active_analyses: int
    completed_today: int
    clinical_notes_count: int
    active_list: List[Dict[str, Any]]


@router.get("/analysis/patient/{patient_id}/active")
async def get_active_analysis_for_patient(patient_id: str):
    """Get active (in-progress) analysis for a specific patient.

    Args:
        patient_id: The patient ID

    Returns:
        Active analysis info or null if none
    """
    for aid, state in _analyses.items():
        if state.get("patient_id") == patient_id and state.get("status") not in ["completed", "error"]:
            return {
                "request_id": aid,
                "patient_id": state.get("patient_id"),
                "status": state.get("status"),
                "progress_percent": state.get("progress_percent", 0),
                "current_step": state.get("current_step"),
                "current_step_detail": state.get("current_step_detail"),
                "steps_completed": state.get("steps_completed", []),
                "steps_remaining": state.get("steps_remaining", []),
            }
    return None


@router.post("/analysis/{request_id}/stop")
async def stop_analysis(request_id: str):
    """Stop/cancel a running analysis.

    Args:
        request_id: The analysis request ID

    Returns:
        Confirmation message

    Raises:
        404: Analysis not found
        400: Analysis already completed
    """
    if request_id not in _analyses:
        raise HTTPException(status_code=404, detail=f"Analysis {request_id} not found")

    state = _analyses[request_id]

    if state["status"] in ["completed", "error"]:
        raise HTTPException(status_code=400, detail="Analysis already finished")

    # Mark as cancelled
    state["status"] = "error"
    state["error_message"] = "Analysis cancelled by user"
    state["current_step_detail"] = "Cancelled"

    logger.info(f"Analysis {request_id} stopped by user")

    return {"message": "Analysis stopped", "request_id": request_id}


@router.get("/analysis/stats", response_model=AnalysisStatsResponse)
async def get_analysis_stats():
    """Get current analysis statistics.

    Returns:
        Statistics about active and recent analyses
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, func
    from models.db_models import AnalysisResultDB, ClinicalNoteDB
    from database import async_session_maker

    active = [
        {
            "request_id": aid,
            "patient_id": state.get("patient_id"),
            "status": state.get("status"),
            "progress_percent": state.get("progress_percent", 0),
            "current_step": state.get("current_step")
        }
        for aid, state in _analyses.items()
        if state.get("status") not in ["completed", "error"]
    ]

    # Query database for real stats
    completed_today_count = 0
    clinical_notes_count = 0

    try:
        async with async_session_maker() as db:
            # Count total completed analyses
            result = await db.execute(
                select(func.count(AnalysisResultDB.id))
                .where(AnalysisResultDB.status == "completed")
            )
            completed_today_count = result.scalar() or 0

            # Count all clinical notes
            result = await db.execute(
                select(func.count(ClinicalNoteDB.id))
            )
            clinical_notes_count = result.scalar() or 0
    except Exception:
        pass  # Use defaults if DB query fails

    return AnalysisStatsResponse(
        active_analyses=len(active),
        completed_today=completed_today_count,
        clinical_notes_count=clinical_notes_count,
        active_list=active
    )


@router.post("/analysis/run", response_model=RunAnalysisResponse)
async def run_analysis(request: RunAnalysisRequest):
    """Start a new AI analysis for a patient.

    Args:
        request: Analysis request parameters

    Returns:
        Analysis request ID and initial status
    """
    request_id = str(uuid.uuid4())

    # Initialize analysis state (step names match orchestrator agent)
    _analyses[request_id] = {
        "request_id": request_id,
        "patient_id": request.patient_id,
        "user_email": request.user_email,
        "status": "initializing",
        "current_step": "initializing",
        "current_step_detail": "Loading patient data...",
        "progress_percent": 0,
        "steps_completed": [],
        "steps_remaining": [
            "medical_history",
            "genomics",
            "clinical_trials",
            "evidence",
            "treatment",
            "synthesizing"
        ],
        "agent_statuses": {},
        "partial_results": {},
        "result": None,
        "error_message": None
    }

    # Start analysis in background (mock implementation)
    asyncio.create_task(_run_mock_analysis(request_id, request))

    return RunAnalysisResponse(
        request_id=request_id,
        patient_id=request.patient_id,
        status="initializing",
        message="Analysis started. Use /analysis/{request_id}/status to check progress."
    )


@router.get("/analysis/{request_id}/status", response_model=AnalysisProgress)
async def get_analysis_status(request_id: str):
    """Get the status of an analysis.

    Args:
        request_id: The analysis request ID

    Returns:
        Current analysis progress

    Raises:
        404: Analysis not found
    """
    if request_id not in _analyses:
        raise HTTPException(status_code=404, detail=f"Analysis {request_id} not found")

    state = _analyses[request_id]
    return AnalysisProgress(
        request_id=state["request_id"],
        patient_id=state["patient_id"],
        status=state["status"],
        current_step=state["current_step"],
        current_step_detail=state.get("current_step_detail", ""),
        steps_completed=state["steps_completed"],
        steps_remaining=state["steps_remaining"],
        agent_statuses=state["agent_statuses"],
        partial_results=state["partial_results"],
        progress_percent=state["progress_percent"],
        error_message=state.get("error_message")
    )


@router.get("/analysis/{request_id}/results")
async def get_analysis_results(request_id: str):
    """Get the results of a completed analysis.

    Args:
        request_id: The analysis request ID

    Returns:
        Complete analysis results

    Raises:
        404: Analysis not found
        400: Analysis not yet complete
    """
    if request_id not in _analyses:
        raise HTTPException(status_code=404, detail=f"Analysis {request_id} not found")

    state = _analyses[request_id]

    if state["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not yet complete. Current status: {state['status']}"
        )

    return state["result"]


@router.get("/analysis/{request_id}/stream")
async def analysis_stream_sse(request_id: str):
    """Server-Sent Events endpoint for streaming analysis progress.

    This endpoint streams analysis progress updates using SSE format,
    compatible with browser EventSource API.

    Args:
        request_id: The analysis request ID

    Returns:
        StreamingResponse with SSE format
    """
    async def event_generator():
        if request_id not in _analyses:
            yield f"data: {json.dumps({'error': f'Analysis {request_id} not found'})}\n\n"
            return

        last_progress = -1
        while True:
            state = _analyses.get(request_id)
            if not state:
                break

            # Send update if progress changed
            if state["progress_percent"] != last_progress:
                event_data = {
                    "request_id": request_id,
                    "patient_id": state["patient_id"],
                    "status": state["status"],
                    "current_step": state["current_step"],
                    "current_step_detail": state.get("current_step_detail", ""),
                    "progress_percent": state["progress_percent"],
                    "steps_completed": state["steps_completed"],
                    "steps_remaining": state["steps_remaining"],
                    "agent_statuses": {k: v.value if hasattr(v, 'value') else v for k, v in state.get("agent_statuses", {}).items()},
                    "partial_results": state.get("partial_results", {}),
                    "error_message": state.get("error_message")
                }
                yield f"data: {json.dumps(event_data, cls=DateTimeEncoder)}\n\n"
                last_progress = state["progress_percent"]

            # Check if complete
            if state["status"] == "completed":
                result_data = {
                    "request_id": request_id,
                    "patient_id": state["patient_id"],
                    "status": "completed",
                    "progress_percent": 100,
                    "result": state.get("result")
                }
                yield f"data: {json.dumps(result_data, cls=DateTimeEncoder)}\n\n"
                break
            elif state["status"] == "error":
                error_data = {
                    "request_id": request_id,
                    "status": "error",
                    "error_message": state.get("error_message", "Analysis failed")
                }
                yield f"data: {json.dumps(error_data, cls=DateTimeEncoder)}\n\n"
                break

            await asyncio.sleep(0.5)  # Poll interval

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.websocket("/analysis/{request_id}/ws")
async def analysis_stream_ws(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for streaming analysis progress.

    Args:
        websocket: WebSocket connection
        request_id: The analysis request ID
    """
    await websocket.accept()

    try:
        if request_id not in _analyses:
            await websocket.send_json({
                "type": "error",
                "message": f"Analysis {request_id} not found"
            })
            await websocket.close()
            return

        # Stream progress updates
        last_progress = -1
        while True:
            state = _analyses.get(request_id)
            if not state:
                break

            # Send update if progress changed
            if state["progress_percent"] != last_progress:
                await websocket.send_json({
                    "type": "progress",
                    "request_id": request_id,
                    "status": state["status"],
                    "current_step": state["current_step"],
                    "progress_percent": state["progress_percent"],
                    "steps_completed": state["steps_completed"],
                    "agent_statuses": {k: v.value if hasattr(v, 'value') else v for k, v in state["agent_statuses"].items()}
                })
                last_progress = state["progress_percent"]

            # Check if complete
            if state["status"] in ["completed", "error"]:
                await websocket.send_json({
                    "type": "completed" if state["status"] == "completed" else "error",
                    "request_id": request_id,
                    "result": state.get("result")
                })
                break

            await asyncio.sleep(0.5)  # Poll interval

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for analysis {request_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Oncology Analysis System Prompt
ONCOLOGY_ANALYSIS_PROMPT = """You are an expert oncology clinical decision support system. You are analyzing a cancer patient's data to provide evidence-based treatment recommendations.

Based on the patient information provided, generate a comprehensive analysis in the following JSON format:

{
    "summary": "A 2-3 sentence summary of the clinical picture and key recommendation",
    "key_findings": ["List of 4-6 key clinical findings relevant to treatment decisions"],
    "recommendations": ["List of 3-5 specific, actionable treatment recommendations"],
    "discussion_points": ["List of 3-4 topics to discuss with the patient/care team"],
    "treatment_options": [
        {
            "name": "Treatment name (e.g., Drug name or regimen)",
            "type": "Treatment type (e.g., Targeted Therapy, Immunotherapy, Chemotherapy)",
            "recommendation_level": "strongly_recommended|recommended|consider|not_recommended",
            "rationale": "Why this treatment is recommended for this patient",
            "expected_efficacy": "Expected outcomes (e.g., PFS, response rate)",
            "side_effects": ["Common side effects"],
            "monitoring_required": ["Required monitoring"],
            "contraindications": ["Any contraindications for this patient"],
            "drug_interactions": ["Relevant drug interactions"]
        }
    ],
    "clinical_trials": [
        {
            "nct_id": "NCT number if known, or 'Search recommended'",
            "title": "Trial title or description",
            "phase": "Phase I/II/III",
            "status": "Recruiting",
            "match_score": 0.85,
            "match_reasons": ["Why this trial matches the patient"],
            "brief_summary": "Brief description of the trial"
        }
    ],
    "sources_used": ["List of guideline sources referenced (e.g., NCCN Guidelines, OncoKB)"]
}

Important guidelines:
1. Be specific to the patient's cancer type, stage, and biomarkers
2. Consider comorbidities and organ function when recommending treatments
3. Cite evidence levels (NCCN Category 1, 2A, 2B) when applicable
4. Include dose adjustments needed for renal/hepatic impairment
5. Prioritize targeted therapies for actionable mutations
6. Always recommend clinical trial consideration for appropriate patients
7. Be conservative and always recommend oncology team consultation

Respond ONLY with the JSON object, no additional text."""


def _format_patient_for_analysis(patient) -> str:
    """Format patient data for LLM analysis prompt."""
    from datetime import date

    # Calculate age
    today = date.today()
    dob = patient.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # Build patient summary
    lines = [
        f"=== PATIENT CLINICAL SUMMARY ===",
        f"",
        f"DEMOGRAPHICS:",
        f"- Age: {age} years old",
        f"- Sex: {patient.sex}",
        f"- ECOG Performance Status: {patient.ecog_status.value if patient.ecog_status else 'Not recorded'}",
    ]

    # Cancer details
    if patient.cancer_details:
        cd = patient.cancer_details
        lines.extend([
            f"",
            f"CANCER DIAGNOSIS:",
            f"- Cancer Type: {cd.cancer_type.value}",
            f"- Subtype: {cd.subtype or 'Not specified'}",
            f"- Stage: {cd.stage.value}",
            f"- TNM Staging: {cd.tnm_staging or 'Not available'}",
            f"- Primary Site: {cd.primary_site}",
            f"- Histology: {cd.histology or 'Not specified'}",
            f"- Diagnosis Date: {cd.diagnosis_date.isoformat() if cd.diagnosis_date else 'Not recorded'}",
        ])
        if cd.metastases:
            lines.append(f"- Metastatic Sites: {', '.join(cd.metastases)}")

    # Comorbidities
    if patient.comorbidities:
        lines.extend([
            f"",
            f"COMORBIDITIES:",
        ])
        for comorb in patient.comorbidities:
            implications = f" (Treatment implications: {', '.join(comorb.treatment_implications)})" if comorb.treatment_implications else ""
            lines.append(f"- {comorb.condition} ({comorb.severity}){implications}")

    # Organ function
    if patient.organ_function:
        lines.extend([
            f"",
            f"ORGAN FUNCTION:",
        ])
        for organ in patient.organ_function:
            values = ", ".join([f"{k}: {v}" for k, v in organ.key_values.items()]) if organ.key_values else ""
            lines.append(f"- {organ.organ}: {organ.status} {f'({values})' if values else ''}")

    # Medications
    if patient.current_medications:
        lines.extend([
            f"",
            f"CURRENT MEDICATIONS:",
        ])
        for med in patient.current_medications:
            lines.append(f"- {med}")

    # Smoking history
    if patient.smoking_status:
        lines.extend([
            f"",
            f"SMOKING HISTORY:",
            f"- Status: {patient.smoking_status}",
            f"- Pack Years: {patient.pack_years or 'Not recorded'}",
        ])

    # Allergies
    if patient.allergies:
        lines.extend([
            f"",
            f"ALLERGIES:",
        ])
        for allergy in patient.allergies:
            lines.append(f"- {allergy}")

    return "\n".join(lines)


async def _run_orchestrator_analysis(request_id: str, request: RunAnalysisRequest):
    """Run analysis using OrchestratorAgent with all 7 specialized agents.

    This uses the multi-agent system where:
    - OrchestratorAgent coordinates the workflow
    - MedicalHistoryAgent analyzes patient medical history
    - GenomicsAgent interprets genomic/mutation data
    - ClinicalTrialsAgent matches patient to clinical trials
    - EvidenceAgent retrieves medical literature
    - TreatmentAgent generates treatment recommendations

    Args:
        request_id: The analysis request ID
        request: The analysis request
    """
    from agents.orchestrator_agent import OrchestratorOutput

    state = _analyses[request_id]
    state["status"] = "in_progress"
    state["started_at"] = datetime.now().isoformat()

    orchestrator_output = None

    try:
        logger.info(f"Starting orchestrator analysis for patient {request.patient_id}")

        # Create orchestrator input
        orchestrator_input = OrchestratorInput(
            patient_id=request.patient_id,
            include_trials=request.include_trials,
            include_evidence=True,
            user_questions=request.user_questions or []
        )

        # Stream progress from orchestrator - final item is OrchestratorOutput
        async for item in orchestrator_agent.run_streaming(orchestrator_input):
            # Check if this is the final result
            if isinstance(item, OrchestratorOutput):
                orchestrator_output = item
                logger.info(f"Analysis {request_id}: Received final result")
                continue

            # Otherwise it's a progress update
            progress = item
            state["status"] = progress.status
            state["current_step"] = progress.current_step
            state["current_step_detail"] = progress.current_step_detail
            state["progress_percent"] = progress.progress_percent
            state["steps_completed"] = progress.steps_completed
            state["steps_remaining"] = progress.steps_remaining

            # Update agent statuses
            for step in progress.steps_completed:
                state["agent_statuses"][step] = AgentStatus.COMPLETED
            if progress.current_step and progress.status not in ["completed", "error"]:
                state["agent_statuses"][progress.current_step] = AgentStatus.PROCESSING

            # Log progress
            logger.info(f"Analysis {request_id}: {progress.current_step} ({progress.progress_percent}%)")

            if progress.error_message:
                state["error_message"] = progress.error_message

        # Check we got the final result
        if not orchestrator_output:
            raise RuntimeError("Orchestrator did not return final result")

        final_result = orchestrator_output.result
        logger.info(f"Analysis {request_id} - final_result.status: {final_result.status}")

        # Check if the orchestrator returned an error status
        if final_result.status == "error":
            logger.error(f"Analysis {request_id} failed: {final_result.summary}")
            state["status"] = "error"
            state["error_message"] = final_result.summary
            state["current_step"] = "error"
            state["current_step_detail"] = final_result.summary

            # Save failed analysis to database with error status
            try:
                completed_at = datetime.now()
                async with async_session_maker() as db:
                    analysis_db = AnalysisResultDB(
                        patient_id=request.patient_id,
                        analysis_type=request.analysis_type,
                        status="error",
                        result_data={"error": final_result.summary},
                        sources_used=[],
                        confidence_score=0.0,
                        started_at=datetime.fromisoformat(state.get("started_at", completed_at.isoformat())),
                        completed_at=completed_at
                    )
                    db.add(analysis_db)
                    await db.commit()
                    logger.info(f"Saved failed analysis {request_id} to database")
            except Exception as db_error:
                logger.error(f"Failed to save failed analysis to database: {db_error}")
            return  # Don't continue to "completed" flow

        # Convert to dict for storage - only for successful analyses
        completed_at = datetime.now()
        result = {
            "request_id": request_id,
            "patient_id": request.patient_id,
            "status": "completed",
            "completed_at": completed_at.isoformat(),
            "summary": final_result.summary,
            "key_findings": final_result.key_findings,
            "recommendations": final_result.recommendations,
            "discussion_points": final_result.discussion_points,
            "sources_used": final_result.sources_used,
            # Include intermediate results for tabs
            "patient_summary": final_result.patient_summary,
            "genomic_analysis": final_result.genomic_analysis,
            "clinical_trials": final_result.clinical_trials,
            "evidence_summary": final_result.evidence_summary,
            "treatment_plan": final_result.treatment_plan,
        }

        state["result"] = result
        state["status"] = "completed"
        state["progress_percent"] = 100
        state["current_step"] = "completed"
        state["current_step_detail"] = "Analysis complete"

        logger.info(f"Analysis {request_id} completed successfully via orchestrator")

        # Send email notification if user_email is provided
        user_email = state.get("user_email")
        logger.info(f"Analysis {request_id} - user_email from state: {user_email}")
        if user_email:
            try:
                email_service = get_email_service()
                # Get patient name for email
                patient = await patient_service.get_by_id(request.patient_id)
                patient_name = f"{patient.first_name} {patient.last_name}" if patient else request.patient_id

                # Build analysis summary for email
                analysis_summary = {
                    "treatment_recommendations": [],
                    "clinical_trials_count": 0,
                    "summary": final_result.summary or "",
                    "key_findings": final_result.key_findings[:5] if final_result.key_findings else []
                }

                # Extract treatment recommendations from the recommendations list
                if final_result.recommendations:
                    for i, rec in enumerate(final_result.recommendations[:3]):
                        analysis_summary["treatment_recommendations"].append({
                            "name": rec if isinstance(rec, str) else str(rec),
                            "confidence_score": 0.9 - (i * 0.05)  # Descending confidence
                        })

                # Also try to get from treatment_plan if available
                if not analysis_summary["treatment_recommendations"] and final_result.treatment_plan:
                    treatment_plan = final_result.treatment_plan
                    # treatment_plan is a dict, check for treatment_options
                    if isinstance(treatment_plan, dict):
                        options = treatment_plan.get("treatment_options", []) or treatment_plan.get("primary_recommendations", [])
                        for i, opt in enumerate(options[:3]):
                            if isinstance(opt, dict):
                                analysis_summary["treatment_recommendations"].append({
                                    "name": opt.get("name") or opt.get("treatment_name", "Treatment Option"),
                                    "confidence_score": opt.get("confidence_score") or opt.get("confidence", 0.85)
                                })
                            else:
                                analysis_summary["treatment_recommendations"].append({
                                    "name": str(opt),
                                    "confidence_score": 0.85
                                })

                # Extract clinical trials count - it's a list directly
                if final_result.clinical_trials:
                    if isinstance(final_result.clinical_trials, list):
                        analysis_summary["clinical_trials_count"] = len(final_result.clinical_trials)
                    elif hasattr(final_result.clinical_trials, "matched_trials"):
                        analysis_summary["clinical_trials_count"] = len(final_result.clinical_trials.matched_trials)

                await email_service.send_analysis_complete_notification(
                    to_email=user_email,
                    patient_name=patient_name,
                    patient_id=request.patient_id,
                    analysis_summary=analysis_summary
                )
                logger.info(f"Sent analysis completion email to {user_email}")
            except Exception as email_error:
                logger.error(f"Failed to send analysis completion email: {email_error}")

        # Save to database
        analysis_id = str(uuid.uuid4())
        try:
            async with async_session_maker() as db:
                # Serialize result to handle date/datetime objects
                serialized_result = serialize_for_json(result)
                analysis_db = AnalysisResultDB(
                    id=analysis_id,
                    patient_id=request.patient_id,
                    analysis_type=request.analysis_type,
                    status="completed",
                    result_data=serialized_result,
                    sources_used=serialized_result.get("sources_used", []),
                    confidence_score=0.85,
                    started_at=datetime.fromisoformat(state.get("started_at", completed_at.isoformat())),
                    completed_at=completed_at
                )
                db.add(analysis_db)

                # Create patient event for timeline
                event = PatientEventDB(
                    id=str(uuid.uuid4()),
                    patient_id=request.patient_id,
                    event_type="analysis",
                    event_date=completed_at,
                    title=f"Analysis Completed: {request.analysis_type}",
                    description=serialized_result.get("summary", "Analysis completed successfully"),
                    reference_type="analysis",
                    reference_id=analysis_id
                )
                db.add(event)

                await db.commit()
                logger.info(f"Saved analysis {request_id} to database")

                # Index results in vector store for RAG
                try:
                    indexed = await vector_store_service.index_analysis_results(
                        patient_id=request.patient_id,
                        analysis_id=analysis_id,
                        analysis_data=serialized_result
                    )
                    logger.info(f"Indexed analysis results for RAG: {indexed}")
                except Exception as index_error:
                    logger.error(f"Failed to index analysis results: {index_error}")

        except Exception as db_error:
            logger.error(f"Failed to save analysis to database: {db_error}")

    except Exception as e:
        logger.error(f"Analysis {request_id} failed: {e}", exc_info=True)
        state["status"] = "error"
        state["error_message"] = str(e)
        state["current_step_detail"] = f"Error: {str(e)}"

        # Mark current step as failed
        current = state.get("current_step")
        if current and current != "completed":
            state["agent_statuses"][current] = AgentStatus.ERROR


async def _run_mock_analysis(request_id: str, request: RunAnalysisRequest):
    """Run analysis - uses orchestrator by default.

    Args:
        request_id: The analysis request ID
        request: The analysis request
    """
    await _run_orchestrator_analysis(request_id, request)


@router.get("/analysis/patient/{patient_id}/history")
async def get_patient_analysis_history(patient_id: str, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get analysis history for a patient.

    Args:
        patient_id: The patient ID
        limit: Maximum number of results to return
        db: Database session

    Returns:
        List of past analyses for the patient
    """
    result = await db.execute(
        select(AnalysisResultDB)
        .where(AnalysisResultDB.patient_id == patient_id)
        .order_by(AnalysisResultDB.created_at.desc())
        .limit(limit)
    )
    analyses = result.scalars().all()

    return {
        "patient_id": patient_id,
        "total": len(analyses),
        "analyses": [
            {
                "id": a.id,
                "analysis_type": a.analysis_type,
                "status": a.status,
                "summary": a.result_data.get("summary", "") if a.result_data else "",
                "key_findings": a.result_data.get("key_findings", []) if a.result_data else [],
                "confidence_score": a.confidence_score,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in analyses
        ]
    }


# ============== Email Notification Endpoints ==============

class PatientEventNotificationRequest(BaseModel):
    """Request for patient file opened/closed notification."""
    patient_id: str
    user_email: str


class EmailTestRequest(BaseModel):
    """Request for testing email."""
    to_email: str
    email_type: str = "test"  # test, analysis_complete, patient_opened, patient_closed


@router.post("/notifications/patient-opened")
async def notify_patient_opened(request: PatientEventNotificationRequest):
    """Send notification when patient file is opened.

    Args:
        request: Patient ID and user email

    Returns:
        Success status
    """
    try:
        email_service = get_email_service()
        if not email_service.is_enabled:
            return {"success": False, "message": "Email service is disabled"}

        # Get patient info
        patient = await patient_service.get_by_id(request.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {request.patient_id} not found")

        patient_name = f"{patient.first_name} {patient.last_name}"

        success = await email_service.send_patient_opened_notification(
            to_email=request.user_email,
            patient_name=patient_name,
            patient_id=request.patient_id
        )

        return {
            "success": success,
            "message": "Patient opened notification sent" if success else "Failed to send notification"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send patient opened notification: {e}")
        return {"success": False, "message": str(e)}


@router.post("/notifications/patient-closed")
async def notify_patient_closed(request: PatientEventNotificationRequest):
    """Send notification when patient file is closed.

    Args:
        request: Patient ID and user email

    Returns:
        Success status
    """
    try:
        email_service = get_email_service()
        if not email_service.is_enabled:
            return {"success": False, "message": "Email service is disabled"}

        # Get patient info
        patient = await patient_service.get_by_id(request.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {request.patient_id} not found")

        patient_name = f"{patient.first_name} {patient.last_name}"

        success = await email_service.send_patient_closed_notification(
            to_email=request.user_email,
            patient_name=patient_name,
            patient_id=request.patient_id
        )

        return {
            "success": success,
            "message": "Patient closed notification sent" if success else "Failed to send notification"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send patient closed notification: {e}")
        return {"success": False, "message": str(e)}


@router.post("/notifications/test")
async def test_email_notification(request: EmailTestRequest):
    """Test email notification sending.

    Args:
        request: Email test parameters

    Returns:
        Success status and details
    """
    try:
        email_service = get_email_service()

        if not email_service.is_enabled:
            return {
                "success": False,
                "message": "Email service is disabled. Check SENDGRID_API_KEY and SENDGRID_FROM_EMAIL in .env"
            }

        # Get a sample patient for testing
        sample_patient_id = "P1764922232566"  # Default test patient
        patient = await patient_service.get_by_id(sample_patient_id)
        patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Test Patient"

        if request.email_type == "analysis_complete":
            # Test analysis complete email
            analysis_summary = {
                "treatment_recommendations": [
                    {"name": "Osimertinib (Tagrisso)", "confidence_score": 0.95},
                    {"name": "Clinical Trial MARIPOSA-2", "confidence_score": 0.85},
                    {"name": "Erlotinib + Chemotherapy", "confidence_score": 0.75}
                ],
                "clinical_trials_count": 8
            }
            success = await email_service.send_analysis_complete_notification(
                to_email=request.to_email,
                patient_name=patient_name,
                patient_id=sample_patient_id,
                analysis_summary=analysis_summary
            )
        elif request.email_type == "patient_opened":
            success = await email_service.send_patient_opened_notification(
                to_email=request.to_email,
                patient_name=patient_name,
                patient_id=sample_patient_id
            )
        elif request.email_type == "patient_closed":
            success = await email_service.send_patient_closed_notification(
                to_email=request.to_email,
                patient_name=patient_name,
                patient_id=sample_patient_id
            )
        else:
            # Default test email
            success = await email_service.send_email(
                to_email=request.to_email,
                subject="Cancer Care Coordinator - Test Email",
                html_content=email_service._get_base_template("""
                    <div style="text-align: center; margin-bottom: 24px;">
                        <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 600;">
                            Test Email
                        </h2>
                        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">
                            This is a test email from Cancer Care Coordinator.
                        </p>
                    </div>
                    <p style="color: #334155; font-size: 14px; line-height: 1.6;">
                        If you received this email, your SendGrid configuration is working correctly!
                    </p>
                """)
            )

        return {
            "success": success,
            "message": f"Test email ({request.email_type}) sent to {request.to_email}" if success else "Failed to send test email",
            "email_enabled": email_service.is_enabled
        }

    except Exception as e:
        logger.error(f"Test email failed: {e}")
        return {
            "success": False,
            "message": str(e),
            "email_enabled": False
        }
