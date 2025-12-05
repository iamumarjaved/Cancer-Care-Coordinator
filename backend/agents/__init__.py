"""AI Agents for Cancer Care Coordinator.

This module contains the AI agents that power the analysis pipeline:
- BaseAgent: Abstract base class for all agents
- MedicalHistoryAgent: Extracts and summarizes patient medical history
- GenomicsAgent: Interprets genomic/mutation data
- ClinicalTrialsAgent: Matches patients to clinical trials
- EvidenceAgent: Searches medical literature and guidelines
- TreatmentAgent: Generates treatment recommendations
- PatientCommunicationAgent: Handles patient chat interactions
- OrchestratorAgent: Coordinates the analysis workflow
"""

from .base_agent import BaseAgent
from .medical_history_agent import MedicalHistoryAgent
from .genomics_agent import GenomicsAgent
from .clinical_trials_agent import ClinicalTrialsAgent
from .evidence_agent import EvidenceAgent
from .treatment_agent import TreatmentAgent
from .patient_communication_agent import PatientCommunicationAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    "BaseAgent",
    "MedicalHistoryAgent",
    "GenomicsAgent",
    "ClinicalTrialsAgent",
    "EvidenceAgent",
    "TreatmentAgent",
    "PatientCommunicationAgent",
    "OrchestratorAgent",
]
