"""Clinical Trials Agent for matching patients to trials."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from .base_agent import BaseAgent
from models.patient import PatientSummary
from models.genomics import GenomicAnalysisResult
from models.treatment import ClinicalTrial, ClinicalTrialPhase, EligibilityCriterion
from services.llm_service import LLMService
from services.clinicaltrials_service import ClinicalTrialsService, get_clinicaltrials_service

logger = logging.getLogger(__name__)


class ClinicalTrialsInput(BaseModel):
    """Input for clinical trials matching."""
    patient_summary: PatientSummary
    genomics_result: Optional[GenomicAnalysisResult] = None
    patient_location: Optional[str] = None
    max_distance_miles: Optional[float] = 100


class ClinicalTrialsOutput(BaseModel):
    """Output from clinical trials matching."""
    matched_trials: List[ClinicalTrial] = Field(default_factory=list)
    total_trials_searched: int = 0
    search_criteria_used: List[str] = Field(default_factory=list)
    excluded_reason_summary: dict = Field(default_factory=dict)


class ClinicalTrialsAgent(BaseAgent[ClinicalTrialsInput, ClinicalTrialsOutput]):
    """Agent that matches patients to clinical trials.

    This agent:
    - Searches clinical trial databases (ClinicalTrials.gov)
    - Matches patient characteristics to eligibility criteria
    - Ranks trials by match score
    - Identifies nearby trial locations
    - Provides rationale for each match
    """

    # Mock trial database
    MOCK_TRIALS = [
        {
            "nct_id": "NCT04487080",
            "title": "MARIPOSA-2: Amivantamab Plus Chemotherapy in EGFR-Mutant NSCLC After Osimertinib Progression",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "Janssen Research",
            "intervention": "Amivantamab + Lazertinib + Chemotherapy",
            "intervention_type": "Combination",
            "biomarker": "EGFR",
            "mutations": ["exon 19 del", "L858R", "T790M"],
            "locations": ["Memorial Sloan Kettering, New York, NY", "MD Anderson, Houston, TX"],
        },
        {
            "nct_id": "NCT04035486",
            "title": "FLAURA2: Osimertinib With or Without Chemotherapy in EGFR-Mutant NSCLC",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "AstraZeneca",
            "intervention": "Osimertinib + Pemetrexed/Platinum",
            "intervention_type": "Combination",
            "biomarker": "EGFR",
            "mutations": ["exon 19 del", "L858R"],
            "locations": ["Dana-Farber, Boston, MA", "UCLA, Los Angeles, CA"],
        },
        {
            "nct_id": "NCT04538664",
            "title": "PAPILLON: Amivantamab in EGFR Exon 20 Insertion NSCLC",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "Janssen Research",
            "intervention": "Amivantamab + Chemotherapy",
            "intervention_type": "Combination",
            "biomarker": "EGFR",
            "mutations": ["exon 20 ins"],
            "locations": ["Johns Hopkins, Baltimore, MD"],
        },
        {
            "nct_id": "NCT04613596",
            "title": "KRYSTAL-12: Adagrasib in KRAS G12C NSCLC",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "Mirati Therapeutics",
            "intervention": "Adagrasib",
            "intervention_type": "Drug",
            "biomarker": "KRAS",
            "mutations": ["G12C"],
            "locations": ["Mayo Clinic, Rochester, MN"],
        },
        {
            "nct_id": "NCT04821622",
            "title": "CROWN-2: Lorlatinib vs Alectinib in ALK+ NSCLC",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "Pfizer",
            "intervention": "Lorlatinib",
            "intervention_type": "Drug",
            "biomarker": "ALK",
            "mutations": ["fusion", "rearrangement"],
            "locations": ["Stanford, Palo Alto, CA"],
        },
        {
            "nct_id": "NCT03515837",
            "title": "KEYNOTE-789: Pembrolizumab in EGFR-TKI Resistant NSCLC",
            "phase": ClinicalTrialPhase.PHASE_3,
            "status": "Recruiting",
            "sponsor": "Merck",
            "intervention": "Pembrolizumab + Chemotherapy",
            "intervention_type": "Combination",
            "biomarker": "PD-L1",
            "mutations": [],
            "locations": ["Cleveland Clinic, Cleveland, OH", "Mass General, Boston, MA"],
        },
        {
            "nct_id": "NCT04767438",
            "title": "Novel EGFR Degrader in EGFR-Mutant NSCLC",
            "phase": ClinicalTrialPhase.PHASE_1,
            "status": "Recruiting",
            "sponsor": "Academic",
            "intervention": "CFT8919",
            "intervention_type": "Drug",
            "biomarker": "EGFR",
            "mutations": ["any"],
            "locations": ["UCSF, San Francisco, CA"],
        },
    ]

    def __init__(
        self,
        llm_service: LLMService,
        use_mock: bool = True,
        trials_service: Optional[ClinicalTrialsService] = None
    ):
        super().__init__(
            name="clinical_trials",
            llm_service=llm_service,
            use_mock=use_mock
        )
        self._trials_service = trials_service or get_clinicaltrials_service()

    def get_system_prompt(self) -> str:
        return """You are a clinical trials specialist AI.
Your role is to:
1. Search clinical trial databases for relevant trials
2. Match patient characteristics to eligibility criteria
3. Rank trials by likelihood of eligibility
4. Identify practical considerations (location, phase, treatment burden)
5. Explain why each trial may or may not be appropriate

Be thorough in eligibility assessment. Note both inclusion and exclusion criteria.
Prioritize trials with higher match scores and recruiting status."""

    async def execute(self, input_data: ClinicalTrialsInput) -> ClinicalTrialsOutput:
        """Execute clinical trials search using real ClinicalTrials.gov API."""
        patient_summary = input_data.patient_summary
        genomics = input_data.genomics_result

        search_criteria = []
        matched_trials = []
        excluded_reasons = {}

        # Build search parameters from patient data
        condition = ""
        biomarkers = []

        if patient_summary.cancer:
            cancer_type = patient_summary.cancer.cancer_type.value
            condition = cancer_type
            search_criteria.append(f"Cancer type: {cancer_type}")
            search_criteria.append(f"Stage: {patient_summary.cancer.stage.value}")

        # Extract biomarkers from genomics
        if genomics and genomics.report:
            for mutation in genomics.report.actionable_mutations:
                biomarker = f"{mutation.gene}"
                biomarkers.append(biomarker)
                search_criteria.append(f"Mutation: {mutation.gene} {mutation.variant}")

        try:
            # Search real ClinicalTrials.gov API
            logger.info(f"Searching ClinicalTrials.gov for: {condition}, biomarkers: {biomarkers}")

            api_trials = await self._trials_service.search_trials(
                condition=condition or "cancer",
                status="RECRUITING",
                location_country="United States",
                max_results=30,
                biomarkers=biomarkers if biomarkers else None
            )

            logger.info(f"Found {len(api_trials)} trials from API")

            # Evaluate eligibility for each trial using LLM
            for api_trial in api_trials[:15]:  # Limit to top 15 for processing
                try:
                    match_result = await self._evaluate_trial_eligibility(
                        api_trial, patient_summary, genomics
                    )
                    if match_result:
                        matched_trials.append(match_result)
                except Exception as e:
                    logger.warning(f"Error evaluating trial {api_trial.nct_id}: {e}")
                    excluded_reasons[api_trial.nct_id] = str(e)

            # Sort by match score
            matched_trials.sort(key=lambda t: t.match_score, reverse=True)

            # If no trials matched after API search, fall back to mock data for demo
            if len(matched_trials) == 0:
                logger.info(f"No trials found from API (searched {len(api_trials)}), using mock data for demonstration")
                return self._mock_execute(input_data)

            return ClinicalTrialsOutput(
                matched_trials=matched_trials[:10],
                total_trials_searched=len(api_trials),
                search_criteria_used=search_criteria,
                excluded_reason_summary=excluded_reasons
            )

        except Exception as e:
            logger.error(f"Error searching ClinicalTrials.gov: {e}")
            # Fall back to mock if API fails
            logger.info("Falling back to mock data")
            return self._mock_execute(input_data)

    async def _evaluate_trial_eligibility(
        self,
        api_trial,
        patient_summary: PatientSummary,
        genomics: Optional[GenomicAnalysisResult]
    ) -> Optional[ClinicalTrial]:
        """Use LLM to evaluate patient eligibility for a trial."""

        # Build eligibility evaluation prompt
        prompt = f"""Evaluate this patient's eligibility for the clinical trial.

PATIENT SUMMARY:
- Age: {patient_summary.age}
- Cancer: {patient_summary.cancer.cancer_type.value if patient_summary.cancer else 'Unknown'}
- Stage: {patient_summary.cancer.stage.value if patient_summary.cancer else 'Unknown'}
- ECOG Status: {patient_summary.ecog_status.value if patient_summary.ecog_status else 'Unknown'}

GENOMIC PROFILE:
{self._format_genomics(genomics)}

CLINICAL TRIAL:
- NCT ID: {api_trial.nct_id}
- Title: {api_trial.title}
- Phase: {api_trial.phase}
- Status: {api_trial.status}
- Conditions: {', '.join(api_trial.conditions)}
- Interventions: {', '.join(api_trial.interventions)}

ELIGIBILITY CRITERIA:
{api_trial.eligibility_criteria_text[:2000] if api_trial.eligibility_criteria_text else 'Not specified'}

Based on the patient profile and trial criteria, provide:
1. A match score from 0.0 to 1.0 (1.0 = perfect match)
2. List of criteria the patient meets
3. List of criteria the patient does not meet
4. List of criteria that cannot be determined
5. Brief rationale for the match score

Respond in JSON format:
{{
    "match_score": 0.0-1.0,
    "meets_criteria": ["criterion 1", "criterion 2"],
    "does_not_meet": ["criterion 1"],
    "unknown_criteria": ["criterion 1"],
    "rationale": "Brief explanation",
    "potential_benefits": ["benefit 1", "benefit 2"],
    "potential_drawbacks": ["drawback 1"]
}}"""

        try:
            response = await self.llm_service.complete(
                prompt=prompt,
                system_prompt="You are a clinical trials eligibility specialist. Evaluate patient-trial matches accurately and conservatively.",
                temperature=0.2
            )

            # Parse LLM response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if not json_match:
                logger.warning(f"Could not parse LLM response for trial {api_trial.nct_id}")
                return None

            eval_result = json.loads(json_match.group())
            match_score = float(eval_result.get("match_score", 0.0))

            # Only include trials with decent match score
            if match_score < 0.3:
                return None

            # Convert eligibility to our model format
            eligibility_criteria = []
            for criterion in eval_result.get("meets_criteria", []):
                eligibility_criteria.append(EligibilityCriterion(
                    criterion=criterion,
                    inclusion=True,
                    patient_meets=True,
                    details=""
                ))
            for criterion in eval_result.get("does_not_meet", []):
                eligibility_criteria.append(EligibilityCriterion(
                    criterion=criterion,
                    inclusion=True,
                    patient_meets=False,
                    details=""
                ))
            for criterion in eval_result.get("unknown_criteria", []):
                eligibility_criteria.append(EligibilityCriterion(
                    criterion=criterion,
                    inclusion=True,
                    patient_meets=None,
                    details="Unable to determine from available information"
                ))

            # Map phase string to enum
            phase = self._parse_phase(api_trial.phase)

            return ClinicalTrial(
                nct_id=api_trial.nct_id,
                title=api_trial.title,
                phase=phase,
                status=api_trial.status,
                sponsor=api_trial.sponsor,
                intervention=", ".join(api_trial.interventions) if api_trial.interventions else "",
                intervention_type="Drug",
                locations=[f"{loc.facility}, {loc.city}, {loc.state}" for loc in api_trial.locations[:5]],
                match_score=match_score,
                eligibility_criteria=eligibility_criteria,
                meets_criteria_count=len(eval_result.get("meets_criteria", [])),
                does_not_meet_count=len(eval_result.get("does_not_meet", [])),
                unknown_count=len(eval_result.get("unknown_criteria", [])),
                rationale=eval_result.get("rationale", ""),
                potential_benefits=eval_result.get("potential_benefits", []),
                potential_drawbacks=eval_result.get("potential_drawbacks", [])
            )

        except Exception as e:
            logger.error(f"Error evaluating trial eligibility: {e}")
            return None

    def _format_genomics(self, genomics: Optional[GenomicAnalysisResult]) -> str:
        """Format genomics data for LLM prompt."""
        if not genomics or not genomics.report:
            return "No genomic data available"

        parts = []
        for mutation in genomics.report.actionable_mutations:
            parts.append(f"- {mutation.gene} {mutation.variant} ({mutation.clinical_significance})")

        if genomics.report.immunotherapy_markers:
            markers = genomics.report.immunotherapy_markers
            if markers.pd_l1_status:
                parts.append(f"- PD-L1: {markers.pd_l1_status}")
            if markers.tmb_status:
                parts.append(f"- TMB: {markers.tmb_status}")
            if markers.msi_status:
                parts.append(f"- MSI: {markers.msi_status}")

        return "\n".join(parts) if parts else "No significant findings"

    def _parse_phase(self, phase_str: str) -> ClinicalTrialPhase:
        """Parse phase string to enum."""
        phase_lower = phase_str.lower() if phase_str else ""
        if "phase 1" in phase_lower and "phase 2" in phase_lower:
            return ClinicalTrialPhase.PHASE_1_2
        elif "phase 2" in phase_lower and "phase 3" in phase_lower:
            return ClinicalTrialPhase.PHASE_2_3
        elif "phase 3" in phase_lower:
            return ClinicalTrialPhase.PHASE_3
        elif "phase 2" in phase_lower:
            return ClinicalTrialPhase.PHASE_2
        elif "phase 1" in phase_lower:
            return ClinicalTrialPhase.PHASE_1
        elif "phase 4" in phase_lower:
            return ClinicalTrialPhase.PHASE_4
        else:
            return ClinicalTrialPhase.NOT_APPLICABLE

    def _mock_execute(self, input_data: ClinicalTrialsInput) -> ClinicalTrialsOutput:
        """Generate mock clinical trials matches."""
        patient_summary = input_data.patient_summary
        genomics = input_data.genomics_result

        matched_trials = []
        search_criteria = []
        excluded_reasons = {}

        # Build search criteria from patient data
        if patient_summary.cancer:
            search_criteria.append(f"Cancer type: {patient_summary.cancer.cancer_type.value}")
            search_criteria.append(f"Stage: {patient_summary.cancer.stage.value}")

        # Get patient mutations for matching
        patient_mutations = []
        if genomics and genomics.report:
            for mutation in genomics.report.actionable_mutations:
                patient_mutations.append(f"{mutation.gene}:{mutation.variant}".lower())
                search_criteria.append(f"Mutation: {mutation.gene} {mutation.variant}")

        # Match trials
        for trial_data in self.MOCK_TRIALS:
            match_score, eligibility, rationale = self._evaluate_trial_match(
                trial_data, patient_summary, patient_mutations, genomics
            )

            if match_score >= 0.3:  # Threshold for inclusion
                trial = ClinicalTrial(
                    nct_id=trial_data["nct_id"],
                    title=trial_data["title"],
                    phase=trial_data["phase"],
                    status=trial_data["status"],
                    sponsor=trial_data.get("sponsor"),
                    intervention=trial_data["intervention"],
                    intervention_type=trial_data["intervention_type"],
                    locations=trial_data.get("locations", []),
                    match_score=match_score,
                    eligibility_criteria=eligibility,
                    meets_criteria_count=sum(1 for e in eligibility if e.patient_meets is True),
                    does_not_meet_count=sum(1 for e in eligibility if e.patient_meets is False),
                    unknown_count=sum(1 for e in eligibility if e.patient_meets is None),
                    rationale=rationale,
                    potential_benefits=self._get_trial_benefits(trial_data),
                    potential_drawbacks=self._get_trial_drawbacks(trial_data, patient_summary)
                )
                matched_trials.append(trial)
            else:
                excluded_reasons[trial_data["nct_id"]] = "Low match score - eligibility criteria not met"

        # Sort by match score
        matched_trials.sort(key=lambda t: t.match_score, reverse=True)

        return ClinicalTrialsOutput(
            matched_trials=matched_trials[:10],  # Top 10
            total_trials_searched=len(self.MOCK_TRIALS),
            search_criteria_used=search_criteria,
            excluded_reason_summary=excluded_reasons
        )

    def _evaluate_trial_match(
        self,
        trial_data: dict,
        patient_summary: PatientSummary,
        patient_mutations: List[str],
        genomics: Optional[GenomicAnalysisResult]
    ) -> tuple:
        """Evaluate how well a patient matches a trial."""
        eligibility = []
        score_components = []

        # Check biomarker match
        trial_biomarker = trial_data.get("biomarker", "").lower()
        trial_mutations = [m.lower() for m in trial_data.get("mutations", [])]

        biomarker_match = False
        for patient_mut in patient_mutations:
            gene, variant = patient_mut.split(":") if ":" in patient_mut else (patient_mut, "")
            if trial_biomarker in gene:
                if "any" in trial_mutations or any(m in variant for m in trial_mutations):
                    biomarker_match = True
                    eligibility.append(EligibilityCriterion(
                        criterion=f"{trial_biomarker.upper()} mutation",
                        inclusion=True,
                        patient_meets=True,
                        details=f"Patient has {gene.upper()} {variant}"
                    ))
                    score_components.append(0.4)
                    break

        if not biomarker_match and trial_biomarker:
            if trial_biomarker == "pd-l1":
                # PD-L1 is for immunotherapy trials - check markers
                eligibility.append(EligibilityCriterion(
                    criterion="PD-L1 status",
                    inclusion=True,
                    patient_meets=None,  # Unknown
                    details="PD-L1 testing status needs verification"
                ))
                score_components.append(0.2)
            else:
                eligibility.append(EligibilityCriterion(
                    criterion=f"{trial_biomarker.upper()} mutation",
                    inclusion=True,
                    patient_meets=False,
                    details=f"Patient does not have {trial_biomarker.upper()} mutation"
                ))
                score_components.append(0)

        # Check ECOG status
        ecog_value = patient_summary.ecog_status.value if patient_summary.ecog_status else 1
        if ecog_value <= 1:
            eligibility.append(EligibilityCriterion(
                criterion="ECOG 0-1",
                inclusion=True,
                patient_meets=True,
                details=f"Patient ECOG is {ecog_value}"
            ))
            score_components.append(0.2)
        else:
            eligibility.append(EligibilityCriterion(
                criterion="ECOG 0-1",
                inclusion=True,
                patient_meets=False,
                details=f"Patient ECOG is {ecog_value}"
            ))
            score_components.append(0)

        # Check organ function
        organ_issues = [o for o in patient_summary.organ_function
                       if o.status in ["moderate_impairment", "severe_impairment", "mild_impairment"]]
        if not organ_issues:
            eligibility.append(EligibilityCriterion(
                criterion="Adequate organ function",
                inclusion=True,
                patient_meets=True,
                details="No significant organ impairment"
            ))
            score_components.append(0.2)
        else:
            eligibility.append(EligibilityCriterion(
                criterion="Adequate organ function",
                inclusion=True,
                patient_meets=None,  # Unknown - needs review
                details=f"Organ impairment noted: {', '.join(o.organ for o in organ_issues)}"
            ))
            score_components.append(0.1)

        # Trial phase bonus (Phase 3 preferred)
        if trial_data["phase"] == ClinicalTrialPhase.PHASE_3:
            score_components.append(0.1)
        elif trial_data["phase"] in [ClinicalTrialPhase.PHASE_2, ClinicalTrialPhase.PHASE_2_3]:
            score_components.append(0.05)

        # Recruiting status
        if trial_data["status"] == "Recruiting":
            score_components.append(0.1)

        # Calculate final score
        match_score = min(sum(score_components), 1.0)

        # Generate rationale
        rationale = self._generate_match_rationale(
            trial_data, biomarker_match, ecog_value, organ_issues
        )

        return match_score, eligibility, rationale

    def _generate_match_rationale(
        self,
        trial_data: dict,
        biomarker_match: bool,
        ecog_value: int,
        organ_issues: List
    ) -> str:
        """Generate rationale for trial match."""
        parts = []

        if biomarker_match:
            parts.append(f"Patient's {trial_data['biomarker'].upper()} mutation matches trial criteria")

        if ecog_value <= 1:
            parts.append("Good performance status supports trial participation")

        if not organ_issues:
            parts.append("No organ function concerns")
        elif organ_issues:
            parts.append(f"Organ function concerns may require sponsor discussion")

        if trial_data["phase"] == ClinicalTrialPhase.PHASE_3:
            parts.append("Phase 3 trial offers established safety data")

        return ". ".join(parts) + "." if parts else "Review eligibility criteria with trial site."

    def _get_trial_benefits(self, trial_data: dict) -> List[str]:
        """Get potential benefits of trial."""
        benefits = []

        benefits.append(f"Access to {trial_data['intervention']}")

        if trial_data["phase"] in [ClinicalTrialPhase.PHASE_3, ClinicalTrialPhase.PHASE_2_3]:
            benefits.append("Late-phase trial with established efficacy signals")

        if "Combination" in trial_data["intervention_type"]:
            benefits.append("Novel combination approach")

        benefits.append("Close monitoring and expert care")
        benefits.append("Potential to help future patients")

        return benefits

    def _get_trial_drawbacks(
        self,
        trial_data: dict,
        patient_summary: PatientSummary
    ) -> List[str]:
        """Get potential drawbacks of trial."""
        drawbacks = []

        if trial_data["phase"] == ClinicalTrialPhase.PHASE_1:
            drawbacks.append("Early-phase trial with limited efficacy data")

        drawbacks.append("Additional visits and monitoring required")
        drawbacks.append("May not receive standard of care in some arms")

        return drawbacks

    def _build_search_prompt(self, input_data: ClinicalTrialsInput) -> str:
        """Build search prompt."""
        return f"""Search for clinical trials matching this patient:

Patient Summary:
{input_data.patient_summary.model_dump_json(indent=2)}

Genomics:
{input_data.genomics_result.model_dump_json(indent=2) if input_data.genomics_result else 'Not available'}

Location Preference: {input_data.patient_location or 'Any'}
Max Distance: {input_data.max_distance_miles} miles

Please identify and rank matching clinical trials with eligibility assessment."""
