"""ClinicalTrials.gov API Service.

This service integrates with the ClinicalTrials.gov API v2 to search for
and retrieve clinical trial information for cancer patients.

API Documentation: https://clinicaltrials.gov/data-api/api
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

# ClinicalTrials.gov API v2 base URL
CLINICALTRIALS_API_BASE = "https://clinicaltrials.gov/api/v2"


class TrialLocation(BaseModel):
    """Clinical trial location."""
    facility: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    status: str = ""


class EligibilityCriterion(BaseModel):
    """Eligibility criterion for a trial."""
    type: str  # "inclusion" or "exclusion"
    description: str
    met: Optional[bool] = None  # Whether patient meets this criterion


class ClinicalTrialResult(BaseModel):
    """Clinical trial search result."""
    nct_id: str
    title: str
    brief_summary: str = ""
    phase: str = ""
    status: str = ""
    conditions: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)
    sponsor: str = ""
    locations: List[TrialLocation] = Field(default_factory=list)
    eligibility_criteria_text: str = ""
    eligibility_criteria: List[EligibilityCriterion] = Field(default_factory=list)
    enrollment: Optional[int] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    last_update: Optional[str] = None
    url: str = ""


class ClinicalTrialsService:
    """Service for searching ClinicalTrials.gov.

    Uses the ClinicalTrials.gov API v2 to search for clinical trials
    that may be relevant to a cancer patient based on their diagnosis,
    biomarkers, and other clinical factors.
    """

    def __init__(self, timeout: float = 30.0):
        """Initialize the service.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def search_trials(
        self,
        condition: str,
        intervention: Optional[str] = None,
        status: str = "RECRUITING",
        location_country: Optional[str] = "United States",
        max_results: int = 50,
        biomarkers: Optional[List[str]] = None,
    ) -> List[ClinicalTrialResult]:
        """Search for clinical trials.

        Args:
            condition: Cancer condition (e.g., "NSCLC", "Non-Small Cell Lung Cancer")
            intervention: Drug or intervention name (optional)
            status: Trial status filter (default: RECRUITING)
            location_country: Country filter (default: United States)
            max_results: Maximum number of results to return
            biomarkers: List of biomarkers/mutations to search for

        Returns:
            List of matching clinical trials
        """
        try:
            # Build search query
            query_parts = [condition]
            if biomarkers:
                query_parts.extend(biomarkers)

            # Build API parameters
            params = {
                "format": "json",
                "pageSize": min(max_results, 100),  # API max is 100
                "query.cond": condition,
            }

            # Add intervention filter if specified
            if intervention:
                params["query.intr"] = intervention

            # Add status filter
            if status:
                params["filter.overallStatus"] = status

            # Add location filter
            if location_country:
                params["filter.geo"] = f"distance(0,0,10000mi)"  # Global search
                # Note: API uses geo-based filtering, country filter via post-processing

            logger.info(f"Searching ClinicalTrials.gov: {params}")

            # Make API request
            response = await self._client.get(
                f"{CLINICALTRIALS_API_BASE}/studies",
                params=params
            )
            response.raise_for_status()

            data = response.json()
            studies = data.get("studies", [])

            # Parse results
            trials = []
            for study in studies:
                try:
                    trial = self._parse_study(study)
                    if trial:
                        # Filter by country if specified
                        if location_country:
                            has_country = any(
                                loc.country.lower() == location_country.lower()
                                for loc in trial.locations
                            ) if trial.locations else True  # Include if no locations listed
                            if not has_country:
                                continue
                        trials.append(trial)
                except Exception as e:
                    logger.warning(f"Failed to parse study: {e}")
                    continue

            logger.info(f"Found {len(trials)} trials matching criteria")
            return trials[:max_results]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching ClinicalTrials.gov: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching ClinicalTrials.gov: {e}")
            return []

    async def get_trial_details(self, nct_id: str) -> Optional[ClinicalTrialResult]:
        """Get detailed information about a specific trial.

        Args:
            nct_id: The NCT identifier (e.g., "NCT04487080")

        Returns:
            Trial details or None if not found
        """
        try:
            response = await self._client.get(
                f"{CLINICALTRIALS_API_BASE}/studies/{nct_id}",
                params={"format": "json"}
            )
            response.raise_for_status()

            data = response.json()
            return self._parse_study(data)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching trial {nct_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching trial {nct_id}: {e}")
            return None

    async def search_by_biomarker(
        self,
        cancer_type: str,
        biomarker: str,
        status: str = "RECRUITING",
        max_results: int = 20
    ) -> List[ClinicalTrialResult]:
        """Search for trials targeting a specific biomarker.

        Args:
            cancer_type: Cancer type (e.g., "NSCLC")
            biomarker: Biomarker/mutation (e.g., "EGFR", "ALK fusion")
            status: Trial status filter
            max_results: Maximum results

        Returns:
            List of matching trials
        """
        # Build combined query
        query = f"{cancer_type} {biomarker}"
        return await self.search_trials(
            condition=query,
            status=status,
            max_results=max_results,
            biomarkers=[biomarker]
        )

    def _parse_study(self, study_data: Dict[str, Any]) -> Optional[ClinicalTrialResult]:
        """Parse a study from API response.

        Args:
            study_data: Raw study data from API

        Returns:
            Parsed ClinicalTrialResult or None
        """
        try:
            # Extract protocol section
            protocol = study_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            description = protocol.get("descriptionModule", {})
            conditions_module = protocol.get("conditionsModule", {})
            arms_module = protocol.get("armsInterventionsModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            contacts = protocol.get("contactsLocationsModule", {})
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            design = protocol.get("designModule", {})

            # Get NCT ID
            nct_id = identification.get("nctId", "")
            if not nct_id:
                return None

            # Parse phases
            phases = design.get("phases", [])
            phase = ", ".join(phases) if phases else "Not specified"

            # Parse interventions
            interventions = []
            for arm in arms_module.get("interventions", []):
                name = arm.get("name", "")
                int_type = arm.get("type", "")
                if name:
                    interventions.append(f"{name} ({int_type})" if int_type else name)

            # Parse locations
            locations = []
            for loc in contacts.get("locations", [])[:10]:  # Limit to 10 locations
                locations.append(TrialLocation(
                    facility=loc.get("facility", ""),
                    city=loc.get("city", ""),
                    state=loc.get("state", ""),
                    country=loc.get("country", ""),
                    status=loc.get("status", "")
                ))

            # Parse eligibility criteria
            eligibility_text = eligibility.get("eligibilityCriteria", "")
            eligibility_criteria = self._parse_eligibility_criteria(eligibility_text)

            # Get enrollment
            enrollment_info = design.get("enrollmentInfo", {})
            enrollment = enrollment_info.get("count")

            # Get dates
            start_date = status_module.get("startDateStruct", {}).get("date")
            completion_date = status_module.get("completionDateStruct", {}).get("date")
            last_update = status_module.get("lastUpdatePostDateStruct", {}).get("date")

            # Get sponsor
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            sponsor = lead_sponsor.get("name", "")

            return ClinicalTrialResult(
                nct_id=nct_id,
                title=identification.get("officialTitle", identification.get("briefTitle", "")),
                brief_summary=description.get("briefSummary", ""),
                phase=phase,
                status=status_module.get("overallStatus", ""),
                conditions=conditions_module.get("conditions", []),
                interventions=interventions,
                sponsor=sponsor,
                locations=locations,
                eligibility_criteria_text=eligibility_text,
                eligibility_criteria=eligibility_criteria,
                enrollment=enrollment,
                start_date=start_date,
                completion_date=completion_date,
                last_update=last_update,
                url=f"https://clinicaltrials.gov/study/{nct_id}"
            )

        except Exception as e:
            logger.error(f"Error parsing study: {e}")
            return None

    def _parse_eligibility_criteria(self, criteria_text: str) -> List[EligibilityCriterion]:
        """Parse eligibility criteria text into structured format.

        Args:
            criteria_text: Raw eligibility criteria text

        Returns:
            List of parsed criteria
        """
        criteria = []
        if not criteria_text:
            return criteria

        current_type = "inclusion"
        lines = criteria_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            lower_line = line.lower()
            if "inclusion" in lower_line and "criteria" in lower_line:
                current_type = "inclusion"
                continue
            elif "exclusion" in lower_line and "criteria" in lower_line:
                current_type = "exclusion"
                continue

            # Skip headers and short lines
            if len(line) < 10 or line.endswith(":"):
                continue

            # Remove bullet points and numbering
            clean_line = line.lstrip("•-*0123456789.) ")
            if clean_line and len(clean_line) > 10:
                criteria.append(EligibilityCriterion(
                    type=current_type,
                    description=clean_line
                ))

        return criteria[:50]  # Limit to 50 criteria

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
_service: Optional[ClinicalTrialsService] = None


def get_clinicaltrials_service() -> ClinicalTrialsService:
    """Get or create the ClinicalTrials service instance."""
    global _service
    if _service is None:
        _service = ClinicalTrialsService()
    return _service
