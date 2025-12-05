"""Genomics Agent for interpreting genetic/mutation data."""

from typing import List, Optional
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from models.patient import Patient
from models.genomics import (
    GenomicReport, GenomicAnalysisResult, Mutation, MutationClassification,
    ImmunotherapyMarkers, Therapy
)
from services.llm_service import LLMService


class GenomicsInput(BaseModel):
    """Input for genomics analysis."""
    patient: Patient
    genomic_report: Optional[GenomicReport] = None


class GenomicsOutput(BaseModel):
    """Output from genomics analysis."""
    analysis_result: Optional[GenomicAnalysisResult] = None
    actionable_mutations: List[Mutation] = Field(default_factory=list)
    therapy_candidates: List[str] = Field(default_factory=list)
    immunotherapy_markers: Optional[ImmunotherapyMarkers] = None
    resistance_mutations: List[str] = Field(default_factory=list)
    clinical_trial_targets: List[str] = Field(default_factory=list)


class GenomicsAgent(BaseAgent[GenomicsInput, GenomicsOutput]):
    """Agent that interprets genomic and mutation data.

    This agent:
    - Identifies actionable mutations with FDA-approved therapies
    - Assesses immunotherapy markers (PD-L1, TMB, MSI)
    - Identifies resistance mutations
    - Suggests targeted therapy candidates
    - Identifies mutations that may qualify for clinical trials
    """

    # Known actionable mutations and their therapies
    ACTIONABLE_MUTATIONS = {
        "EGFR": {
            "exon 19 del": ["Osimertinib", "Erlotinib", "Gefitinib", "Afatinib"],
            "L858R": ["Osimertinib", "Erlotinib", "Gefitinib", "Afatinib"],
            "T790M": ["Osimertinib"],
            "exon 20 ins": ["Amivantamab", "Mobocertinib"],
        },
        "ALK": {
            "fusion": ["Alectinib", "Brigatinib", "Lorlatinib", "Crizotinib"],
            "rearrangement": ["Alectinib", "Brigatinib", "Lorlatinib"],
        },
        "ROS1": {
            "fusion": ["Crizotinib", "Entrectinib", "Lorlatinib"],
            "rearrangement": ["Crizotinib", "Entrectinib"],
        },
        "BRAF": {
            "V600E": ["Dabrafenib + Trametinib", "Vemurafenib + Cobimetinib"],
        },
        "KRAS": {
            "G12C": ["Sotorasib", "Adagrasib"],
        },
        "MET": {
            "exon 14 skip": ["Capmatinib", "Tepotinib"],
            "amplification": ["Capmatinib", "Crizotinib"],
        },
        "RET": {
            "fusion": ["Selpercatinib", "Pralsetinib"],
            "rearrangement": ["Selpercatinib", "Pralsetinib"],
        },
        "NTRK": {
            "fusion": ["Larotrectinib", "Entrectinib"],
        },
        "HER2": {
            "amplification": ["Trastuzumab deruxtecan"],
            "mutation": ["Trastuzumab deruxtecan"],
        },
    }

    # Resistance mutations
    RESISTANCE_MUTATIONS = {
        "EGFR": {
            "T790M": "1st/2nd gen EGFR TKIs",
            "C797S": "Osimertinib",
        },
        "ALK": {
            "G1202R": "1st/2nd gen ALK TKIs",
            "L1196M": "Crizotinib",
        },
    }

    def __init__(self, llm_service: LLMService, use_mock: bool = True):
        super().__init__(
            name="genomics",
            llm_service=llm_service,
            use_mock=use_mock
        )

    def get_system_prompt(self) -> str:
        return """You are a genomics and precision oncology AI specialist.
Your role is to:
1. Interpret genomic test results and identify actionable mutations
2. Match mutations to FDA-approved targeted therapies
3. Assess immunotherapy markers (PD-L1, TMB, MSI status)
4. Identify resistance mutations and their implications
5. Suggest mutations that may qualify for clinical trials

Be precise and evidence-based. Reference FDA approvals and NCCN guidelines when relevant.
Always note the level of evidence for each recommendation."""

    async def execute(self, input_data: GenomicsInput) -> GenomicsOutput:
        """Execute genomics analysis using LLM."""
        prompt = self._build_analysis_prompt(input_data)

        response = await self._call_llm(
            prompt=prompt,
            output_model=GenomicsOutput,
            temperature=0.2
        )

        return response

    def _mock_execute(self, input_data: GenomicsInput) -> GenomicsOutput:
        """Generate mock genomics analysis."""
        patient = input_data.patient
        report = input_data.genomic_report

        # If no report provided, create mock data based on patient
        if not report:
            report = self._create_mock_report(patient)

        # Analyze mutations
        actionable_mutations = []
        therapy_candidates = []
        resistance_mutations = []
        clinical_trial_targets = []

        for mutation in report.actionable_mutations + report.other_mutations:
            # Check if mutation is actionable
            if mutation.gene in self.ACTIONABLE_MUTATIONS:
                gene_mutations = self.ACTIONABLE_MUTATIONS[mutation.gene]
                for pattern, therapies in gene_mutations.items():
                    if pattern.lower() in mutation.variant.lower():
                        mutation.therapies = [
                            Therapy(drug_name=t, fda_approved=True)
                            for t in therapies
                        ]
                        if mutation not in actionable_mutations:
                            actionable_mutations.append(mutation)
                        therapy_candidates.extend(therapies)

            # Check for resistance mutations
            if mutation.gene in self.RESISTANCE_MUTATIONS:
                for variant, resistance_to in self.RESISTANCE_MUTATIONS[mutation.gene].items():
                    if variant.lower() in mutation.variant.lower():
                        resistance_mutations.append(f"{mutation.gene} {variant}: resistance to {resistance_to}")

            # Clinical trial targets (mutations without FDA-approved therapy)
            if mutation.classification == MutationClassification.PATHOGENIC_ACTIONABLE:
                if not mutation.therapies:
                    clinical_trial_targets.append(f"{mutation.gene} {mutation.variant}")

        # Deduplicate therapy candidates
        therapy_candidates = list(set(therapy_candidates))

        # Assess immunotherapy markers
        immuno_markers = report.immunotherapy_markers
        if not immuno_markers:
            immuno_markers = self._assess_immunotherapy_eligibility(report)

        # Create analysis result
        key_findings = self._generate_key_findings(actionable_mutations, immuno_markers, resistance_mutations)
        treatment_implications = self._generate_treatment_implications(
            actionable_mutations, immuno_markers, resistance_mutations
        )

        analysis_result = GenomicAnalysisResult(
            patient_id=patient.id,
            report=report,
            summary=self._generate_summary(actionable_mutations, immuno_markers),
            targeted_therapy_candidates=therapy_candidates[:5],  # Top 5
            immunotherapy_candidate=immuno_markers.immunotherapy_likely_benefit if immuno_markers else False,
            key_findings=key_findings,
            treatment_implications=treatment_implications
        )

        return GenomicsOutput(
            analysis_result=analysis_result,
            actionable_mutations=actionable_mutations,
            therapy_candidates=therapy_candidates,
            immunotherapy_markers=immuno_markers,
            resistance_mutations=resistance_mutations,
            clinical_trial_targets=clinical_trial_targets
        )

    def _create_mock_report(self, patient: Patient) -> GenomicReport:
        """Create a mock genomic report."""
        return GenomicReport(
            report_id=f"GR-{patient.id}",
            patient_id=patient.id,
            test_date="2024-01-15",
            test_type="NGS Panel",
            specimen_type="Tumor tissue",
            actionable_mutations=[
                Mutation(
                    gene="EGFR",
                    variant="exon 19 del",
                    variant_detail="p.E746_A750del",
                    classification=MutationClassification.PATHOGENIC_ACTIONABLE,
                    allele_frequency=0.34,
                    prognostic_impact="favorable"
                )
            ],
            other_mutations=[
                Mutation(
                    gene="TP53",
                    variant="R248W",
                    classification=MutationClassification.PATHOGENIC,
                    allele_frequency=0.28
                )
            ],
            immunotherapy_markers=ImmunotherapyMarkers(
                pdl1_expression=15.0,
                pdl1_interpretation="low",
                tmb=4.0,
                tmb_interpretation="low",
                msi_status="MSS",
                immunotherapy_likely_benefit=False,
                reasoning="Low PD-L1 and TMB suggest limited immunotherapy benefit"
            )
        )

    def _assess_immunotherapy_eligibility(self, report: GenomicReport) -> ImmunotherapyMarkers:
        """Assess immunotherapy eligibility from markers."""
        likely_benefit = False
        reasoning_parts = []

        pdl1 = report.immunotherapy_markers.pdl1_expression if report.immunotherapy_markers else None
        tmb = report.immunotherapy_markers.tmb if report.immunotherapy_markers else None
        msi = report.immunotherapy_markers.msi_status if report.immunotherapy_markers else None

        # PD-L1 assessment
        if pdl1 is not None:
            if pdl1 >= 50:
                likely_benefit = True
                reasoning_parts.append(f"High PD-L1 ({pdl1}%) supports immunotherapy")
            elif pdl1 >= 1:
                reasoning_parts.append(f"PD-L1 {pdl1}% may support combination immunotherapy")

        # TMB assessment
        if tmb is not None:
            if tmb >= 10:
                likely_benefit = True
                reasoning_parts.append(f"High TMB ({tmb} mut/Mb) associated with immunotherapy response")

        # MSI assessment
        if msi == "MSI-H":
            likely_benefit = True
            reasoning_parts.append("MSI-H status indicates immunotherapy benefit")

        return ImmunotherapyMarkers(
            pdl1_expression=pdl1,
            pdl1_interpretation="high" if pdl1 and pdl1 >= 50 else "low" if pdl1 else None,
            tmb=tmb,
            tmb_interpretation="high" if tmb and tmb >= 10 else "low" if tmb else None,
            msi_status=msi,
            immunotherapy_likely_benefit=likely_benefit,
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "Insufficient markers for assessment"
        )

    def _generate_key_findings(
        self,
        actionable_mutations: List[Mutation],
        immuno_markers: Optional[ImmunotherapyMarkers],
        resistance_mutations: List[str]
    ) -> List[str]:
        """Generate key findings list."""
        findings = []

        for mutation in actionable_mutations:
            therapies = [t.drug_name for t in mutation.therapies[:3]]
            findings.append(
                f"{mutation.gene} {mutation.variant} detected - FDA-approved therapies: {', '.join(therapies)}"
            )

        if immuno_markers and immuno_markers.immunotherapy_likely_benefit:
            findings.append("Patient likely to benefit from immunotherapy")

        if resistance_mutations:
            findings.append(f"Resistance mutations detected: {'; '.join(resistance_mutations)}")

        return findings

    def _generate_treatment_implications(
        self,
        actionable_mutations: List[Mutation],
        immuno_markers: Optional[ImmunotherapyMarkers],
        resistance_mutations: List[str]
    ) -> List[str]:
        """Generate treatment implications."""
        implications = []

        # Targeted therapy implications
        for mutation in actionable_mutations:
            if mutation.therapies:
                preferred = mutation.therapies[0].drug_name
                implications.append(f"Consider {preferred} as first-line targeted therapy for {mutation.gene} mutation")

        # Immunotherapy implications
        if immuno_markers:
            if immuno_markers.immunotherapy_likely_benefit:
                implications.append("Immunotherapy (pembrolizumab, nivolumab) should be considered")
            else:
                implications.append("Immunotherapy alone may have limited efficacy - consider combination strategies")

        # Resistance implications
        if resistance_mutations:
            implications.append("Resistance mutations may limit efficacy of certain targeted therapies")

        return implications

    def _generate_summary(
        self,
        actionable_mutations: List[Mutation],
        immuno_markers: Optional[ImmunotherapyMarkers]
    ) -> str:
        """Generate analysis summary."""
        parts = []

        if actionable_mutations:
            genes = [m.gene for m in actionable_mutations]
            parts.append(f"Actionable mutations identified in: {', '.join(genes)}")
        else:
            parts.append("No actionable mutations identified")

        if immuno_markers:
            if immuno_markers.immunotherapy_likely_benefit:
                parts.append("Favorable immunotherapy markers")
            else:
                parts.append("Limited immunotherapy markers")

        return ". ".join(parts) + "."

    def _build_analysis_prompt(self, input_data: GenomicsInput) -> str:
        """Build the analysis prompt."""
        patient = input_data.patient
        report = input_data.genomic_report

        return f"""Analyze the following genomic report for patient {patient.id}:

Cancer Type: {patient.cancer_details.cancer_type.value if patient.cancer_details else 'Unknown'}
Cancer Stage: {patient.cancer_details.stage.value if patient.cancer_details else 'Unknown'}

Genomic Report:
{report.model_dump_json(indent=2) if report else 'No report available'}

Please provide:
1. List of actionable mutations with FDA-approved therapies
2. Assessment of immunotherapy markers
3. Any resistance mutations detected
4. Recommendations for clinical trial targets
5. Overall summary and treatment implications"""
