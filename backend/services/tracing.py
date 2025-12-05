"""OpenAI Tracing Service - Custom instrumentation for LLM calls and agent workflows."""

import os
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from functools import wraps
import json

from config import settings

logger = logging.getLogger(__name__)

# LangSmith integration
_langsmith_enabled = False
_langsmith_trace = None
_langsmith_traceable = None

def _setup_langsmith():
    """Setup LangSmith tracing if enabled."""
    global _langsmith_enabled, _langsmith_trace, _langsmith_traceable

    if settings.LANGSMITH_TRACING_ENABLED and settings.LANGSMITH_API_KEY:
        # Set environment variables for LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

        try:
            from langsmith import trace as ls_trace, traceable
            _langsmith_trace = ls_trace
            _langsmith_traceable = traceable
            _langsmith_enabled = True
            logger.info(f"LangSmith tracing enabled for project: {settings.LANGSMITH_PROJECT}")
        except ImportError:
            logger.warning("langsmith package not installed, tracing disabled")

    return _langsmith_enabled

# Initialize on module load
_setup_langsmith()


@dataclass
class LLMSpan:
    """Represents a single LLM call span."""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    operation: str  # "chat.completion", "embedding", etc.
    model: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Request data
    prompt_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

    # Response data
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    response_length: Optional[int] = None

    # Status
    status: str = "started"  # started, completed, error
    error_message: Optional[str] = None

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, response_text: str = None, usage: Dict = None):
        """Mark the span as completed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "completed"

        if response_text:
            self.response_length = len(response_text)

        if usage:
            self.prompt_tokens = usage.get("prompt_tokens")
            self.completion_tokens = usage.get("completion_tokens")
            self.total_tokens = usage.get("total_tokens")

    def fail(self, error: str):
        """Mark the span as failed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "error"
        self.error_message = error

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage."""
        data = asdict(self)
        # Convert datetime to ISO format
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


@dataclass
class AgentSpan:
    """Represents an agent execution span."""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Agent-specific data
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    steps_count: int = 0

    # Child spans
    llm_spans: List[str] = field(default_factory=list)

    # Status
    status: str = "started"
    error_message: Optional[str] = None

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, output_summary: str = None):
        """Mark the agent span as completed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "completed"
        if output_summary:
            self.output_summary = output_summary

    def fail(self, error: str):
        """Mark the agent span as failed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "error"
        self.error_message = error

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage."""
        data = asdict(self)
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


@dataclass
class Trace:
    """A complete trace of an operation."""
    trace_id: str
    operation: str  # "analysis", "chat", etc.
    patient_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    # Spans
    agent_spans: List[AgentSpan] = field(default_factory=list)
    llm_spans: List[LLMSpan] = field(default_factory=list)

    # Summary stats
    total_tokens: int = 0
    total_llm_calls: int = 0
    total_agents: int = 0

    # Status
    status: str = "started"
    error_message: Optional[str] = None

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self):
        """Mark the trace as completed and compute summary stats."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "completed"

        # Compute summary stats
        self.total_llm_calls = len(self.llm_spans)
        self.total_agents = len(self.agent_spans)
        self.total_tokens = sum(
            span.total_tokens or 0 for span in self.llm_spans
        )

    def fail(self, error: str):
        """Mark the trace as failed."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "error"
        self.error_message = error

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage."""
        return {
            "trace_id": self.trace_id,
            "operation": self.operation,
            "patient_id": self.patient_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_message": self.error_message,
            "total_tokens": self.total_tokens,
            "total_llm_calls": self.total_llm_calls,
            "total_agents": self.total_agents,
            "metadata": self.metadata,
            "agent_spans": [s.to_dict() for s in self.agent_spans],
            "llm_spans": [s.to_dict() for s in self.llm_spans],
        }


class TracingService:
    """Service for tracing LLM calls and agent workflows."""

    def __init__(self):
        self._current_trace: Optional[Trace] = None
        self._current_agent_span: Optional[AgentSpan] = None
        self._traces: Dict[str, Trace] = {}  # In-memory storage
        self._langsmith_context = None  # Current LangSmith trace context
        self._langsmith_agent_contexts: List[Any] = []  # Stack of agent contexts

    def generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return f"trace_{uuid.uuid4().hex[:16]}"

    def generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return f"span_{uuid.uuid4().hex[:12]}"

    @asynccontextmanager
    async def trace(
        self,
        operation: str,
        patient_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Context manager for creating a trace.

        Usage:
            async with tracing.trace("analysis", patient_id="p123") as trace:
                # Your code here
                pass

        When LangSmith is enabled, this also creates a parent trace in LangSmith
        that groups all nested LLM calls together.
        """
        trace_id = self.generate_trace_id()
        trace_obj = Trace(
            trace_id=trace_id,
            operation=operation,
            patient_id=patient_id,
            start_time=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self._current_trace = trace_obj
        self._traces[trace_id] = trace_obj
        self._langsmith_context = None

        logger.info(f"[TRACE START] {trace_id} - {operation}" + (f" (patient: {patient_id})" if patient_id else ""))

        # Build LangSmith metadata
        ls_metadata = {
            "trace_id": trace_id,
            "operation": operation,
            **({"patient_id": patient_id} if patient_id else {}),
            **(metadata or {})
        }

        # Enter LangSmith trace context if enabled
        if _langsmith_enabled and _langsmith_trace:
            self._langsmith_context = _langsmith_trace(
                name=f"{operation}",
                run_type="chain",
                metadata=ls_metadata,
                project_name=settings.LANGSMITH_PROJECT
            )
            self._langsmith_context.__enter__()
            logger.debug(f"[LANGSMITH] Started trace: {operation}")

        try:
            yield trace_obj
            trace_obj.complete()
            logger.info(
                f"[TRACE END] {trace_id} - {operation} "
                f"(duration: {trace_obj.duration_ms:.0f}ms, "
                f"llm_calls: {trace_obj.total_llm_calls}, "
                f"tokens: {trace_obj.total_tokens})"
            )
        except Exception as e:
            trace_obj.fail(str(e))
            logger.error(f"[TRACE ERROR] {trace_id} - {operation}: {e}")
            raise
        finally:
            # Exit LangSmith context
            if self._langsmith_context:
                self._langsmith_context.__exit__(None, None, None)
                logger.debug(f"[LANGSMITH] Ended trace: {operation}")
            self._current_trace = None
            self._langsmith_context = None
            self._log_trace(trace_obj)

    @asynccontextmanager
    async def agent_span(
        self,
        agent_name: str,
        input_summary: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Context manager for creating an agent span.

        Usage:
            async with tracing.agent_span("MedicalHistoryAgent") as span:
                # Agent code here
                pass

        When LangSmith is enabled, this creates a nested span under the parent trace.
        """
        span_id = self.generate_span_id()
        trace_id = self._current_trace.trace_id if self._current_trace else self.generate_trace_id()
        parent_id = self._current_agent_span.span_id if self._current_agent_span else None

        span = AgentSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            agent_name=agent_name,
            start_time=datetime.now(timezone.utc),
            input_summary=input_summary[:200] if input_summary else None,
            metadata=metadata or {}
        )

        previous_span = self._current_agent_span
        self._current_agent_span = span

        if self._current_trace:
            self._current_trace.agent_spans.append(span)

        logger.debug(f"[AGENT START] {span_id} - {agent_name}")

        # Create nested LangSmith span if enabled
        ls_agent_context = None
        if _langsmith_enabled and _langsmith_trace:
            ls_metadata = {
                "span_id": span_id,
                "agent_name": agent_name,
                **({"input_summary": input_summary[:100]} if input_summary else {}),
                **(metadata or {})
            }
            ls_agent_context = _langsmith_trace(
                name=agent_name,
                run_type="chain",
                metadata=ls_metadata
            )
            ls_agent_context.__enter__()
            self._langsmith_agent_contexts.append(ls_agent_context)

        try:
            yield span
            span.complete()
            logger.debug(
                f"[AGENT END] {span_id} - {agent_name} "
                f"(duration: {span.duration_ms:.0f}ms)"
            )
        except Exception as e:
            span.fail(str(e))
            logger.error(f"[AGENT ERROR] {span_id} - {agent_name}: {e}")
            raise
        finally:
            # Exit LangSmith agent context
            if ls_agent_context:
                ls_agent_context.__exit__(None, None, None)
                if self._langsmith_agent_contexts:
                    self._langsmith_agent_contexts.pop()
            self._current_agent_span = previous_span

    def start_llm_span(
        self,
        operation: str = "chat.completion",
        model: str = "unknown",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> LLMSpan:
        """Start an LLM span manually (for non-context-manager usage).

        Returns the span so you can call complete() or fail() on it.
        """
        span_id = self.generate_span_id()
        trace_id = self._current_trace.trace_id if self._current_trace else self.generate_trace_id()
        parent_id = self._current_agent_span.span_id if self._current_agent_span else None

        span = LLMSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            operation=operation,
            model=model,
            start_time=datetime.now(timezone.utc),
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=metadata or {}
        )

        if self._current_trace:
            self._current_trace.llm_spans.append(span)

        if self._current_agent_span:
            self._current_agent_span.llm_spans.append(span_id)

        logger.debug(f"[LLM START] {span_id} - {model}")

        return span

    def complete_llm_span(
        self,
        span: LLMSpan,
        response_text: str = None,
        usage: Dict = None
    ):
        """Complete an LLM span with response data."""
        span.complete(response_text, usage)
        logger.debug(
            f"[LLM END] {span.span_id} - {span.model} "
            f"(duration: {span.duration_ms:.0f}ms, "
            f"tokens: {span.total_tokens or 'N/A'})"
        )

    def fail_llm_span(self, span: LLMSpan, error: str):
        """Mark an LLM span as failed."""
        span.fail(error)
        logger.warning(f"[LLM ERROR] {span.span_id} - {span.model}: {error}")

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)

    def get_current_trace(self) -> Optional[Trace]:
        """Get the current active trace."""
        return self._current_trace

    def get_recent_traces(self, limit: int = 10) -> List[Dict]:
        """Get recent traces for debugging."""
        traces = sorted(
            self._traces.values(),
            key=lambda t: t.start_time,
            reverse=True
        )[:limit]
        return [t.to_dict() for t in traces]

    def _log_trace(self, trace: Trace):
        """Log the complete trace for debugging/analysis."""
        trace_data = trace.to_dict()
        # Log as structured data
        logger.info(f"[TRACE COMPLETE] {json.dumps(trace_data, default=str)}")


# Global tracing service instance
tracing_service = TracingService()


# Convenience functions
def get_tracer() -> TracingService:
    """Get the global tracing service instance."""
    return tracing_service


def trace(operation: str, patient_id: Optional[str] = None, metadata: Optional[Dict] = None):
    """Convenience function for creating a trace context."""
    return tracing_service.trace(operation, patient_id, metadata)


def agent_span(agent_name: str, input_summary: Optional[str] = None, metadata: Optional[Dict] = None):
    """Convenience function for creating an agent span context."""
    return tracing_service.agent_span(agent_name, input_summary, metadata)
