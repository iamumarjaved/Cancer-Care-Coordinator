"""Analysis Service for managing patient analysis workflows."""

import asyncio
from typing import Dict, Optional, AsyncGenerator
from datetime import datetime
import logging
import uuid

from models.messages import AnalysisRequest, AnalysisProgress, AnalysisResult
from services.llm_service import LLMService
from services.patient_service import PatientService
from agents.orchestrator_agent import OrchestratorAgent, OrchestratorInput


class AnalysisService:
    """Service for managing patient analysis workflows.

    Handles:
    - Starting analysis requests
    - Tracking analysis progress
    - Retrieving analysis results
    - Streaming progress updates
    """

    def __init__(
        self,
        llm_service: LLMService,
        patient_service: PatientService,
        use_mock: bool = True
    ):
        """Initialize analysis service.

        Args:
            llm_service: LLM service instance
            patient_service: Patient service instance
            use_mock: Whether to use mock mode
        """
        self.llm_service = llm_service
        self.patient_service = patient_service
        self.use_mock = use_mock
        self.logger = logging.getLogger("service.analysis")

        # Create orchestrator agent
        self.orchestrator = OrchestratorAgent(
            llm_service=llm_service,
            patient_service=patient_service,
            use_mock=use_mock
        )

        # In-memory storage for analysis state
        self._analyses: Dict[str, dict] = {}

    async def start_analysis(self, request: AnalysisRequest) -> str:
        """Start a new analysis workflow.

        Args:
            request: Analysis request

        Returns:
            Request ID for tracking
        """
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request.patient_id}-{uuid.uuid4().hex[:6]}"

        self.logger.info(f"Starting analysis {request_id} for patient {request.patient_id}")

        # Initialize analysis state
        self._analyses[request_id] = {
            "request_id": request_id,
            "patient_id": request.patient_id,
            "request": request,
            "status": "initializing",
            "progress_percent": 0,
            "steps_completed": [],
            "steps_remaining": ["medical_history", "genomics", "clinical_trials", "evidence", "treatment", "synthesizing"],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None
        }

        # Start analysis in background
        asyncio.create_task(self._run_analysis(request_id, request))

        return request_id

    async def _run_analysis(self, request_id: str, request: AnalysisRequest):
        """Run the analysis workflow.

        Args:
            request_id: Analysis request ID
            request: Analysis request
        """
        try:
            # Create orchestrator input
            input_data = OrchestratorInput(
                patient_id=request.patient_id,
                include_trials=request.include_trials,
                include_evidence=True,
                user_questions=request.user_questions or []
            )

            # Update status
            self._analyses[request_id]["status"] = "in_progress"

            # Run orchestrator with streaming
            async for progress in self.orchestrator.run_streaming(input_data):
                # Update stored state
                self._analyses[request_id]["status"] = progress.status
                self._analyses[request_id]["progress_percent"] = progress.progress_percent
                self._analyses[request_id]["steps_completed"] = progress.steps_completed
                self._analyses[request_id]["steps_remaining"] = progress.steps_remaining

                if progress.error_message:
                    self._analyses[request_id]["error"] = progress.error_message

            # Get final result
            result = await self.orchestrator.run_analysis(input_data)

            # Store result
            self._analyses[request_id]["status"] = "completed"
            self._analyses[request_id]["progress_percent"] = 100
            self._analyses[request_id]["completed_at"] = datetime.now().isoformat()
            self._analyses[request_id]["result"] = result.result

            self.logger.info(f"Analysis {request_id} completed successfully")

        except Exception as e:
            self.logger.error(f"Analysis {request_id} failed: {str(e)}")
            self._analyses[request_id]["status"] = "error"
            self._analyses[request_id]["error"] = str(e)

    async def get_status(self, request_id: str) -> Optional[AnalysisProgress]:
        """Get current status of an analysis.

        Args:
            request_id: Analysis request ID

        Returns:
            AnalysisProgress or None if not found
        """
        if request_id not in self._analyses:
            return None

        state = self._analyses[request_id]

        return AnalysisProgress(
            request_id=request_id,
            patient_id=state["patient_id"],
            status=state["status"],
            current_step=state["steps_completed"][-1] if state["steps_completed"] else "initializing",
            progress_percent=state["progress_percent"],
            steps_completed=state["steps_completed"],
            steps_remaining=state["steps_remaining"],
            current_step_detail=self._get_step_detail(state["status"]),
            error_message=state.get("error")
        )

    async def get_results(self, request_id: str) -> Optional[AnalysisResult]:
        """Get results of a completed analysis.

        Args:
            request_id: Analysis request ID

        Returns:
            AnalysisResult or None if not found or not complete
        """
        if request_id not in self._analyses:
            return None

        state = self._analyses[request_id]

        if state["status"] != "completed":
            return None

        return state["result"]

    async def stream_progress(self, request_id: str) -> AsyncGenerator[AnalysisProgress, None]:
        """Stream progress updates for an analysis.

        Args:
            request_id: Analysis request ID

        Yields:
            AnalysisProgress updates
        """
        if request_id not in self._analyses:
            return

        last_status = None
        last_progress = -1

        while True:
            state = self._analyses.get(request_id)
            if not state:
                break

            current_status = state["status"]
            current_progress = state["progress_percent"]

            # Yield if status or progress changed
            if current_status != last_status or current_progress != last_progress:
                yield AnalysisProgress(
                    request_id=request_id,
                    patient_id=state["patient_id"],
                    status=current_status,
                    current_step=state["steps_completed"][-1] if state["steps_completed"] else "initializing",
                    progress_percent=current_progress,
                    steps_completed=state["steps_completed"],
                    steps_remaining=state["steps_remaining"],
                    current_step_detail=self._get_step_detail(current_status),
                    error_message=state.get("error")
                )

                last_status = current_status
                last_progress = current_progress

            # Exit if completed or error
            if current_status in ["completed", "error"]:
                break

            await asyncio.sleep(0.5)

    async def cancel_analysis(self, request_id: str) -> bool:
        """Cancel a running analysis.

        Args:
            request_id: Analysis request ID

        Returns:
            True if cancelled, False if not found or already complete
        """
        if request_id not in self._analyses:
            return False

        state = self._analyses[request_id]
        if state["status"] in ["completed", "error", "cancelled"]:
            return False

        state["status"] = "cancelled"
        state["error"] = "Analysis cancelled by user"
        self.logger.info(f"Analysis {request_id} cancelled")

        return True

    async def list_analyses(
        self,
        patient_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> list:
        """List analyses with optional filters.

        Args:
            patient_id: Filter by patient ID
            status: Filter by status

        Returns:
            List of analysis summaries
        """
        results = []

        for req_id, state in self._analyses.items():
            if patient_id and state["patient_id"] != patient_id:
                continue
            if status and state["status"] != status:
                continue

            results.append({
                "request_id": req_id,
                "patient_id": state["patient_id"],
                "status": state["status"],
                "progress_percent": state["progress_percent"],
                "started_at": state["started_at"],
                "completed_at": state.get("completed_at")
            })

        return results

    def _get_step_detail(self, status: str) -> str:
        """Get human-readable detail for status.

        Args:
            status: Current status

        Returns:
            Human-readable description
        """
        details = {
            "initializing": "Loading patient data...",
            "medical_history": "Analyzing medical history...",
            "genomics": "Interpreting genomic data...",
            "clinical_trials": "Matching to clinical trials...",
            "evidence": "Searching medical literature...",
            "treatment": "Generating treatment recommendations...",
            "synthesizing": "Synthesizing final report...",
            "completed": "Analysis complete",
            "error": "An error occurred",
            "cancelled": "Analysis cancelled",
            "in_progress": "Analysis in progress..."
        }
        return details.get(status, "Processing...")

    async def cleanup_old_analyses(self, max_age_hours: int = 24):
        """Clean up old completed analyses.

        Args:
            max_age_hours: Maximum age in hours
        """
        now = datetime.now()
        to_remove = []

        for req_id, state in self._analyses.items():
            if state["status"] in ["completed", "error", "cancelled"]:
                if state.get("completed_at"):
                    completed = datetime.fromisoformat(state["completed_at"])
                    age_hours = (now - completed).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(req_id)

        for req_id in to_remove:
            del self._analyses[req_id]

        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old analyses")
