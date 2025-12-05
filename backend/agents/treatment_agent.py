"""Treatment Agent for generating treatment recommendations."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .base_agent import BaseAgent
from models.patient import PatientSummary
from models.genomics import GenomicAnalysisResult
from models.treatment import (
    TreatmentPlan, TreatmentOption, ClinicalTrial,
    EvidenceSummary, RecommendationLevel, EvidenceLevel
)
from services.llm_service import LLMService


class TreatmentInput(BaseModel):
    """Input for treatment recommendation."""
    patient_id: str
    patient_summary: PatientSummary
    genomics_result: Optional[GenomicAnalysisResult] = None
    evidence_summaries: List[EvidenceSummary] = Field(default_factory=list)
    clinical_trials: List[ClinicalTrial] = Field(default_factory=list)


class TreatmentOutput(BaseModel):
    """Output from treatment recommendation."""
    treatment_plan: Optional[TreatmentPlan] = None
    primary_recommendation: Optional[TreatmentOption] = None
    alternatives: List[TreatmentOption] = Field(default_factory=list)
    clinical_trial_recommendations: List[ClinicalTrial] = Field(default_factory=list)
    discussion_points: List[str] = Field(default_factory=list)


class TreatmentAgent(BaseAgent[TreatmentInput, TreatmentOutput]):
    """Agent that generates personalized treatment recommendations.

    This agent:
    - Synthesizes all available patient data
    - Ranks treatment options based on multiple criteria
    - Considers patient-specific factors (comorbidities, preferences)
    - Provides evidence-based rationale for recommendations
    - Identifies relevant clinical trials
    - Highlights discussion points for care team
    """

    # Treatment database with criteria
    TREATMENT_DATABASE = {
        "EGFR_mutant": [
            {
                "name": "Osimertinib (Tagrisso)",
                "type": "targeted_therapy",
                "drugs": ["Osimertinib"],
                "dosing": "80mg once daily",
                "schedule": "Continuous until progression",
                "response_rate": 0.80,
                "pfs_months": 18.9,
                "os_months": 38.6,
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["FLAURA", "FLAURA2"],
                "common_side_effects": ["Diarrhea", "Rash", "Dry skin", "Paronychia"],
                "serious_side_effects": ["QT prolongation", "ILD/Pneumonitis", "Cardiac failure"],
                "renal_adjustment": False,
                "hepatic_adjustment": False,
            },
            {
                "name": "Erlotinib (Tarceva)",
                "type": "targeted_therapy",
                "drugs": ["Erlotinib"],
                "dosing": "150mg once daily",
                "schedule": "Continuous until progression",
                "response_rate": 0.65,
                "pfs_months": 10.4,
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["EURTAC", "OPTIMAL"],
                "common_side_effects": ["Rash", "Diarrhea", "Fatigue"],
                "serious_side_effects": ["ILD", "Hepatotoxicity"],
                "renal_adjustment": False,
                "hepatic_adjustment": True,
            },
        ],
        "ALK_positive": [
            {
                "name": "Alectinib (Alecensa)",
                "type": "targeted_therapy",
                "drugs": ["Alectinib"],
                "dosing": "600mg twice daily",
                "schedule": "Continuous until progression",
                "response_rate": 0.83,
                "pfs_months": 34.8,
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["ALEX", "J-ALEX"],
                "common_side_effects": ["Fatigue", "Constipation", "Edema", "Myalgia"],
                "serious_side_effects": ["ILD", "Hepatotoxicity", "Bradycardia"],
            },
            {
                "name": "Lorlatinib (Lorbrena)",
                "type": "targeted_therapy",
                "drugs": ["Lorlatinib"],
                "dosing": "100mg once daily",
                "schedule": "Continuous until progression",
                "response_rate": 0.76,
                "pfs_months": 60.0,  # Not yet reached in CROWN
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["CROWN"],
                "common_side_effects": ["Hyperlipidemia", "Edema", "Weight gain", "Cognitive effects"],
                "serious_side_effects": ["CNS effects", "Hypertension", "AV block"],
            },
        ],
        "KRAS_G12C": [
            {
                "name": "Sotorasib (Lumakras)",
                "type": "targeted_therapy",
                "drugs": ["Sotorasib"],
                "dosing": "960mg once daily",
                "schedule": "Continuous until progression",
                "response_rate": 0.37,
                "pfs_months": 6.8,
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["CodeBreaK 100", "CodeBreaK 200"],
                "common_side_effects": ["Diarrhea", "Nausea", "Fatigue", "Hepatotoxicity"],
                "serious_side_effects": ["ILD", "Hepatotoxicity"],
            },
        ],
        "immunotherapy": [
            {
                "name": "Pembrolizumab (Keytruda)",
                "type": "immunotherapy",
                "drugs": ["Pembrolizumab"],
                "dosing": "200mg every 3 weeks",
                "schedule": "Up to 2 years",
                "response_rate": 0.45,
                "pfs_months": 10.3,
                "evidence": EvidenceLevel.CATEGORY_1,
                "key_trials": ["KEYNOTE-024", "KEYNOTE-042"],
                "common_side_effects": ["Fatigue", "Rash", "Diarrhea", "Nausea"],
                "serious_side_effects": ["Pneumonitis", "Colitis", "Hepatitis", "Thyroid disorders"],
                "requires_pdl1": True,
                "pdl1_threshold": 50,
            },
        ],
        "chemotherapy": [
            {
                "name": "Carboplatin + Pemetrexed",
                "type": "chemotherapy",
                "drugs": ["Carboplatin", "Pemetrexed"],
                "dosing": "Carboplatin AUC 5, Pemetrexed 500mg/m2",
                "schedule": "Every 3 weeks x 4-6 cycles, then pemetrexed maintenance",
                "response_rate": 0.30,
                "pfs_months": 5.0,
                "evidence": EvidenceLevel.CATEGORY_1,
                "common_side_effects": ["Nausea", "Fatigue", "Cytopenias", "Neuropathy"],
                "serious_side_effects": ["Febrile neutropenia", "Renal toxicity", "Ototoxicity"],
                "renal_adjustment": True,
            },
        ],
    }

    def __init__(self, llm_service: LLMService, use_mock: bool = True):
        super().__init__(
            name="treatment",
            llm_service=llm_service,
            use_mock=use_mock
        )

    def get_system_prompt(self) -> str:
        return """You are an oncology treatment planning AI specialist.
Your role is to:
1. Synthesize all patient data to create personalized treatment recommendations
2. Rank options considering efficacy, toxicity, and patient factors
3. Account for comorbidities, organ function, and drug interactions
4. Provide clear evidence-based rationale for each recommendation
5. Identify appropriate clinical trials
6. Highlight important discussion points for the care team

Be thorough but practical. Consider real-world factors like drug availability and patient burden.
Never make final treatment decisions - present options for physician review."""

    async def execute(self, input_data: TreatmentInput) -> TreatmentOutput:
        """Execute treatment recommendation using LLM."""
        try:
            prompt = self._build_recommendation_prompt(input_data)

            response = await self._call_llm(
                prompt=prompt,
                output_model=TreatmentOutput,
                temperature=0.2,
                max_tokens=4000  # Increase token limit for complex responses
            )

            return response

        except Exception as e:
            self.logger.error(f"LLM call failed in treatment agent: {e}, falling back to mock")
            return self._mock_execute(input_data)

    def _mock_execute(self, input_data: TreatmentInput) -> TreatmentOutput:
        """Generate mock treatment recommendations."""
        patient_summary = input_data.patient_summary
        genomics = input_data.genomics_result

        # Identify treatment category based on mutations
        treatment_category = self._identify_treatment_category(genomics)

        # Get candidate treatments
        candidates = self._get_candidate_treatments(treatment_category, patient_summary, genomics)

        # Rank and score treatments
        ranked_treatments = self._rank_treatments(candidates, patient_summary, genomics)

        # Get primary recommendation and alternatives
        primary = ranked_treatments[0] if ranked_treatments else self._get_default_treatment(patient_summary)
        alternatives = ranked_treatments[1:4] if len(ranked_treatments) > 1 else []

        # Filter and rank clinical trials
        trial_recs = self._filter_clinical_trials(input_data.clinical_trials, genomics)

        # Generate discussion points
        discussion_points = self._generate_discussion_points(
            primary, alternatives, patient_summary, genomics
        )

        # Build treatment plan
        treatment_plan = TreatmentPlan(
            patient_id=input_data.patient_id,
            generated_at=datetime.now().isoformat(),
            treatment_options=[primary] + alternatives,
            clinical_trials=trial_recs[:5],
            discussion_points=discussion_points,
            next_steps=self._generate_next_steps(primary, patient_summary),
            summary=self._generate_plan_summary(primary, alternatives, trial_recs)
        )

        return TreatmentOutput(
            treatment_plan=treatment_plan,
            primary_recommendation=primary,
            alternatives=alternatives,
            clinical_trial_recommendations=trial_recs,
            discussion_points=discussion_points
        )

    def _identify_treatment_category(
        self,
        genomics: Optional[GenomicAnalysisResult]
    ) -> str:
        """Identify treatment category based on mutations."""
        if not genomics or not genomics.report:
            return "chemotherapy"

        for mutation in genomics.report.actionable_mutations:
            gene = mutation.gene.upper()
            variant = mutation.variant.lower()

            if gene == "EGFR":
                return "EGFR_mutant"
            elif gene == "ALK":
                return "ALK_positive"
            elif gene == "KRAS" and "g12c" in variant:
                return "KRAS_G12C"
            elif gene == "ROS1":
                return "ROS1_positive"
            elif gene == "BRAF" and "v600" in variant:
                return "BRAF_V600"

        # Check immunotherapy markers
        if genomics.report.immunotherapy_markers:
            markers = genomics.report.immunotherapy_markers
            if markers.pdl1_expression and markers.pdl1_expression >= 50:
                return "immunotherapy"

        return "chemotherapy"

    def _get_candidate_treatments(
        self,
        category: str,
        patient_summary: PatientSummary,
        genomics: Optional[GenomicAnalysisResult]
    ) -> List[dict]:
        """Get candidate treatments for category."""
        candidates = self.TREATMENT_DATABASE.get(category, [])

        # Add immunotherapy if appropriate
        if genomics and genomics.report and genomics.report.immunotherapy_markers:
            markers = genomics.report.immunotherapy_markers
            if markers.immunotherapy_likely_benefit:
                candidates.extend(self.TREATMENT_DATABASE.get("immunotherapy", []))

        # Always include chemotherapy as backup
        if category != "chemotherapy":
            candidates.extend(self.TREATMENT_DATABASE.get("chemotherapy", []))

        return candidates

    def _rank_treatments(
        self,
        candidates: List[dict],
        patient_summary: PatientSummary,
        genomics: Optional[GenomicAnalysisResult]
    ) -> List[TreatmentOption]:
        """Rank treatments and create TreatmentOption objects."""
        scored_treatments = []

        for i, tx in enumerate(candidates):
            score, why_rec, why_not, considerations = self._score_treatment(
                tx, patient_summary, genomics
            )

            treatment_option = TreatmentOption(
                rank=i + 1,
                treatment_name=tx["name"],
                treatment_type=tx["type"],
                drugs=tx.get("drugs", []),
                dosing=tx.get("dosing"),
                schedule=tx.get("schedule"),
                recommendation=self._score_to_recommendation(score),
                confidence=score,
                expected_response_rate=tx.get("response_rate"),
                expected_pfs_months=tx.get("pfs_months"),
                expected_os_months=tx.get("os_months"),
                why_recommended=why_rec,
                why_not_recommended=why_not,
                considerations=considerations,
                evidence_level=tx.get("evidence"),
                key_trials=tx.get("key_trials", []),
                guideline_references=["NCCN Guidelines"],
                common_side_effects=tx.get("common_side_effects", []),
                serious_side_effects=tx.get("serious_side_effects", []),
                dose_adjustments=self._get_dose_adjustments(tx, patient_summary),
                monitoring_required=self._get_monitoring_requirements(tx)
            )
            scored_treatments.append((score, treatment_option))

        # Sort by score descending
        scored_treatments.sort(key=lambda x: x[0], reverse=True)

        # Update ranks
        ranked = []
        for rank, (score, tx) in enumerate(scored_treatments, 1):
            tx.rank = rank
            ranked.append(tx)

        return ranked

    def _score_treatment(
        self,
        tx: dict,
        patient_summary: PatientSummary,
        genomics: Optional[GenomicAnalysisResult]
    ) -> tuple:
        """Score a treatment option."""
        score = 0.5  # Base score
        why_recommended = []
        why_not_recommended = []
        considerations = []

        # Efficacy score
        rr = tx.get("response_rate", 0.3)
        if rr >= 0.7:
            score += 0.2
            why_recommended.append(f"High response rate ({rr*100:.0f}%)")
        elif rr >= 0.5:
            score += 0.1
            why_recommended.append(f"Good response rate ({rr*100:.0f}%)")

        # Evidence level
        evidence = tx.get("evidence")
        if evidence == EvidenceLevel.CATEGORY_1:
            score += 0.15
            why_recommended.append("Category 1 evidence (highest level)")
        elif evidence == EvidenceLevel.CATEGORY_2A:
            score += 0.1
            why_recommended.append("Category 2A evidence")

        # PFS bonus
        pfs = tx.get("pfs_months", 0)
        if pfs >= 12:
            score += 0.1
            why_recommended.append(f"Durable responses (median PFS {pfs} months)")

        # Check organ function
        for organ in patient_summary.organ_function:
            if organ.organ.lower() == "kidney" and organ.status in ["moderate_impairment", "severe_impairment"]:
                if tx.get("renal_adjustment"):
                    considerations.append("Dose adjustment required for renal impairment")
                    score -= 0.05

            if organ.organ.lower() == "liver" and organ.status in ["moderate_impairment", "severe_impairment"]:
                if tx.get("hepatic_adjustment"):
                    considerations.append("Dose adjustment required for hepatic impairment")
                    score -= 0.05

        # Check ECOG status
        ecog = patient_summary.ecog_status.value if patient_summary.ecog_status else 1
        if ecog >= 2 and tx["type"] == "chemotherapy":
            score -= 0.1
            considerations.append("Performance status may limit chemotherapy tolerability")

        # PD-L1 requirements for immunotherapy
        if tx.get("requires_pdl1"):
            if genomics and genomics.report and genomics.report.immunotherapy_markers:
                pdl1 = genomics.report.immunotherapy_markers.pdl1_expression or 0
                if pdl1 >= tx.get("pdl1_threshold", 50):
                    score += 0.1
                    why_recommended.append(f"PD-L1 {pdl1}% meets threshold")
                else:
                    score -= 0.15
                    why_not_recommended.append(f"PD-L1 {pdl1}% below preferred threshold")
            else:
                considerations.append("PD-L1 status should be verified")

        # Cap score
        score = max(0, min(1, score))

        return score, why_recommended, why_not_recommended, considerations

    def _score_to_recommendation(self, score: float) -> RecommendationLevel:
        """Convert score to recommendation level."""
        if score >= 0.8:
            return RecommendationLevel.STRONGLY_RECOMMENDED
        elif score >= 0.6:
            return RecommendationLevel.RECOMMENDED
        elif score >= 0.4:
            return RecommendationLevel.CONSIDER
        else:
            return RecommendationLevel.NOT_RECOMMENDED

    def _get_default_treatment(self, patient_summary: PatientSummary) -> TreatmentOption:
        """Get default chemotherapy treatment."""
        chemo = self.TREATMENT_DATABASE["chemotherapy"][0]
        return TreatmentOption(
            rank=1,
            treatment_name=chemo["name"],
            treatment_type=chemo["type"],
            drugs=chemo["drugs"],
            dosing=chemo["dosing"],
            schedule=chemo["schedule"],
            recommendation=RecommendationLevel.RECOMMENDED,
            confidence=0.5,
            expected_response_rate=chemo["response_rate"],
            expected_pfs_months=chemo["pfs_months"],
            why_recommended=["Standard first-line option when no targetable mutations"],
            evidence_level=chemo["evidence"],
            common_side_effects=chemo["common_side_effects"],
            serious_side_effects=chemo["serious_side_effects"]
        )

    def _get_dose_adjustments(self, tx: dict, patient_summary: PatientSummary) -> List[str]:
        """Get required dose adjustments."""
        adjustments = []

        for organ in patient_summary.organ_function:
            if organ.status in ["moderate_impairment", "severe_impairment"]:
                if organ.organ.lower() == "kidney" and tx.get("renal_adjustment"):
                    adjustments.append(f"Renal: Reduce dose per package insert for {organ.status}")
                if organ.organ.lower() == "liver" and tx.get("hepatic_adjustment"):
                    adjustments.append(f"Hepatic: Reduce dose per package insert for {organ.status}")

        return adjustments

    def _get_monitoring_requirements(self, tx: dict) -> List[str]:
        """Get monitoring requirements."""
        monitoring = ["Regular CBC and chemistry panels"]

        if tx["type"] == "targeted_therapy":
            monitoring.append("LFTs every 2-4 weeks initially")
            if "QT" in str(tx.get("serious_side_effects", [])):
                monitoring.append("ECG at baseline and periodically")

        if tx["type"] == "immunotherapy":
            monitoring.append("Thyroid function tests")
            monitoring.append("Monitor for immune-related adverse events")

        if tx["type"] == "chemotherapy":
            monitoring.append("CBC before each cycle")
            monitoring.append("Renal function monitoring")

        return monitoring

    def _filter_clinical_trials(
        self,
        trials: List[ClinicalTrial],
        genomics: Optional[GenomicAnalysisResult]
    ) -> List[ClinicalTrial]:
        """Filter and rank clinical trials."""
        # Sort by match score
        sorted_trials = sorted(trials, key=lambda t: t.match_score, reverse=True)
        # Filter to high-quality matches
        return [t for t in sorted_trials if t.match_score >= 0.5]

    def _generate_discussion_points(
        self,
        primary: TreatmentOption,
        alternatives: List[TreatmentOption],
        patient_summary: PatientSummary,
        genomics: Optional[GenomicAnalysisResult]
    ) -> List[str]:
        """Generate discussion points for care team."""
        points = []

        if primary:
            treatment_name = primary.treatment_name or "Unknown"
            rec_val = primary.recommendation.value if primary.recommendation else "recommended"
            points.append(f"Primary recommendation: {treatment_name} ({rec_val})")

        if alternatives:
            alt_names = ", ".join((a.treatment_name or "Unknown") for a in alternatives[:2] if a)
            if alt_names:
                points.append(f"Alternatives to discuss: {alt_names}")

        # Comorbidity considerations
        severe_comorb = [c for c in patient_summary.comorbidities if c.severity == "severe"]
        if severe_comorb:
            points.append(f"Severe comorbidities to consider: {', '.join(c.condition for c in severe_comorb)}")

        # Organ function
        impaired = [o.organ for o in patient_summary.organ_function
                   if o.status in ["moderate_impairment", "severe_impairment"]]
        if impaired:
            points.append(f"Organ function concerns: {', '.join(impaired)} - verify dosing")

        # Genomic considerations
        if genomics and genomics.report:
            if len(genomics.report.actionable_mutations) > 1:
                points.append("Multiple actionable mutations detected - discuss sequencing strategy")

        return points

    def _generate_next_steps(
        self,
        primary: TreatmentOption,
        patient_summary: PatientSummary
    ) -> List[str]:
        """Generate next steps."""
        treatment_name = primary.treatment_name if primary and primary.treatment_name else "selected treatment"
        steps = [
            "Review treatment plan with patient and family",
            f"If {treatment_name} selected: Order baseline labs and imaging",
            "Schedule treatment initiation appointment",
            "Arrange for supportive care (antiemetics, growth factors if needed)",
        ]

        # Add trial consideration
        steps.append("Consider clinical trial enrollment if eligible")

        return steps

    def _generate_plan_summary(
        self,
        primary: TreatmentOption,
        alternatives: List[TreatmentOption],
        trials: List[ClinicalTrial]
    ) -> str:
        """Generate treatment plan summary."""
        treatment_name = primary.treatment_name if primary and primary.treatment_name else "Unknown treatment"
        parts = [f"Primary recommendation: {treatment_name}"]

        if primary and primary.expected_response_rate:
            parts.append(f"Expected response rate: {primary.expected_response_rate*100:.0f}%")

        if alternatives:
            parts.append(f"{len(alternatives)} alternative options available")

        if trials:
            parts.append(f"{len(trials)} clinical trials identified")

        return ". ".join(parts) + "."

    def _build_recommendation_prompt(self, input_data: TreatmentInput) -> str:
        """Build recommendation prompt."""
        return f"""Generate treatment recommendations for this patient:

Patient ID: {input_data.patient_id}

Patient Summary:
{input_data.patient_summary.model_dump_json(indent=2)}

Genomics:
{input_data.genomics_result.model_dump_json(indent=2) if input_data.genomics_result else 'Not available'}

Evidence Summaries:
{[e.model_dump() for e in input_data.evidence_summaries]}

Available Clinical Trials:
{[t.model_dump() for t in input_data.clinical_trials]}

Please provide ranked treatment recommendations with:
1. Primary recommendation with full rationale
2. Alternative options
3. Clinical trial recommendations
4. Discussion points for the care team
5. Next steps"""
