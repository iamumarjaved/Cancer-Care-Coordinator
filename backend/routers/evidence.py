"""Evidence API Router - Returns AI-generated analysis results and PubMed search."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models.db_models import AnalysisResultDB
from models.treatment import EvidenceLevel
from services.pubmed_service import get_pubmed_service, Publication as PubMedPublication

router = APIRouter()
logger = logging.getLogger(__name__)


class Publication(BaseModel):
    """Medical publication."""
    pmid: str = ""
    title: str
    abstract: str = ""
    authors: List[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    url: str = ""
    relevance: str = ""


class GuidelineRecommendation(BaseModel):
    """Clinical guideline recommendation."""
    guideline: str = ""
    source: str = ""
    version: str = ""
    recommendation: str
    evidence_level: str = ""
    applicable: bool = True
    notes: str = ""


class EvidenceSummaryItem(BaseModel):
    """Evidence summary for a treatment."""
    treatment: str
    evidence_strength: str = ""
    key_trials: List[dict] = Field(default_factory=list)
    guideline_recommendations: List[dict] = Field(default_factory=list)
    summary: str = ""
    applicability_to_patient: str = ""


class PatientEvidenceResponse(BaseModel):
    """Evidence summary response for a patient."""
    patient_id: str
    publications: List[Publication] = Field(default_factory=list)
    guidelines: List[GuidelineRecommendation] = Field(default_factory=list)
    evidence_summaries: List[EvidenceSummaryItem] = Field(default_factory=list)
    search_terms: List[str] = Field(default_factory=list)
    sources_used: List[str] = Field(default_factory=list)


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


@router.get("/patients/{patient_id}/evidence", response_model=PatientEvidenceResponse)
async def get_patient_evidence(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get evidence summary for a patient from AI analysis.

    Args:
        patient_id: The patient ID

    Returns:
        Evidence including publications, guidelines, and summaries from AI analysis
    """
    analysis_data = await get_latest_analysis(patient_id, db)

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis found for patient {patient_id}. Run an analysis first."
        )

    evidence_summary = analysis_data.get("evidence_summary", {})

    # Extract evidence summaries
    evidence_summaries = []
    raw_summaries = evidence_summary.get("evidence_summaries", []) if evidence_summary else []
    for es in raw_summaries:
        evidence_summaries.append(EvidenceSummaryItem(
            treatment=es.get("treatment", "Unknown"),
            evidence_strength=es.get("evidence_strength", ""),
            key_trials=es.get("key_trials", []),
            guideline_recommendations=es.get("guideline_recommendations", []),
            summary=es.get("summary", ""),
            applicability_to_patient=es.get("applicability_to_patient", "")
        ))

    # Extract publications from evidence
    publications = []
    raw_publications = evidence_summary.get("publications", []) if evidence_summary else []
    for pub in raw_publications:
        publications.append(Publication(
            pmid=pub.get("pmid", ""),
            title=pub.get("title", pub.get("name", "")),
            abstract=pub.get("abstract", ""),
            authors=pub.get("authors", []),
            journal=pub.get("journal", ""),
            publication_date=pub.get("publication_date", pub.get("year", "")),
            doi=pub.get("doi", ""),
            url=pub.get("url", ""),
            relevance=pub.get("relevance", pub.get("result", ""))
        ))

    # Also check for key trials in evidence summaries and add them as publications
    for es in raw_summaries:
        for trial in es.get("key_trials", []):
            if isinstance(trial, dict):
                publications.append(Publication(
                    title=trial.get("name", trial.get("title", "")),
                    journal=trial.get("journal", ""),
                    relevance=trial.get("result", "")
                ))

    # Extract guidelines
    guidelines = []
    raw_guidelines = evidence_summary.get("guidelines", []) if evidence_summary else []
    for gl in raw_guidelines:
        guidelines.append(GuidelineRecommendation(
            guideline=gl.get("guideline", gl.get("source", "")),
            source=gl.get("source", ""),
            recommendation=gl.get("recommendation", ""),
            evidence_level=gl.get("evidence_level", ""),
            notes=gl.get("notes", "")
        ))

    # Also extract guideline_recommendations from evidence_summaries
    for es in raw_summaries:
        for gr in es.get("guideline_recommendations", []):
            if isinstance(gr, dict):
                guidelines.append(GuidelineRecommendation(
                    guideline=gr.get("guideline", ""),
                    source=gr.get("source", ""),
                    recommendation=gr.get("recommendation", ""),
                    evidence_level=gr.get("evidence_level", "")
                ))

    return PatientEvidenceResponse(
        patient_id=patient_id,
        publications=publications,
        guidelines=guidelines,
        evidence_summaries=evidence_summaries,
        search_terms=evidence_summary.get("search_terms_used", []) if evidence_summary else [],
        sources_used=analysis_data.get("sources_used", [])
    )


@router.get("/evidence/search")
async def search_evidence(
    query: str = Query(..., description="Search query"),
    cancer_type: Optional[str] = Query(None, description="Cancer type filter"),
    biomarker: Optional[str] = Query(None, description="Biomarker filter"),
    drug: Optional[str] = Query(None, description="Drug filter"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum results")
):
    """Search medical literature for evidence using PubMed.

    Args:
        query: Search query
        cancer_type: Optional cancer type filter
        biomarker: Optional biomarker filter
        drug: Optional drug filter
        max_results: Maximum number of results

    Returns:
        List of matching publications from PubMed
    """
    pubmed_service = get_pubmed_service()

    try:
        # Build search query
        search_parts = [query]
        if cancer_type:
            search_parts.append(cancer_type)
        if biomarker:
            search_parts.append(biomarker)
        if drug:
            search_parts.append(drug)

        full_query = " AND ".join(search_parts)

        # Search PubMed
        results = await pubmed_service.search_publications(
            query=full_query,
            max_results=max_results
        )

        # Convert to response format
        publications = []
        for pub in results:
            publications.append(Publication(
                pmid=pub.pmid,
                title=pub.title,
                abstract=pub.abstract,
                authors=pub.authors,
                journal=pub.journal,
                publication_date=pub.publication_date,
                doi=pub.doi,
                url=pub.url,
                relevance=""
            ))

        return {
            "query": full_query,
            "total_results": len(publications),
            "publications": publications
        }

    except Exception as e:
        logger.error(f"Error searching evidence: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching medical literature: {str(e)}"
        )


@router.get("/evidence/publication/{pmid}")
async def get_publication_details(pmid: str):
    """Get detailed information about a publication from PubMed.

    Args:
        pmid: PubMed ID

    Returns:
        Publication details
    """
    pubmed_service = get_pubmed_service()

    try:
        pub = await pubmed_service.get_article_details(pmid)

        if not pub:
            raise HTTPException(
                status_code=404,
                detail=f"Publication {pmid} not found"
            )

        return Publication(
            pmid=pub.pmid,
            title=pub.title,
            abstract=pub.abstract,
            authors=pub.authors,
            journal=pub.journal,
            publication_date=pub.publication_date,
            doi=pub.doi,
            url=pub.url,
            relevance=""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching publication {pmid}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching publication: {str(e)}"
        )


@router.get("/evidence/guidelines")
async def get_guidelines(
    cancer_type: str = Query(..., description="Cancer type"),
    biomarker: Optional[str] = Query(None, description="Biomarker filter")
):
    """Get clinical guideline recommendations.

    Args:
        cancer_type: Cancer type
        biomarker: Optional biomarker filter

    Returns:
        List of guideline recommendations

    Note:
        NCCN guidelines are not freely available via API.
        This returns commonly referenced guideline summaries.
    """
    guidelines = []

    cancer_lower = cancer_type.lower()
    biomarker_lower = (biomarker or "").lower()

    if "nsclc" in cancer_lower or "lung" in cancer_lower:
        if "egfr" in biomarker_lower or not biomarker:
            guidelines.append(GuidelineRecommendation(
                guideline="NCCN Non-Small Cell Lung Cancer",
                source="NCCN",
                version="v2.2024",
                recommendation="Osimertinib is preferred first-line therapy for EGFR sensitizing mutations",
                evidence_level="Category 1",
                applicable=True,
                notes="Based on FLAURA trial"
            ))

        if "alk" in biomarker_lower or not biomarker:
            guidelines.append(GuidelineRecommendation(
                guideline="NCCN Non-Small Cell Lung Cancer",
                source="NCCN",
                version="v2.2024",
                recommendation="Alectinib, brigatinib, or lorlatinib are preferred first-line options for ALK+ NSCLC",
                evidence_level="Category 1",
                applicable=True,
                notes="Based on ALEX, ALTA-1L, and CROWN trials"
            ))

        if "kras" in biomarker_lower:
            guidelines.append(GuidelineRecommendation(
                guideline="NCCN Non-Small Cell Lung Cancer",
                source="NCCN",
                version="v2.2024",
                recommendation="Sotorasib or adagrasib for KRAS G12C-mutated NSCLC after prior systemic therapy",
                evidence_level="Category 2A",
                applicable=True,
                notes="FDA approved based on CodeBreaK and KRYSTAL trials"
            ))

        if "pd-l1" in biomarker_lower or "pdl1" in biomarker_lower or not biomarker:
            guidelines.append(GuidelineRecommendation(
                guideline="NCCN Non-Small Cell Lung Cancer",
                source="NCCN",
                version="v2.2024",
                recommendation="Pembrolizumab monotherapy for PD-L1 >= 50% without EGFR/ALK alterations",
                evidence_level="Category 1",
                applicable=True,
                notes="Based on KEYNOTE-024 trial"
            ))

    if "breast" in cancer_lower:
        if "her2" in biomarker_lower or not biomarker:
            guidelines.append(GuidelineRecommendation(
                guideline="NCCN Breast Cancer",
                source="NCCN",
                version="v4.2024",
                recommendation="Trastuzumab-based regimens are standard for HER2+ breast cancer",
                evidence_level="Category 1",
                applicable=True,
                notes="Multiple trials support anti-HER2 therapy"
            ))

    return {
        "cancer_type": cancer_type,
        "biomarker": biomarker,
        "total_guidelines": len(guidelines),
        "guidelines": guidelines
    }
