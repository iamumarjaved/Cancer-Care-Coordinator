"""PubMed/NCBI API Service.

This service integrates with the NCBI E-utilities API to search for
and retrieve medical literature from PubMed.

API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

import httpx
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

# NCBI E-utilities base URL
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class Author(BaseModel):
    """Publication author."""
    name: str
    affiliation: str = ""


class Publication(BaseModel):
    """PubMed publication."""
    pmid: str
    title: str
    abstract: str = ""
    authors: List[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    publication_types: List[str] = Field(default_factory=list)
    mesh_terms: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    url: str = ""


class PubMedService:
    """Service for searching PubMed.

    Uses the NCBI E-utilities API to search for and retrieve
    medical literature relevant to cancer treatment decisions.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """Initialize the service.

        Args:
            api_key: NCBI API key (optional, increases rate limit)
            timeout: HTTP request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def search_publications(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance",
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        publication_types: Optional[List[str]] = None,
    ) -> List[Publication]:
        """Search PubMed for publications.

        Args:
            query: Search query (e.g., "EGFR NSCLC osimertinib treatment")
            max_results: Maximum number of results (default: 20)
            sort: Sort order ("relevance" or "date")
            min_date: Minimum publication date (YYYY/MM/DD format)
            max_date: Maximum publication date (YYYY/MM/DD format)
            publication_types: Filter by publication type (e.g., ["Clinical Trial", "Review"])

        Returns:
            List of matching publications
        """
        try:
            # Step 1: Search for PMIDs
            pmids = await self._search_pmids(
                query=query,
                max_results=max_results,
                sort=sort,
                min_date=min_date,
                max_date=max_date
            )

            if not pmids:
                logger.info(f"No publications found for query: {query}")
                return []

            # Step 2: Fetch details for each PMID
            publications = await self._fetch_details(pmids)

            # Step 3: Filter by publication type if specified
            if publication_types:
                publications = [
                    pub for pub in publications
                    if any(pt in pub.publication_types for pt in publication_types)
                ]

            logger.info(f"Found {len(publications)} publications for query: {query}")
            return publications

        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []

    async def _search_pmids(
        self,
        query: str,
        max_results: int,
        sort: str,
        min_date: Optional[str],
        max_date: Optional[str]
    ) -> List[str]:
        """Search PubMed and return PMIDs.

        Args:
            query: Search query
            max_results: Maximum results
            sort: Sort order
            min_date: Minimum date
            max_date: Maximum date

        Returns:
            List of PMIDs
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "sort": sort,
            "retmode": "json",
        }

        if self._api_key:
            params["api_key"] = self._api_key

        if min_date:
            params["mindate"] = min_date
        if max_date:
            params["maxdate"] = max_date

        response = await self._client.get(
            f"{NCBI_EUTILS_BASE}/esearch.fcgi",
            params=params
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("esearchresult", {})
        pmids = result.get("idlist", [])

        return pmids

    async def _fetch_details(self, pmids: List[str]) -> List[Publication]:
        """Fetch publication details for PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of Publication objects
        """
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        if self._api_key:
            params["api_key"] = self._api_key

        response = await self._client.get(
            f"{NCBI_EUTILS_BASE}/efetch.fcgi",
            params=params
        )
        response.raise_for_status()

        # Parse XML response
        publications = self._parse_pubmed_xml(response.text)
        return publications

    def _parse_pubmed_xml(self, xml_text: str) -> List[Publication]:
        """Parse PubMed XML response.

        Args:
            xml_text: XML response text

        Returns:
            List of Publication objects
        """
        publications = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                try:
                    pub = self._parse_article(article)
                    if pub:
                        publications.append(pub)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue

        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")

        return publications

    def _parse_article(self, article: ET.Element) -> Optional[Publication]:
        """Parse a single PubMed article.

        Args:
            article: XML element for PubmedArticle

        Returns:
            Publication object or None
        """
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""
        if not pmid:
            return None

        article_elem = medline.find("Article")
        if article_elem is None:
            return None

        # Title
        title_elem = article_elem.find("ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""

        # Abstract
        abstract_elem = article_elem.find(".//AbstractText")
        abstract = ""
        if abstract_elem is not None:
            abstract = "".join(abstract_elem.itertext())
        else:
            # Try to get multiple abstract sections
            abstract_parts = []
            for abs_text in article_elem.findall(".//AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

        # Authors
        authors = []
        for author in article_elem.findall(".//Author"):
            last_name = author.findtext("LastName", "")
            fore_name = author.findtext("ForeName", "")
            if last_name:
                name = f"{last_name} {fore_name}".strip()
                authors.append(name)

        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # Publication date
        pub_date = ""
        pub_date_elem = article_elem.find(".//PubDate")
        if pub_date_elem is not None:
            year = pub_date_elem.findtext("Year", "")
            month = pub_date_elem.findtext("Month", "")
            day = pub_date_elem.findtext("Day", "")
            pub_date = f"{year}-{month}-{day}".strip("-")

        # DOI
        doi = ""
        for id_elem in article_elem.findall(".//ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text or ""
                break

        # Publication types
        pub_types = []
        for pt in article_elem.findall(".//PublicationType"):
            if pt.text:
                pub_types.append(pt.text)

        # MeSH terms
        mesh_terms = []
        for mesh in medline.findall(".//MeshHeading/DescriptorName"):
            if mesh.text:
                mesh_terms.append(mesh.text)

        # Keywords
        keywords = []
        for kw in medline.findall(".//Keyword"):
            if kw.text:
                keywords.append(kw.text)

        return Publication(
            pmid=pmid,
            title=title,
            abstract=abstract,
            authors=authors[:10],  # Limit to first 10 authors
            journal=journal,
            publication_date=pub_date,
            doi=doi,
            publication_types=pub_types,
            mesh_terms=mesh_terms[:20],  # Limit MeSH terms
            keywords=keywords[:20],  # Limit keywords
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        )

    async def get_article_details(self, pmid: str) -> Optional[Publication]:
        """Get detailed information about a specific article.

        Args:
            pmid: PubMed ID

        Returns:
            Publication details or None
        """
        publications = await self._fetch_details([pmid])
        return publications[0] if publications else None

    async def get_abstracts(self, pmids: List[str]) -> Dict[str, str]:
        """Get abstracts for multiple PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            Dictionary mapping PMID to abstract text
        """
        publications = await self._fetch_details(pmids)
        return {pub.pmid: pub.abstract for pub in publications}

    async def search_cancer_treatment(
        self,
        cancer_type: str,
        biomarker: Optional[str] = None,
        drug: Optional[str] = None,
        max_results: int = 15
    ) -> List[Publication]:
        """Search for cancer treatment publications.

        Optimized search for cancer treatment literature.

        Args:
            cancer_type: Cancer type (e.g., "NSCLC", "breast cancer")
            biomarker: Biomarker/mutation (e.g., "EGFR", "HER2")
            drug: Drug name (e.g., "osimertinib")
            max_results: Maximum results

        Returns:
            List of relevant publications
        """
        # Build optimized query
        query_parts = [f"{cancer_type}[Title/Abstract]"]

        if biomarker:
            query_parts.append(f"{biomarker}[Title/Abstract]")

        if drug:
            query_parts.append(f"{drug}[Title/Abstract]")

        # Add treatment-related terms
        query_parts.append("(treatment OR therapy OR efficacy OR outcome)")

        query = " AND ".join(query_parts)

        # Search with clinical relevance filters
        return await self.search_publications(
            query=query,
            max_results=max_results,
            sort="relevance",
            publication_types=["Clinical Trial", "Review", "Meta-Analysis", "Randomized Controlled Trial"]
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
_service: Optional[PubMedService] = None


def get_pubmed_service(api_key: Optional[str] = None) -> PubMedService:
    """Get or create the PubMed service instance.

    Args:
        api_key: Optional NCBI API key

    Returns:
        PubMedService instance
    """
    global _service
    if _service is None:
        _service = PubMedService(api_key=api_key)
    return _service
