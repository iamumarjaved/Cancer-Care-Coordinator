"""Evidence Agent for searching medical literature and guidelines."""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from models.patient import PatientSummary
from models.genomics import GenomicAnalysisResult
from models.treatment import EvidenceSummary, EvidenceLevel
from services.llm_service import LLMService
from services.pubmed_service import PubMedService, get_pubmed_service

logger = logging.getLogger(__name__)


class EvidenceInput(BaseModel):
    """Input for evidence search."""
    patient_summary: PatientSummary
    genomics_result: Optional[GenomicAnalysisResult] = None
    treatment_queries: List[str] = Field(default_factory=list)


class Publication(BaseModel):
    """Medical publication reference."""
    title: Optional[str] = "Unknown publication"
    authors: Optional[str] = "Unknown authors"
    journal: Optional[str] = "Unknown journal"
    year: Optional[int] = None
    pmid: Optional[str] = None
    key_finding: Optional[str] = None
    relevance_to_patient: Optional[str] = None


class GuidelineRecommendation(BaseModel):
    """Guideline recommendation."""
    guideline: Optional[str] = "NCCN Guidelines"  # e.g., "NCCN NSCLC v2.2024"
    recommendation: Optional[str] = "See guidelines for details"
    evidence_level: Optional[EvidenceLevel] = EvidenceLevel.CATEGORY_2A
    applicable_to_patient: Optional[bool] = True
    notes: Optional[str] = None


class EvidenceOutput(BaseModel):
    """Output from evidence search."""
    evidence_summaries: List[EvidenceSummary] = Field(default_factory=list)
    guideline_recommendations: List[GuidelineRecommendation] = Field(default_factory=list)
    relevant_publications: List[Publication] = Field(default_factory=list)
    recent_updates: List[str] = Field(default_factory=list)
    search_terms_used: List[str] = Field(default_factory=list)


class EvidenceAgent(BaseAgent[EvidenceInput, EvidenceOutput]):
    """Agent that searches medical literature and guidelines.

    This agent:
    - Searches PubMed for relevant publications
    - Retrieves NCCN and other guideline recommendations
    - Identifies key clinical trials and their outcomes
    - Summarizes evidence strength for treatment options
    - Highlights recent updates and new approvals
    """

    # Mock guideline data
    NCCN_GUIDELINES = {
        "EGFR_mutant_NSCLC": {
            "first_line": [
                {
                    "treatment": "Osimertinib",
                    "recommendation": "Preferred",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on FLAURA trial; PFS 18.9 vs 10.2 months"
                },
                {
                    "treatment": "Erlotinib",
                    "recommendation": "Other recommended",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Alternative if osimertinib not available"
                },
            ],
            "progression": [
                {
                    "treatment": "Osimertinib (if not prior)",
                    "recommendation": "Preferred for T790M+",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on AURA3 trial"
                },
                {
                    "treatment": "Platinum-based chemotherapy",
                    "recommendation": "Preferred after osimertinib",
                    "evidence": EvidenceLevel.CATEGORY_2A,
                    "notes": "Standard second-line"
                },
            ]
        },
        "ALK_positive_NSCLC": {
            "first_line": [
                {
                    "treatment": "Alectinib",
                    "recommendation": "Preferred",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on ALEX trial; PFS 34.8 months"
                },
                {
                    "treatment": "Brigatinib",
                    "recommendation": "Preferred",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on ALTA-1L trial"
                },
                {
                    "treatment": "Lorlatinib",
                    "recommendation": "Preferred",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on CROWN trial; excellent CNS activity"
                },
            ]
        },
        "immunotherapy_NSCLC": {
            "pdl1_high": [
                {
                    "treatment": "Pembrolizumab monotherapy",
                    "recommendation": "Preferred for PD-L1 ≥50%",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on KEYNOTE-024"
                },
            ],
            "pdl1_low": [
                {
                    "treatment": "Pembrolizumab + chemotherapy",
                    "recommendation": "Preferred for PD-L1 1-49%",
                    "evidence": EvidenceLevel.CATEGORY_1,
                    "notes": "Based on KEYNOTE-189"
                },
            ]
        }
    }

    # Mock publications
    MOCK_PUBLICATIONS = [
        {
            "title": "Osimertinib in Untreated EGFR-Mutated Advanced Non–Small-Cell Lung Cancer",
            "authors": "Soria JC et al.",
            "journal": "N Engl J Med",
            "year": 2018,
            "pmid": "29151359",
            "key_finding": "Median PFS 18.9 months vs 10.2 months with erlotinib/gefitinib",
            "biomarker": "EGFR"
        },
        {
            "title": "Osimertinib or Platinum-Pemetrexed in EGFR T790M-Positive Lung Cancer",
            "authors": "Mok TS et al.",
            "journal": "N Engl J Med",
            "year": 2017,
            "pmid": "27959700",
            "key_finding": "Median PFS 10.1 months vs 4.4 months with chemotherapy in T790M+",
            "biomarker": "EGFR_T790M"
        },
        {
            "title": "Alectinib versus Crizotinib in Untreated ALK-Positive NSCLC",
            "authors": "Peters S et al.",
            "journal": "N Engl J Med",
            "year": 2017,
            "pmid": "28586279",
            "key_finding": "Median PFS not reached vs 11.1 months; better CNS activity",
            "biomarker": "ALK"
        },
        {
            "title": "Sotorasib for KRAS p.G12C-Mutated NSCLC",
            "authors": "Skoulidis F et al.",
            "journal": "N Engl J Med",
            "year": 2021,
            "pmid": "34096690",
            "key_finding": "ORR 37.1%, median PFS 6.8 months in previously treated patients",
            "biomarker": "KRAS_G12C"
        },
        {
            "title": "Pembrolizumab plus Chemotherapy in Metastatic NSCLC",
            "authors": "Gandhi L et al.",
            "journal": "N Engl J Med",
            "year": 2018,
            "pmid": "29658856",
            "key_finding": "Median OS 22.0 months vs 10.7 months; benefit regardless of PD-L1",
            "biomarker": "PD-L1"
        },
    ]

    def __init__(
        self,
        llm_service: LLMService,
        use_mock: bool = True,
        pubmed_service: Optional[PubMedService] = None
    ):
        super().__init__(
            name="evidence",
            llm_service=llm_service,
            use_mock=use_mock
        )
        self._pubmed_service = pubmed_service or get_pubmed_service()

    def get_system_prompt(self) -> str:
        return """You are a medical evidence specialist AI.
Your role is to:
1. Search medical literature databases (PubMed, Cochrane)
2. Retrieve current guideline recommendations (NCCN, ASCO, ESMO)
3. Identify landmark clinical trials and their outcomes
4. Assess evidence quality and applicability to specific patients
5. Highlight recent updates and emerging data

Be thorough and cite specific sources. Note evidence levels per NCCN categories.
Focus on high-quality evidence (RCTs, meta-analyses) when available."""

    async def execute(self, input_data: EvidenceInput) -> EvidenceOutput:
        """Execute evidence search using real PubMed API."""
        patient_summary = input_data.patient_summary
        genomics = input_data.genomics_result

        search_terms = []
        publications = []
        guideline_recs = []
        evidence_summaries = []
        recent_updates = []

        # Build search parameters from patient data
        cancer_type = ""
        biomarkers = []

        if patient_summary.cancer:
            cancer_type = patient_summary.cancer.cancer_type.value
            search_terms.append(cancer_type)
            search_terms.append(patient_summary.cancer.stage.value)

        # Extract biomarkers from genomics
        if genomics and genomics.report:
            for mutation in genomics.report.actionable_mutations:
                biomarkers.append(mutation.gene)
                search_terms.append(f"{mutation.gene} {mutation.variant}")

        try:
            # Search real PubMed API for each biomarker
            logger.info(f"Searching PubMed for: {cancer_type}, biomarkers: {biomarkers}")

            for biomarker in biomarkers[:3]:  # Limit to top 3 biomarkers
                pubmed_results = await self._pubmed_service.search_cancer_treatment(
                    cancer_type=cancer_type or "cancer",
                    biomarker=biomarker,
                    max_results=5
                )

                for pub in pubmed_results:
                    # Convert PubMed publication to our format
                    publications.append(Publication(
                        title=pub.title,
                        authors=", ".join(pub.authors[:3]) + (" et al." if len(pub.authors) > 3 else ""),
                        journal=pub.journal,
                        year=int(pub.publication_date.split("-")[0]) if pub.publication_date else 2024,
                        pmid=pub.pmid,
                        key_finding=pub.abstract[:300] + "..." if len(pub.abstract) > 300 else pub.abstract,
                        relevance_to_patient=f"Patient has {biomarker} mutation - study relevant to targeted therapy"
                    ))

            # Also do a general cancer type search if no biomarkers
            if not biomarkers and cancer_type:
                pubmed_results = await self._pubmed_service.search_cancer_treatment(
                    cancer_type=cancer_type,
                    max_results=10
                )
                for pub in pubmed_results[:5]:
                    publications.append(Publication(
                        title=pub.title,
                        authors=", ".join(pub.authors[:3]) + (" et al." if len(pub.authors) > 3 else ""),
                        journal=pub.journal,
                        year=int(pub.publication_date.split("-")[0]) if pub.publication_date else 2024,
                        pmid=pub.pmid,
                        key_finding=pub.abstract[:300] + "..." if len(pub.abstract) > 300 else pub.abstract,
                        relevance_to_patient=f"Study relevant to {cancer_type} treatment"
                    ))

            logger.info(f"Found {len(publications)} publications from PubMed")

            # Get hardcoded guideline recommendations (NCCN has no free API)
            guideline_recs = self._get_guideline_recommendations(biomarkers, patient_summary)

            # Use LLM to synthesize evidence from publications
            if publications:
                evidence_summaries = await self._synthesize_evidence(
                    publications, biomarkers, guideline_recs, input_data
                )

            # Get recent updates for biomarkers
            recent_updates = self._get_recent_updates(biomarkers)

            return EvidenceOutput(
                evidence_summaries=evidence_summaries,
                guideline_recommendations=guideline_recs,
                relevant_publications=publications[:15],  # Limit to 15
                recent_updates=recent_updates,
                search_terms_used=search_terms
            )

        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            # Fall back to mock if API fails
            logger.info("Falling back to mock data")
            return self._mock_execute(input_data)

    async def _synthesize_evidence(
        self,
        publications: List[Publication],
        biomarkers: List[str],
        guideline_recs: List[GuidelineRecommendation],
        input_data: EvidenceInput
    ) -> List[EvidenceSummary]:
        """Use LLM to synthesize evidence from publications."""
        evidence_summaries = []

        # If no publications or guidelines, return basic summaries immediately
        if not publications and not guideline_recs:
            logger.info("No publications or guidelines to synthesize, using basic summaries")
            return self._create_basic_summaries(biomarkers, guideline_recs, publications)

        # Build evidence synthesis prompt - keep it concise to avoid token issues
        pub_summaries = "\n".join([
            f"- {pub.title} ({pub.year}): {pub.key_finding[:150] if pub.key_finding else 'N/A'}"
            for pub in publications[:8]  # Limit to 8 publications
        ])

        guideline_summaries = "\n".join([
            f"- {rec.guideline}: {rec.recommendation} ({rec.evidence_level.value})"
            for rec in guideline_recs[:8]  # Limit to 8 guidelines
        ])

        cancer_type = "Unknown"
        cancer_stage = "Unknown"
        if input_data.patient_summary.cancer:
            cancer_type = input_data.patient_summary.cancer.cancer_type.value
            cancer_stage = input_data.patient_summary.cancer.stage.value

        prompt = f"""Summarize evidence for this patient:
Cancer: {cancer_type}, Stage: {cancer_stage}
Biomarkers: {', '.join(biomarkers[:5]) if biomarkers else 'None'}

Publications:
{pub_summaries[:2000]}

Guidelines:
{guideline_summaries[:1000]}

Return JSON array with 2-4 treatment evidence summaries:
[{{"treatment":"name","key_trials":["trial1","trial2"],"guideline_recommendation":"rec","evidence_strength":"Category 1/2A","applicability":"how applies","summary":"summary"}}]"""

        try:
            response = await self.llm_service.complete(
                prompt=prompt,
                system_prompt="You are a medical evidence specialist. Return ONLY valid JSON array, no markdown or extra text.",
                temperature=0.2,
                max_tokens=1500  # Limit response size
            )

            # Check for empty response
            if not response or not response.strip():
                logger.warning("Empty response from LLM in evidence synthesis")
                return self._create_basic_summaries(biomarkers, guideline_recs, publications)

            # Parse LLM response
            import json
            import re

            # Clean the response - remove markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Remove markdown code blocks
                clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)

            # Extract JSON array from response - robust extraction with proper bracket matching
            json_text = self._extract_json_array(clean_response)
            if not json_text:
                logger.warning(f"No JSON array found in response: {clean_response[:200]}")
                return self._create_basic_summaries(biomarkers, guideline_recs, publications)

            # Try to parse JSON with multiple fallback strategies
            evidence_list = None
            parse_errors = []

            # Strategy 1: Direct parse
            try:
                evidence_list = json.loads(json_text)
            except json.JSONDecodeError as e:
                parse_errors.append(f"Direct: {e}")

            # Strategy 2: Clean whitespace and control characters
            if evidence_list is None:
                try:
                    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_text)
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    evidence_list = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    parse_errors.append(f"Cleaned: {e}")

            # Strategy 3: Fix common issues (trailing commas, single quotes)
            if evidence_list is None:
                try:
                    fixed = re.sub(r',\s*]', ']', json_text)
                    fixed = re.sub(r',\s*}', '}', fixed)
                    fixed = fixed.replace("'", '"')
                    evidence_list = json.loads(fixed)
                except json.JSONDecodeError as e:
                    parse_errors.append(f"Fixed: {e}")

            if evidence_list is None:
                logger.warning(f"All JSON parse strategies failed: {parse_errors}")
                return self._create_basic_summaries(biomarkers, guideline_recs, publications)

            # Process evidence list
            for ev in evidence_list:
                if not isinstance(ev, dict):
                    continue

                # Map evidence strength string to enum
                strength_str = str(ev.get("evidence_strength", "Category 2A")).lower()
                if "category 1" in strength_str or "category_1" in strength_str or "1" == strength_str:
                    strength = EvidenceLevel.CATEGORY_1
                elif "category 2b" in strength_str or "category_2b" in strength_str or "2b" in strength_str:
                    strength = EvidenceLevel.CATEGORY_2B
                elif "category 3" in strength_str or "category_3" in strength_str or "3" == strength_str:
                    strength = EvidenceLevel.CATEGORY_3
                else:
                    strength = EvidenceLevel.CATEGORY_2A

                # Build key trials list safely
                key_trials_raw = ev.get("key_trials", [])
                if isinstance(key_trials_raw, list):
                    key_trials = [{"name": str(t), "result": ""} for t in key_trials_raw if t]
                else:
                    key_trials = []

                # Build guideline recommendations safely
                guideline_rec = ev.get("guideline_recommendation", "")
                guideline_recommendations = []
                if guideline_rec:
                    guideline_recommendations = [{"source": "NCCN", "recommendation": str(guideline_rec)}]

                evidence_summaries.append(EvidenceSummary(
                    treatment=str(ev.get("treatment", "Unknown treatment")),
                    key_trials=key_trials,
                    guideline_recommendations=guideline_recommendations,
                    meta_analyses=[],
                    recent_updates=[],
                    evidence_strength=strength,
                    applicability_to_patient=str(ev.get("applicability", "Applicable based on patient profile")),
                    summary=str(ev.get("summary", "Evidence supports this treatment option."))
                ))

            # If we successfully parsed but got no summaries, use basic
            if not evidence_summaries:
                logger.warning("Parsed JSON but no valid evidence summaries")
                return self._create_basic_summaries(biomarkers, guideline_recs, publications)

            return evidence_summaries

        except Exception as e:
            logger.error(f"Error synthesizing evidence: {e}")
            return self._create_basic_summaries(biomarkers, guideline_recs, publications)

    def _extract_json_array(self, text: str) -> Optional[str]:
        """Extract JSON array from text with proper bracket matching.

        Args:
            text: The text to extract JSON from

        Returns:
            The extracted JSON string or None if not found
        """
        # Find the start of the array
        start = text.find('[')
        if start == -1:
            return None

        # Find matching end bracket by counting
        depth = 0
        in_string = False
        escape_next = False
        end = start

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if depth != 0:
            # Unbalanced brackets - try to find what we can
            logger.warning(f"Unbalanced brackets in JSON, depth={depth}")
            return None

        return text[start:end]

    def _create_basic_summaries(
        self,
        biomarkers: List[str],
        guideline_recs: List[GuidelineRecommendation],
        publications: List[Publication]
    ) -> List[EvidenceSummary]:
        """Create basic evidence summaries without LLM."""
        summaries = []
        for biomarker in biomarkers:
            matching_pubs = [p for p in publications if biomarker.lower() in p.relevance_to_patient.lower()]
            matching_recs = [g for g in guideline_recs if biomarker.lower() in g.recommendation.lower()]

            if matching_pubs or matching_recs:
                summaries.append(EvidenceSummary(
                    treatment=f"{biomarker}-targeted therapy",
                    key_trials=[{"title": p.title, "finding": p.key_finding} for p in matching_pubs[:3]],
                    guideline_recommendations=[
                        {"source": g.guideline, "recommendation": g.recommendation}
                        for g in matching_recs[:3]
                    ],
                    meta_analyses=[],
                    recent_updates=[],
                    evidence_strength=EvidenceLevel.CATEGORY_1 if matching_recs else EvidenceLevel.CATEGORY_2A,
                    applicability_to_patient=f"Patient has {biomarker} mutation",
                    summary=f"Found {len(matching_pubs)} publications and {len(matching_recs)} guideline recommendations for {biomarker}-targeted therapy."
                ))
        return summaries

    def _mock_execute(self, input_data: EvidenceInput) -> EvidenceOutput:
        """Generate mock evidence search results."""
        patient_summary = input_data.patient_summary
        genomics = input_data.genomics_result

        search_terms = []
        guideline_recs = []
        publications = []
        evidence_summaries = []
        recent_updates = []

        # Determine relevant biomarkers
        biomarkers = []
        if genomics and genomics.report:
            for mutation in genomics.report.actionable_mutations:
                biomarkers.append(mutation.gene)
                search_terms.append(f"{mutation.gene} {mutation.variant}")

        # Add cancer type search terms
        if patient_summary.cancer:
            search_terms.append(patient_summary.cancer.cancer_type.value)
            search_terms.append(patient_summary.cancer.stage.value)

        # Get relevant guideline recommendations
        guideline_recs = self._get_guideline_recommendations(biomarkers, patient_summary)

        # Get relevant publications
        publications = self._get_relevant_publications(biomarkers)

        # Build evidence summaries for treatment queries
        for query in input_data.treatment_queries:
            summary = self._build_evidence_summary(query, guideline_recs, publications)
            evidence_summaries.append(summary)

        # If no specific queries, create summaries for identified biomarkers
        if not input_data.treatment_queries and biomarkers:
            for biomarker in biomarkers:
                summary = self._create_biomarker_summary(biomarker, guideline_recs, publications)
                if summary:
                    evidence_summaries.append(summary)

        # Recent updates
        recent_updates = self._get_recent_updates(biomarkers)

        return EvidenceOutput(
            evidence_summaries=evidence_summaries,
            guideline_recommendations=guideline_recs,
            relevant_publications=publications,
            recent_updates=recent_updates,
            search_terms_used=search_terms
        )

    def _get_guideline_recommendations(
        self,
        biomarkers: List[str],
        patient_summary: PatientSummary
    ) -> List[GuidelineRecommendation]:
        """Get relevant guideline recommendations."""
        recommendations = []

        for biomarker in biomarkers:
            if biomarker == "EGFR":
                recs = self.NCCN_GUIDELINES.get("EGFR_mutant_NSCLC", {})
                for line, treatments in recs.items():
                    for tx in treatments:
                        recommendations.append(GuidelineRecommendation(
                            guideline="NCCN NSCLC v2.2024",
                            recommendation=f"{tx['treatment']}: {tx['recommendation']} ({line.replace('_', ' ')})",
                            evidence_level=tx['evidence'],
                            applicable_to_patient=True,
                            notes=tx['notes']
                        ))

            elif biomarker == "ALK":
                recs = self.NCCN_GUIDELINES.get("ALK_positive_NSCLC", {})
                for line, treatments in recs.items():
                    for tx in treatments:
                        recommendations.append(GuidelineRecommendation(
                            guideline="NCCN NSCLC v2.2024",
                            recommendation=f"{tx['treatment']}: {tx['recommendation']} ({line.replace('_', ' ')})",
                            evidence_level=tx['evidence'],
                            applicable_to_patient=True,
                            notes=tx['notes']
                        ))

        return recommendations

    def _get_relevant_publications(self, biomarkers: List[str]) -> List[Publication]:
        """Get relevant publications for biomarkers."""
        publications = []

        for pub in self.MOCK_PUBLICATIONS:
            pub_biomarker = pub.get("biomarker", "")
            for biomarker in biomarkers:
                if biomarker.lower() in pub_biomarker.lower():
                    publications.append(Publication(
                        title=pub["title"],
                        authors=pub["authors"],
                        journal=pub["journal"],
                        year=pub["year"],
                        pmid=pub.get("pmid"),
                        key_finding=pub["key_finding"],
                        relevance_to_patient=f"Patient has {biomarker} mutation - this study directly applies"
                    ))
                    break

        return publications

    def _build_evidence_summary(
        self,
        query: str,
        guideline_recs: List[GuidelineRecommendation],
        publications: List[Publication]
    ) -> EvidenceSummary:
        """Build evidence summary for a treatment query."""
        # Find matching guidelines
        matching_guidelines = [
            {"source": g.guideline, "recommendation": g.recommendation, "notes": g.notes}
            for g in guideline_recs
            if query.lower() in g.recommendation.lower()
        ]

        # Find matching publications
        matching_pubs = [
            {"title": p.title, "finding": p.key_finding}
            for p in publications
            if query.lower() in p.title.lower() or query.lower() in p.key_finding.lower()
        ]

        # Determine evidence strength
        evidence_strength = EvidenceLevel.CATEGORY_2A
        if matching_guidelines:
            for g in guideline_recs:
                if query.lower() in g.recommendation.lower():
                    evidence_strength = g.evidence_level
                    break

        return EvidenceSummary(
            treatment=query,
            key_trials=[{"name": p.title, "result": p.key_finding} for p in publications[:3]],
            guideline_recommendations=matching_guidelines,
            meta_analyses=[],
            recent_updates=[],
            evidence_strength=evidence_strength,
            applicability_to_patient="Directly applicable based on mutation profile",
            summary=f"Evidence supports use of {query} based on {len(matching_pubs)} key trials and {len(matching_guidelines)} guideline recommendations."
        )

    def _create_biomarker_summary(
        self,
        biomarker: str,
        guideline_recs: List[GuidelineRecommendation],
        publications: List[Publication]
    ) -> Optional[EvidenceSummary]:
        """Create evidence summary for a biomarker."""
        matching_pubs = [p for p in publications if biomarker.lower() in p.relevance_to_patient.lower()]
        matching_guidelines = [g for g in guideline_recs if biomarker.lower() in g.recommendation.lower()]

        if not matching_pubs and not matching_guidelines:
            return None

        return EvidenceSummary(
            treatment=f"{biomarker}-targeted therapy",
            key_trials=[{"title": p.title, "finding": p.key_finding} for p in matching_pubs],
            guideline_recommendations=[
                {"source": g.guideline, "recommendation": g.recommendation}
                for g in matching_guidelines
            ],
            meta_analyses=[],
            recent_updates=[],
            evidence_strength=EvidenceLevel.CATEGORY_1,
            applicability_to_patient=f"Patient has {biomarker} mutation - all evidence directly applicable",
            summary=f"Strong evidence for {biomarker}-targeted therapy with Category 1 recommendations from NCCN."
        )

    def _get_recent_updates(self, biomarkers: List[str]) -> List[str]:
        """Get recent updates relevant to patient."""
        updates = []

        if "EGFR" in biomarkers:
            updates.extend([
                "2024: FDA approved amivantamab + lazertinib for EGFR-mutant NSCLC after osimertinib",
                "2023: FLAURA2 showed benefit of osimertinib + chemotherapy combination",
            ])

        if "KRAS" in biomarkers:
            updates.extend([
                "2024: Adagrasib + pembrolizumab combination showing promise in early data",
            ])

        if "ALK" in biomarkers:
            updates.extend([
                "2024: CROWN trial 5-year update confirms lorlatinib durability",
            ])

        return updates

    def _build_search_prompt(self, input_data: EvidenceInput) -> str:
        """Build search prompt."""
        return f"""Search medical literature and guidelines for this patient:

Patient Summary:
{input_data.patient_summary.model_dump_json(indent=2)}

Genomics:
{input_data.genomics_result.model_dump_json(indent=2) if input_data.genomics_result else 'Not available'}

Treatment Queries: {input_data.treatment_queries}

Please provide evidence summaries with:
1. Key clinical trial results
2. Guideline recommendations with evidence levels
3. Recent updates and emerging data
4. Applicability to this specific patient"""
