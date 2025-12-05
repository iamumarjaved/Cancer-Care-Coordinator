"""Medical History Agent for analyzing patient medical records."""

from typing import List, Optional
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from models.patient import Patient, PatientSummary, CancerDetails, ECOGStatus, Comorbidity, OrganFunction
from services.llm_service import LLMService


class ClinicalNoteInfo(BaseModel):
    """Clinical note information for analysis."""
    note_text: str
    note_type: str
    created_at: str


class MedicalHistoryInput(BaseModel):
    """Input for medical history analysis."""
    patient: Patient
    clinical_notes: List[ClinicalNoteInfo] = Field(default_factory=list)


class MedicalHistoryOutput(BaseModel):
    """Output from medical history analysis."""
    patient_summary: PatientSummary
    key_findings: List[str] = Field(default_factory=list)
    treatment_considerations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)


class MedicalHistoryAgent(BaseAgent[MedicalHistoryInput, MedicalHistoryOutput]):
    """Agent that analyzes and summarizes patient medical history.

    This agent extracts and synthesizes:
    - Demographics and relevant history
    - Cancer details and staging
    - Comorbidities and their treatment implications
    - Organ function status
    - Current medications and allergies
    - Key findings relevant to treatment decisions
    """

    def __init__(self, llm_service: LLMService, use_mock: bool = True):
        super().__init__(
            name="medical_history",
            llm_service=llm_service,
            use_mock=use_mock
        )

    def get_system_prompt(self) -> str:
        return """You are a medical oncology AI assistant specialized in analyzing patient medical histories.
Your role is to:
1. Extract and summarize relevant medical information
2. Identify key findings that impact treatment decisions
3. Flag comorbidities that may affect therapy choices
4. Assess organ function and its implications
5. Identify any missing critical information

Always be thorough and accurate. Focus on information relevant to oncology treatment planning.
Do not make treatment recommendations - only summarize and analyze the medical history."""

    async def execute(self, input_data: MedicalHistoryInput) -> MedicalHistoryOutput:
        """Execute medical history analysis using LLM."""
        patient = input_data.patient
        clinical_notes = input_data.clinical_notes

        # Build prompt with patient data and clinical notes
        prompt = self._build_analysis_prompt(patient, clinical_notes)

        # Call LLM for analysis
        response = await self._call_llm(
            prompt=prompt,
            output_model=MedicalHistoryOutput,
            temperature=0.2
        )

        return response

    def _mock_execute(self, input_data: MedicalHistoryInput) -> MedicalHistoryOutput:
        """Generate mock medical history analysis."""
        patient = input_data.patient

        # Build patient summary from available data
        demographics = {
            "age": patient.age,
            "sex": patient.sex,
            "smoking_status": patient.smoking_status or "Unknown",
            "pack_years": patient.pack_years
        }

        patient_summary = PatientSummary(
            demographics=demographics,
            cancer=patient.cancer_details or CancerDetails(
                cancer_type="Other",
                stage="Stage I",
                primary_site="Unknown"
            ),
            comorbidities=patient.comorbidities,
            organ_function=patient.organ_function,
            ecog_status=patient.ecog_status or ECOGStatus.FULLY_ACTIVE,
            current_medications=patient.current_medications,
            allergies=patient.allergies,
            prior_treatments=[],
            treatment_implications=self._derive_treatment_implications(patient)
        )

        # Generate key findings based on patient data
        key_findings = self._generate_key_findings(patient)

        # Generate treatment considerations
        treatment_considerations = self._generate_treatment_considerations(patient)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(patient)

        # Check for missing information
        missing_info = self._check_missing_information(patient)

        return MedicalHistoryOutput(
            patient_summary=patient_summary,
            key_findings=key_findings,
            treatment_considerations=treatment_considerations,
            risk_factors=risk_factors,
            missing_information=missing_info
        )

    def _build_analysis_prompt(self, patient: Patient, clinical_notes: List[ClinicalNoteInfo] = None) -> str:
        """Build the analysis prompt from patient data and clinical notes."""
        clinical_notes = clinical_notes or []

        # Build clinical notes section
        notes_section = ""
        if clinical_notes:
            notes_section = "\n\nRecent Clinical Notes/Updates:\n"
            for note in clinical_notes:
                notes_section += f"- [{note.note_type}] ({note.created_at}): {note.note_text}\n"

        return f"""Analyze the following patient medical history and provide a comprehensive summary:

Patient ID: {patient.id}
Name: {patient.full_name}
Age: {patient.age}
Sex: {patient.sex}

Cancer Details:
{patient.cancer_details.model_dump_json(indent=2) if patient.cancer_details else 'Not available'}

Comorbidities:
{[c.model_dump() for c in patient.comorbidities] if patient.comorbidities else 'None documented'}

Organ Function:
{[o.model_dump() for o in patient.organ_function] if patient.organ_function else 'Not assessed'}

ECOG Status: {patient.ecog_status.value if patient.ecog_status else 'Not assessed'}

Current Medications: {', '.join(patient.current_medications) if patient.current_medications else 'None'}

Allergies: {', '.join(patient.allergies) if patient.allergies else 'None'}

Smoking History: {patient.smoking_status or 'Unknown'}, Pack Years: {patient.pack_years or 'Unknown'}{notes_section}

Please provide:
1. A comprehensive patient summary
2. Key findings relevant to treatment decisions
3. Treatment considerations based on comorbidities and organ function
4. Risk factors to monitor
5. Any critical missing information that should be obtained

IMPORTANT: If there are clinical notes above, incorporate them into your analysis as they contain recent observations, test results, and treatment updates from the medical team."""

    def _derive_treatment_implications(self, patient: Patient) -> List[str]:
        """Derive treatment implications from patient data."""
        implications = []

        # Check organ function
        for organ in patient.organ_function:
            if organ.status in ["moderate_impairment", "severe_impairment"]:
                implications.append(f"{organ.organ} impairment may require dose adjustments")

        # Check comorbidities
        for comorb in patient.comorbidities:
            implications.extend(comorb.treatment_implications)

        # Check ECOG status
        if patient.ecog_status and patient.ecog_status.value >= 2:
            implications.append("Reduced performance status may limit aggressive treatment options")

        # Check allergies for common cancer drugs
        drug_allergies = [a for a in patient.allergies if any(
            drug in a.lower() for drug in ["platinum", "taxol", "taxane", "penicillin"]
        )]
        if drug_allergies:
            implications.append(f"Drug allergies noted: {', '.join(drug_allergies)}")

        return implications

    def _generate_key_findings(self, patient: Patient) -> List[str]:
        """Generate key findings from patient data."""
        findings = []

        if patient.cancer_details:
            cancer = patient.cancer_details
            findings.append(f"{cancer.cancer_type.value}, {cancer.stage.value}")
            if cancer.subtype:
                findings.append(f"Histology: {cancer.subtype}")
            if cancer.metastases:
                findings.append(f"Metastatic sites: {', '.join(cancer.metastases)}")

        if patient.ecog_status:
            findings.append(f"ECOG Performance Status: {patient.ecog_status.value}")

        if patient.smoking_status == "current" or (patient.pack_years and patient.pack_years >= 30):
            findings.append(f"Significant smoking history: {patient.pack_years} pack-years")

        if patient.genomic_report_id:
            findings.append("Genomic testing completed - review for actionable mutations")

        return findings

    def _generate_treatment_considerations(self, patient: Patient) -> List[str]:
        """Generate treatment considerations."""
        considerations = []

        # Check for renal impairment
        renal = next((o for o in patient.organ_function if o.organ.lower() == "kidney"), None)
        if renal and renal.status in ["moderate_impairment", "severe_impairment"]:
            considerations.append("Renal dosing adjustments required for renally-cleared agents")

        # Check for hepatic impairment
        hepatic = next((o for o in patient.organ_function if o.organ.lower() == "liver"), None)
        if hepatic and hepatic.status in ["moderate_impairment", "severe_impairment"]:
            considerations.append("Hepatic dosing adjustments may be required")

        # Check for cardiac history
        cardiac_comorb = [c for c in patient.comorbidities if any(
            term in c.condition.lower() for term in ["heart", "cardiac", "arrhythmia", "chf"]
        )]
        if cardiac_comorb:
            considerations.append("Cardiac monitoring recommended; avoid cardiotoxic agents if possible")

        # Check for diabetes
        diabetes = next((c for c in patient.comorbidities if "diabetes" in c.condition.lower()), None)
        if diabetes:
            considerations.append("Monitor blood glucose during steroid-containing regimens")

        # ECOG considerations
        if patient.ecog_status and patient.ecog_status.value >= 2:
            considerations.append("Consider less intensive regimens due to performance status")

        return considerations

    def _identify_risk_factors(self, patient: Patient) -> List[str]:
        """Identify risk factors."""
        risk_factors = []

        if patient.smoking_status and patient.smoking_status.lower() in ["current", "former"] and patient.pack_years:
            risk_factors.append(f"Tobacco exposure ({patient.pack_years} pack-years)")

        if patient.age >= 70:
            risk_factors.append("Advanced age (>=70) - increased treatment toxicity risk")

        # Check for immunosuppression
        immunosuppressive_meds = [m for m in patient.current_medications if any(
            drug in m.lower() for drug in ["prednisone", "methotrexate", "azathioprine", "cyclosporine"]
        )]
        if immunosuppressive_meds:
            risk_factors.append("Immunosuppressive medications")

        severe_comorb = [c for c in patient.comorbidities if c.severity == "severe"]
        if severe_comorb:
            risk_factors.append(f"Severe comorbidities: {', '.join(c.condition for c in severe_comorb)}")

        return risk_factors

    def _check_missing_information(self, patient: Patient) -> List[str]:
        """Check for missing critical information."""
        missing = []

        if not patient.cancer_details:
            missing.append("Cancer diagnosis details")
        if patient.ecog_status is None:
            missing.append("ECOG Performance Status assessment")
        if not patient.organ_function:
            missing.append("Organ function assessments (renal, hepatic)")
        if patient.smoking_status is None:
            missing.append("Smoking history")
        if not patient.genomic_report_id and patient.cancer_details:
            missing.append("Genomic testing - recommended for treatment selection")

        return missing
