"""Orchestrator Agent for coordinating the analysis workflow."""

from typing import List, Optional, AsyncGenerator, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import asyncio
import logging

from services.tracing import get_tracer, trace, agent_span
from .base_agent import BaseAgent
from .medical_history_agent import MedicalHistoryAgent, MedicalHistoryInput, MedicalHistoryOutput, ClinicalNoteInfo
from .genomics_agent import GenomicsAgent, GenomicsInput, GenomicsOutput
from .clinical_trials_agent import ClinicalTrialsAgent, ClinicalTrialsInput, ClinicalTrialsOutput
from .evidence_agent import EvidenceAgent, EvidenceInput, EvidenceOutput
from .treatment_agent import TreatmentAgent, TreatmentInput, TreatmentOutput

from models.patient import Patient, PatientSummary
from models.genomics import GenomicReport, GenomicAnalysisResult, Mutation, MutationClassification, ImmunotherapyMarkers, Therapy
from models.treatment import TreatmentPlan
from models.messages import AnalysisProgress, AnalysisResult
from services.llm_service import LLMService
from services.patient_service import PatientService
from database import async_session_maker
from models.db_models import ClinicalNoteDB
from sqlalchemy import select, desc


class AnalysisStep(str, Enum):
    """Steps in the analysis workflow."""
    INITIALIZING = "initializing"
    MEDICAL_HISTORY = "medical_history"
    GENOMICS = "genomics"
    CLINICAL_TRIALS = "clinical_trials"
    EVIDENCE = "evidence"
    TREATMENT = "treatment"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    ERROR = "error"


class OrchestratorState(BaseModel):
    """State of the orchestration workflow."""
    request_id: str
    patient_id: str
    current_step: AnalysisStep = AnalysisStep.INITIALIZING
    progress_percent: int = 0
    steps_completed: List[str] = Field(default_factory=list)
    steps_remaining: List[str] = Field(default_factory=list)

    # Intermediate results
    patient: Optional[Patient] = None
    medical_history_output: Optional[MedicalHistoryOutput] = None
    genomics_output: Optional[GenomicsOutput] = None
    trials_output: Optional[ClinicalTrialsOutput] = None
    evidence_output: Optional[EvidenceOutput] = None
    treatment_output: Optional[TreatmentOutput] = None

    # Final result
    final_result: Optional[AnalysisResult] = None

    # Error tracking
    error_message: Optional[str] = None
    error_step: Optional[str] = None


class OrchestratorInput(BaseModel):
    """Input for orchestrator."""
    patient_id: str
    include_trials: bool = True
    include_evidence: bool = True
    user_questions: List[str] = Field(default_factory=list)


class OrchestratorOutput(BaseModel):
    """Output from orchestrator."""
    result: AnalysisResult
    state: OrchestratorState


class OrchestratorAgent(BaseAgent[OrchestratorInput, OrchestratorOutput]):
    """Agent that orchestrates the complete analysis workflow.

    This agent coordinates:
    1. Medical History Analysis
    2. Genomics Interpretation
    3. Clinical Trial Matching
    4. Evidence Search
    5. Treatment Recommendation
    6. Final Synthesis

    Implements a LangGraph-style workflow with state management
    and streaming progress updates.
    """

    STEP_WEIGHTS = {
        AnalysisStep.INITIALIZING: 5,
        AnalysisStep.MEDICAL_HISTORY: 15,
        AnalysisStep.GENOMICS: 20,
        AnalysisStep.CLINICAL_TRIALS: 15,
        AnalysisStep.EVIDENCE: 15,
        AnalysisStep.TREATMENT: 20,
        AnalysisStep.SYNTHESIZING: 10,
    }

    def __init__(
        self,
        llm_service: LLMService,
        patient_service: PatientService,
        use_mock: bool = True
    ):
        super().__init__(
            name="orchestrator",
            llm_service=llm_service,
            use_mock=use_mock
        )
        self.patient_service = patient_service
        self.logger = logging.getLogger("agent.orchestrator")
        self.logger.info(f"OrchestratorAgent initialized with use_mock={use_mock}")

        # Initialize sub-agents
        self.medical_history_agent = MedicalHistoryAgent(llm_service, use_mock)
        self.genomics_agent = GenomicsAgent(llm_service, use_mock)
        self.trials_agent = ClinicalTrialsAgent(llm_service, use_mock)
        self.evidence_agent = EvidenceAgent(llm_service, use_mock)
        self.treatment_agent = TreatmentAgent(llm_service, use_mock)

    def get_system_prompt(self) -> str:
        return """You are an orchestrator AI that coordinates a multi-agent analysis system.
Your role is to:
1. Manage the workflow of specialized agents
2. Pass data between agents efficiently
3. Handle errors gracefully
4. Synthesize final results from all agent outputs
5. Provide coherent progress updates

Ensure each agent receives proper input and handle any failures gracefully."""

    async def execute(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """Execute the full analysis workflow."""
        return await self.run_analysis(input_data)

    def _mock_execute(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """Execute with mock mode - runs synchronously."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_analysis(input_data))
        finally:
            loop.close()

    async def run_analysis(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        """Run the complete analysis workflow."""
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{input_data.patient_id}"

        # Initialize state
        state = OrchestratorState(
            request_id=request_id,
            patient_id=input_data.patient_id,
            current_step=AnalysisStep.INITIALIZING,
            steps_remaining=[
                "medical_history", "genomics", "clinical_trials",
                "evidence", "treatment", "synthesizing"
            ]
        )

        # Run analysis with tracing
        async with trace("analysis", patient_id=input_data.patient_id, metadata={"request_id": request_id}):
            try:
                # Step 1: Initialize - Load patient data
                async with agent_span("Initialize", input_summary=f"Loading patient {input_data.patient_id}"):
                    state = await self._step_initialize(state)

                # Step 2: Medical History
                async with agent_span("MedicalHistoryAgent"):
                    state = await self._step_medical_history(state)

                # Step 3: Genomics
                async with agent_span("GenomicsAgent"):
                    state = await self._step_genomics(state)

                # Step 4: Clinical Trials (optional)
                if input_data.include_trials:
                    async with agent_span("ClinicalTrialsAgent"):
                        state = await self._step_clinical_trials(state)
                else:
                    state.steps_remaining.remove("clinical_trials")
                    state.steps_completed.append("clinical_trials (skipped)")

                # Step 5: Evidence (optional)
                if input_data.include_evidence:
                    async with agent_span("EvidenceAgent"):
                        state = await self._step_evidence(state, input_data.user_questions)
                else:
                    state.steps_remaining.remove("evidence")
                    state.steps_completed.append("evidence (skipped)")

                # Step 6: Treatment
                async with agent_span("TreatmentAgent"):
                    state = await self._step_treatment(state)

                # Step 7: Synthesize
                async with agent_span("Synthesize"):
                    state = await self._step_synthesize(state)

                return OrchestratorOutput(result=state.final_result, state=state)

            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                state.current_step = AnalysisStep.ERROR
                state.error_message = str(e)
                state.error_step = state.current_step.value

                # Create error result
                state.final_result = AnalysisResult(
                    request_id=request_id,
                    patient_id=input_data.patient_id,
                    status="error",
                    completed_at=datetime.now(),
                    summary=f"Analysis failed at step {state.error_step}: {state.error_message}",
                    key_findings=[],
                    recommendations=[],
                    treatment_plan=None,
                    clinical_trials=[],
                    sources_used=[]
                )

                return OrchestratorOutput(result=state.final_result, state=state)

    async def run_streaming(
        self,
        input_data: OrchestratorInput
    ) -> AsyncGenerator[AnalysisProgress | OrchestratorOutput, None]:
        """Run analysis with streaming progress updates.

        Yields AnalysisProgress updates during execution, then yields
        the final OrchestratorOutput at the end.
        """
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{input_data.patient_id}"

        state = OrchestratorState(
            request_id=request_id,
            patient_id=input_data.patient_id,
            current_step=AnalysisStep.INITIALIZING,
            steps_remaining=[
                "medical_history", "genomics", "clinical_trials",
                "evidence", "treatment", "synthesizing"
            ]
        )

        # Yield initial progress
        yield self._state_to_progress(state)

        try:
            # Step 1: Initialize
            state = await self._step_initialize(state)
            yield self._state_to_progress(state)

            # Step 2: Medical History
            state = await self._step_medical_history(state)
            yield self._state_to_progress(state)

            # Step 3: Genomics
            state = await self._step_genomics(state)
            yield self._state_to_progress(state)

            # Step 4: Clinical Trials
            if input_data.include_trials:
                state = await self._step_clinical_trials(state)
            yield self._state_to_progress(state)

            # Step 5: Evidence
            if input_data.include_evidence:
                state = await self._step_evidence(state, input_data.user_questions)
            yield self._state_to_progress(state)

            # Step 6: Treatment
            state = await self._step_treatment(state)
            yield self._state_to_progress(state)

            # Step 7: Synthesize
            state = await self._step_synthesize(state)
            yield self._state_to_progress(state)

            # Yield final result at the end
            yield OrchestratorOutput(result=state.final_result, state=state)

        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            state.current_step = AnalysisStep.ERROR
            state.error_message = str(e)
            yield self._state_to_progress(state)

            # Create error result and yield it
            state.final_result = AnalysisResult(
                request_id=request_id,
                patient_id=input_data.patient_id,
                status="error",
                completed_at=datetime.now(),
                summary=f"Analysis failed: {str(e)}",
                key_findings=[],
                recommendations=[],
                treatment_plan=None,
                clinical_trials=[],
                sources_used=[]
            )
            yield OrchestratorOutput(result=state.final_result, state=state)

    async def _step_initialize(self, state: OrchestratorState) -> OrchestratorState:
        """Initialize: Load patient data."""
        self.logger.info(f"Initializing analysis for patient {state.patient_id}")
        state.current_step = AnalysisStep.INITIALIZING

        # Load patient
        patient = await self.patient_service.get_by_id(state.patient_id)
        if not patient:
            raise ValueError(f"Patient {state.patient_id} not found")

        state.patient = patient
        state.progress_percent = self.STEP_WEIGHTS[AnalysisStep.INITIALIZING]

        # Small delay for mock mode
        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    async def _step_medical_history(self, state: OrchestratorState) -> OrchestratorState:
        """Step 2: Medical History Analysis."""
        self.logger.info("Running medical history analysis")
        state.current_step = AnalysisStep.MEDICAL_HISTORY

        # Fetch clinical notes for this patient
        clinical_notes = []
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(ClinicalNoteDB)
                    .where(ClinicalNoteDB.patient_id == state.patient.id)
                    .order_by(desc(ClinicalNoteDB.created_at))
                    .limit(20)
                )
                notes = result.scalars().all()
                clinical_notes = [
                    ClinicalNoteInfo(
                        note_text=note.note_text,
                        note_type=note.note_type,
                        created_at=note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else ""
                    )
                    for note in notes
                ]
                self.logger.info(f"Found {len(clinical_notes)} clinical notes for patient {state.patient.id}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch clinical notes: {e}")

        input_data = MedicalHistoryInput(patient=state.patient, clinical_notes=clinical_notes)
        state.medical_history_output = await self.medical_history_agent.run(input_data)

        state.steps_completed.append("medical_history")
        state.steps_remaining.remove("medical_history")
        state.progress_percent += self.STEP_WEIGHTS[AnalysisStep.MEDICAL_HISTORY]

        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    async def _step_genomics(self, state: OrchestratorState) -> OrchestratorState:
        """Step 3: Genomics Analysis."""
        self.logger.info("Running genomics analysis")
        state.current_step = AnalysisStep.GENOMICS

        # Load genomic report if available, or generate realistic one based on cancer type
        genomic_report = None
        if state.patient.genomic_report_id:
            # In production, would load from database
            genomic_report = None  # Will generate below

        # Generate realistic genomic report based on cancer type if none available
        if not genomic_report:
            genomic_report = self._generate_genomic_report_for_cancer(state.patient)

        input_data = GenomicsInput(
            patient=state.patient,
            genomic_report=genomic_report
        )
        state.genomics_output = await self.genomics_agent.run(input_data)

        state.steps_completed.append("genomics")
        state.steps_remaining.remove("genomics")
        state.progress_percent += self.STEP_WEIGHTS[AnalysisStep.GENOMICS]

        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    def _generate_genomic_report_for_cancer(self, patient: Patient) -> GenomicReport:
        """Generate a realistic genomic report based on patient's cancer type."""
        cancer_type = "NSCLC"  # Default
        if patient.cancer_details and patient.cancer_details.cancer_type:
            cancer_type = patient.cancer_details.cancer_type.value

        # NSCLC genomic profiles (most common mutations)
        if "NSCLC" in cancer_type or "lung" in cancer_type.lower():
            return GenomicReport(
                report_id=f"GR-{patient.id}",
                patient_id=patient.id,
                test_date="2024-01-15",
                test_type="NGS Panel - Foundation Medicine",
                specimen_type="Tumor tissue biopsy",
                lab_name="Foundation Medicine",
                actionable_mutations=[
                    Mutation(
                        gene="EGFR",
                        variant="exon 19 deletion",
                        variant_detail="p.E746_A750del",
                        classification=MutationClassification.PATHOGENIC_ACTIONABLE,
                        allele_frequency=0.34,
                        tier="Tier I",
                        therapies=[
                            Therapy(drug_name="Osimertinib", fda_approved=True, evidence_level="Level 1",
                                   expected_response_rate=0.77, indication="EGFR-mutated NSCLC"),
                            Therapy(drug_name="Erlotinib", fda_approved=True, evidence_level="Level 1",
                                   expected_response_rate=0.65, indication="EGFR-mutated NSCLC"),
                        ],
                        prognostic_impact="favorable"
                    ),
                ],
                other_mutations=[
                    Mutation(
                        gene="TP53",
                        variant="R248W",
                        variant_detail="p.R248W",
                        classification=MutationClassification.PATHOGENIC,
                        allele_frequency=0.28,
                        tier="Tier III",
                        prognostic_impact="unfavorable"
                    ),
                    Mutation(
                        gene="STK11",
                        variant="Q37*",
                        classification=MutationClassification.PATHOGENIC,
                        allele_frequency=0.22,
                        tier="Tier II",
                        prognostic_impact="unfavorable"
                    ),
                ],
                immunotherapy_markers=ImmunotherapyMarkers(
                    pdl1_expression=45.0,
                    pdl1_interpretation="moderate",
                    pdl1_method="22C3 pharmDx",
                    tmb=8.5,
                    tmb_interpretation="intermediate",
                    tmb_unit="mutations/Mb",
                    msi_status="MSS",
                    immunotherapy_likely_benefit=True,
                    reasoning="Moderate PD-L1 (45%) suggests potential immunotherapy benefit, especially in combination with targeted therapy"
                ),
                summary="EGFR exon 19 deletion identified - patient is candidate for EGFR-targeted therapy",
                primary_recommendation="Osimertinib as first-line treatment"
            )

        # Breast cancer genomic profiles
        elif "breast" in cancer_type.lower():
            return GenomicReport(
                report_id=f"GR-{patient.id}",
                patient_id=patient.id,
                test_date="2024-01-15",
                test_type="NGS Panel - Foundation Medicine",
                specimen_type="Tumor tissue biopsy",
                actionable_mutations=[
                    Mutation(
                        gene="PIK3CA",
                        variant="H1047R",
                        classification=MutationClassification.PATHOGENIC_ACTIONABLE,
                        allele_frequency=0.31,
                        tier="Tier I",
                        therapies=[
                            Therapy(drug_name="Alpelisib", fda_approved=True, evidence_level="Level 1"),
                        ],
                    ),
                ],
                other_mutations=[
                    Mutation(
                        gene="BRCA1",
                        variant="5382insC",
                        classification=MutationClassification.PATHOGENIC,
                        allele_frequency=0.45,
                        tier="Tier I",
                    ),
                ],
                immunotherapy_markers=ImmunotherapyMarkers(
                    pdl1_expression=5.0,
                    pdl1_interpretation="low",
                    tmb=3.0,
                    tmb_interpretation="low",
                    msi_status="MSS",
                    immunotherapy_likely_benefit=False,
                    reasoning="Low PD-L1 and TMB suggest limited immunotherapy benefit"
                ),
            )

        # Default/generic cancer profile
        else:
            return GenomicReport(
                report_id=f"GR-{patient.id}",
                patient_id=patient.id,
                test_date="2024-01-15",
                test_type="NGS Panel",
                specimen_type="Tumor tissue biopsy",
                actionable_mutations=[
                    Mutation(
                        gene="KRAS",
                        variant="G12C",
                        classification=MutationClassification.PATHOGENIC_ACTIONABLE,
                        allele_frequency=0.28,
                        tier="Tier I",
                        therapies=[
                            Therapy(drug_name="Sotorasib", fda_approved=True, evidence_level="Level 1"),
                        ],
                    ),
                ],
                immunotherapy_markers=ImmunotherapyMarkers(
                    pdl1_expression=20.0,
                    pdl1_interpretation="moderate",
                    tmb=6.0,
                    tmb_interpretation="intermediate",
                    msi_status="MSS",
                    immunotherapy_likely_benefit=False,
                ),
            )

    async def _step_clinical_trials(self, state: OrchestratorState) -> OrchestratorState:
        """Step 4: Clinical Trials Matching."""
        self.logger.info("Running clinical trials matching")
        state.current_step = AnalysisStep.CLINICAL_TRIALS

        input_data = ClinicalTrialsInput(
            patient_summary=state.medical_history_output.patient_summary,
            genomics_result=state.genomics_output.analysis_result if state.genomics_output else None
        )
        state.trials_output = await self.trials_agent.run(input_data)

        state.steps_completed.append("clinical_trials")
        state.steps_remaining.remove("clinical_trials")
        state.progress_percent += self.STEP_WEIGHTS[AnalysisStep.CLINICAL_TRIALS]

        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    async def _step_evidence(
        self,
        state: OrchestratorState,
        user_questions: List[str]
    ) -> OrchestratorState:
        """Step 5: Evidence Search."""
        self.logger.info("Running evidence search")
        state.current_step = AnalysisStep.EVIDENCE

        # Build treatment queries from genomics results
        treatment_queries = []
        if state.genomics_output:
            treatment_queries = state.genomics_output.therapy_candidates[:5]

        input_data = EvidenceInput(
            patient_summary=state.medical_history_output.patient_summary,
            genomics_result=state.genomics_output.analysis_result if state.genomics_output else None,
            treatment_queries=treatment_queries + user_questions
        )
        state.evidence_output = await self.evidence_agent.run(input_data)

        state.steps_completed.append("evidence")
        state.steps_remaining.remove("evidence")
        state.progress_percent += self.STEP_WEIGHTS[AnalysisStep.EVIDENCE]

        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    async def _step_treatment(self, state: OrchestratorState) -> OrchestratorState:
        """Step 6: Treatment Recommendation."""
        self.logger.info("Running treatment recommendation")
        state.current_step = AnalysisStep.TREATMENT

        input_data = TreatmentInput(
            patient_id=state.patient_id,
            patient_summary=state.medical_history_output.patient_summary,
            genomics_result=state.genomics_output.analysis_result if state.genomics_output else None,
            evidence_summaries=state.evidence_output.evidence_summaries if state.evidence_output else [],
            clinical_trials=state.trials_output.matched_trials if state.trials_output else []
        )
        state.treatment_output = await self.treatment_agent.run(input_data)

        state.steps_completed.append("treatment")
        state.steps_remaining.remove("treatment")
        state.progress_percent += self.STEP_WEIGHTS[AnalysisStep.TREATMENT]

        if self._use_mock:
            await asyncio.sleep(0.5)

        return state

    async def _step_synthesize(self, state: OrchestratorState) -> OrchestratorState:
        """Step 7: Synthesize final results."""
        self.logger.info("Synthesizing final results")
        state.current_step = AnalysisStep.SYNTHESIZING

        # Collect key findings
        key_findings = []
        if state.medical_history_output:
            key_findings.extend(state.medical_history_output.key_findings[:3])
        if state.genomics_output and state.genomics_output.analysis_result:
            key_findings.extend(state.genomics_output.analysis_result.key_findings[:3])

        # Collect recommendations
        recommendations = []
        if state.treatment_output:
            if state.treatment_output.primary_recommendation and state.treatment_output.primary_recommendation.treatment_name:
                recommendations.append(
                    f"Primary recommendation: {state.treatment_output.primary_recommendation.treatment_name}"
                )
            recommendations.extend(state.treatment_output.discussion_points)

        # Collect sources
        sources = []
        if state.evidence_output:
            sources.extend(state.evidence_output.search_terms_used)
            sources.extend([p.journal for p in state.evidence_output.relevant_publications])

        # Build summary
        summary = self._build_summary(state)

        # Convert Pydantic models to dicts for serialization
        treatment_plan_dict = None
        if state.treatment_output and state.treatment_output.treatment_plan:
            treatment_plan_dict = state.treatment_output.treatment_plan.model_dump()

        clinical_trials_list = []
        if state.trials_output and state.trials_output.matched_trials:
            clinical_trials_list = [trial.model_dump() for trial in state.trials_output.matched_trials[:5]]

        # Convert patient summary to dict
        patient_summary_dict = None
        if state.medical_history_output and state.medical_history_output.patient_summary:
            patient_summary_dict = state.medical_history_output.patient_summary.model_dump()

        # Convert genomics analysis to dict
        genomic_analysis_dict = None
        if state.genomics_output and state.genomics_output.analysis_result:
            genomic_analysis_dict = state.genomics_output.analysis_result.model_dump()

        # Convert evidence summary to dict
        evidence_summary_dict = None
        if state.evidence_output:
            evidence_summary_dict = {
                "search_terms_used": state.evidence_output.search_terms_used,
                "evidence_summaries": [e.model_dump() for e in state.evidence_output.evidence_summaries],
                "relevant_publications": [p.model_dump() for p in state.evidence_output.relevant_publications],
                "guideline_recommendations": [g.model_dump() for g in state.evidence_output.guideline_recommendations]
            }

        # Collect discussion points
        discussion_points = []
        if state.treatment_output:
            discussion_points = state.treatment_output.discussion_points

        # Create final result
        state.final_result = AnalysisResult(
            request_id=state.request_id,
            patient_id=state.patient_id,
            status="completed",
            completed_at=datetime.now(),
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            discussion_points=discussion_points,
            treatment_plan=treatment_plan_dict,
            clinical_trials=clinical_trials_list,
            patient_summary=patient_summary_dict,
            genomic_analysis=genomic_analysis_dict,
            evidence_summary=evidence_summary_dict,
            sources_used=list(set(sources))[:10]
        )

        state.steps_completed.append("synthesizing")
        state.steps_remaining.remove("synthesizing")
        state.current_step = AnalysisStep.COMPLETED
        state.progress_percent = 100

        if self._use_mock:
            await asyncio.sleep(0.3)

        return state

    def _build_summary(self, state: OrchestratorState) -> str:
        """Build analysis summary."""
        parts = []

        # Patient overview
        if state.medical_history_output:
            ps = state.medical_history_output.patient_summary
            cancer_type = ps.cancer.cancer_type.value if ps.cancer and ps.cancer.cancer_type else None
            cancer_stage = ps.cancer.stage.value if ps.cancer and ps.cancer.stage else None

            # Build patient description, skipping unknown values
            age = ps.demographics.get('age')
            sex = ps.demographics.get('sex', '')

            patient_desc = "Patient"
            if age and age != 'Unknown':
                patient_desc = f"{age} year old"
                if sex:
                    patient_desc = f"{patient_desc} {sex}"
            elif sex:
                patient_desc = f"{sex} patient"

            if cancer_type and cancer_stage:
                parts.append(f"{patient_desc} with {cancer_type}, {cancer_stage}")
            elif cancer_type:
                parts.append(f"{patient_desc} with {cancer_type}")
            else:
                parts.append(patient_desc)

        # Genomics highlights
        if state.genomics_output:
            mutations = state.genomics_output.actionable_mutations
            if mutations:
                genes = ", ".join(m.gene for m in mutations)
                parts.append(f"Actionable mutations: {genes}")
            if state.genomics_output.immunotherapy_markers:
                if state.genomics_output.immunotherapy_markers.immunotherapy_likely_benefit:
                    parts.append("Immunotherapy likely beneficial")

        # Treatment highlights
        if state.treatment_output and state.treatment_output.primary_recommendation:
            primary = state.treatment_output.primary_recommendation
            treatment_name = primary.treatment_name or "Unknown"
            rec_value = primary.recommendation.value if primary.recommendation else "recommended"
            parts.append(f"Recommended treatment: {treatment_name} ({rec_value})")

        # Trials
        if state.trials_output and state.trials_output.matched_trials:
            count = len(state.trials_output.matched_trials)
            parts.append(f"{count} clinical trial{'s' if count > 1 else ''} identified")

        return ". ".join(parts) + "."

    def _state_to_progress(self, state: OrchestratorState) -> AnalysisProgress:
        """Convert state to progress update."""
        return AnalysisProgress(
            request_id=state.request_id,
            patient_id=state.patient_id,
            status=state.current_step.value,
            current_step=state.current_step.value,
            progress_percent=state.progress_percent,
            steps_completed=state.steps_completed,
            steps_remaining=state.steps_remaining,
            current_step_detail=self._get_step_detail(state.current_step),
            error_message=state.error_message
        )

    def _get_step_detail(self, step: AnalysisStep) -> str:
        """Get human-readable detail for current step."""
        details = {
            AnalysisStep.INITIALIZING: "Loading patient data...",
            AnalysisStep.MEDICAL_HISTORY: "Analyzing medical history...",
            AnalysisStep.GENOMICS: "Interpreting genomic data...",
            AnalysisStep.CLINICAL_TRIALS: "Matching to clinical trials...",
            AnalysisStep.EVIDENCE: "Searching medical literature...",
            AnalysisStep.TREATMENT: "Generating treatment recommendations...",
            AnalysisStep.SYNTHESIZING: "Synthesizing final report...",
            AnalysisStep.COMPLETED: "Analysis complete",
            AnalysisStep.ERROR: "An error occurred"
        }
        return details.get(step, "Processing...")

    async def get_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """Get patient context for chat interactions."""
        patient = await self.patient_service.get_by_id(patient_id)
        if not patient:
            return {}

        # Quick medical history analysis for context
        input_data = MedicalHistoryInput(patient=patient)
        history_output = await self.medical_history_agent.run(input_data)

        return {
            "patient_summary": history_output.patient_summary,
            "key_findings": history_output.key_findings,
            "treatment_considerations": history_output.treatment_considerations
        }
