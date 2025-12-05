"""Message models for agent communication."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    MEDICAL_HISTORY = "medical_history"
    GENOMICS = "genomics"
    CLINICAL_TRIALS = "clinical_trials"
    EVIDENCE = "evidence"
    TREATMENT = "treatment"
    PATIENT_COMMUNICATION = "patient_communication"


class MessageType(str, Enum):
    """Types of inter-agent messages."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class AgentStatus(str, Enum):
    """Agent processing status."""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"


class AgentMessage(BaseModel):
    """Message passed between agents."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: AgentType
    recipient: AgentType
    message_type: MessageType
    task: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""
    agent: AgentType
    status: AgentStatus
    task: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None
    reasoning_trace: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Request to analyze a patient."""
    patient_id: str
    analysis_type: str = "full"  # "full", "genomics_only", "treatment_only"
    include_trials: bool = True
    user_questions: List[str] = Field(default_factory=list)


class AnalysisProgress(BaseModel):
    """Progress update during analysis."""
    request_id: str
    patient_id: str
    status: str  # "in_progress", "completed", "error"
    current_step: str
    current_step_detail: str = ""  # Human-readable description of current step
    steps_completed: List[str] = Field(default_factory=list)
    steps_remaining: List[str] = Field(default_factory=list)
    agent_statuses: Dict[str, AgentStatus] = Field(default_factory=dict)
    partial_results: Dict[str, Any] = Field(default_factory=dict)
    progress_percent: int = 0
    error_message: Optional[str] = None  # Error message if status is "error"


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    request_id: str
    patient_id: str
    status: str
    completed_at: datetime

    # Results from each agent
    patient_summary: Optional[Dict[str, Any]] = None
    genomic_analysis: Optional[Dict[str, Any]] = None
    clinical_trials: Optional[List[Dict[str, Any]]] = None
    evidence_summary: Optional[Dict[str, Any]] = None
    treatment_plan: Optional[Dict[str, Any]] = None

    # Final synthesized output
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    discussion_points: List[str] = Field(default_factory=list)
    sources_used: List[str] = Field(default_factory=list)

    # Agent trace (for debugging)
    agent_trace: List[AgentResponse] = Field(default_factory=list)


class ChatMessage(BaseModel):
    """Chat message between patient and AI."""
    id: str
    patient_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    role: str  # "patient" or "assistant"
    content: str
    context_used: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request for patient chat."""
    patient_id: str
    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from patient communication agent."""
    patient_id: str
    response: str
    sources_used: List[str] = Field(default_factory=list)
    escalate_to_human: bool = False
    escalation_reason: Optional[str] = None
    suggested_followup: List[str] = Field(default_factory=list)
