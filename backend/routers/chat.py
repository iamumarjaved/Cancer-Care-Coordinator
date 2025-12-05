"""Chat API Router - Patient Communication Interface."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
import asyncio
import uuid
import logging
import json

from models.messages import ChatMessage, ChatRequest, ChatResponse
from services.llm_service import LLMService
from services.patient_service import PatientService
from services.vector_store_service import VectorStoreService
from database import async_session_maker
from models.db_models import AnalysisResultDB, ChatMessageDB, TreatmentCycleDB, PatientDB, TreatmentProcedureDB, ClinicalNoteDB
from sqlalchemy import select, desc, and_
from datetime import timedelta

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()
patient_service = PatientService()
vector_store_service = VectorStoreService()

# Safety keywords that trigger escalation
ESCALATION_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "severe pain", "can't breathe", "chest pain", "emergency"
]

# Topics the AI should not directly answer
RESTRICTED_TOPICS = [
    "prognosis", "how long", "survival", "life expectancy",
    "stop treatment", "refuse treatment", "discontinue"
]


def _should_escalate(message: str) -> tuple[bool, Optional[str]]:
    """Check if message requires human escalation.

    Args:
        message: User message text

    Returns:
        Tuple of (should_escalate, reason)
    """
    message_lower = message.lower()

    for keyword in ESCALATION_KEYWORDS:
        if keyword in message_lower:
            return True, f"Message contains concerning content: '{keyword}'"

    return False, None


def _get_mock_response(message: str, patient_id: str) -> tuple[str, List[str]]:
    """Generate mock AI response.

    Args:
        message: User message
        patient_id: Patient ID for context

    Returns:
        Tuple of (response_text, sources_used)
    """
    message_lower = message.lower()

    # Check for restricted topics
    for topic in RESTRICTED_TOPICS:
        if topic in message_lower:
            return (
                "I understand you have questions about this topic. These are very important "
                "questions that are best discussed directly with your oncology team, as they "
                "have the full picture of your specific situation and can provide the most "
                "accurate information. I'd encourage you to bring this up at your next appointment, "
                "or you can call the office if you'd like to discuss it sooner.",
                []
            )

    # Treatment-related questions
    if any(word in message_lower for word in ["treatment", "therapy", "medication", "drug"]):
        return (
            "Your treatment plan has been carefully designed based on your specific cancer type "
            "and the genetic characteristics of your tumor. The targeted therapy recommended for "
            "you works by blocking specific proteins that help cancer cells grow.\n\n"
            "Common side effects may include:\n"
            "- Skin changes (rash, dry skin)\n"
            "- Digestive issues (diarrhea, nausea)\n"
            "- Fatigue\n\n"
            "Your care team will monitor you closely and can adjust your treatment if needed. "
            "Please report any side effects you experience.\n\n"
            "Is there a specific aspect of your treatment you'd like me to explain further?",
            ["Treatment Plan", "NCCN Guidelines"]
        )

    # Side effects questions
    if any(word in message_lower for word in ["side effect", "symptom", "feel", "pain"]):
        return (
            "I'm sorry to hear you're experiencing symptoms. Here are some general tips that "
            "may help:\n\n"
            "**For nausea:**\n"
            "- Eat small, frequent meals\n"
            "- Avoid strong smells\n"
            "- Try ginger tea or crackers\n\n"
            "**For fatigue:**\n"
            "- Rest when needed\n"
            "- Light exercise if approved by your doctor\n"
            "- Stay hydrated\n\n"
            "**For skin changes:**\n"
            "- Use gentle, fragrance-free moisturizers\n"
            "- Protect from sun exposure\n"
            "- Avoid hot water\n\n"
            "If your symptoms are severe or getting worse, please contact your care team "
            "right away. They may be able to prescribe medications to help.\n\n"
            "What specific symptoms are you experiencing?",
            ["Supportive Care Guidelines"]
        )

    # Clinical trial questions
    if any(word in message_lower for word in ["trial", "study", "research"]):
        return (
            "Clinical trials can be an excellent option and are often how we discover better "
            "treatments. Based on your profile, there are several trials you may be eligible for.\n\n"
            "**What to know about clinical trials:**\n"
            "- You receive close monitoring and care\n"
            "- You may have access to newer treatments\n"
            "- Your participation helps others\n"
            "- You can withdraw at any time\n\n"
            "The trials matched to your case target the specific genetic mutation in your cancer. "
            "Your oncologist can discuss which trials might be right for you and explain the "
            "requirements for participation.\n\n"
            "Would you like me to explain more about any specific trial?",
            ["ClinicalTrials.gov", "Patient Profile"]
        )

    # Genetic/genomic questions
    if any(word in message_lower for word in ["genetic", "genomic", "mutation", "egfr"]):
        return (
            "The genetic testing of your tumor found important information that guides your "
            "treatment. Specifically, an EGFR mutation was detected.\n\n"
            "**What this means:**\n"
            "- EGFR is a protein that can cause cancer cells to grow\n"
            "- Your cancer has a change (mutation) in the EGFR gene\n"
            "- This makes your cancer sensitive to targeted drugs\n"
            "- These drugs specifically block EGFR, stopping cancer growth\n\n"
            "This is actually good news because it means there are FDA-approved medications "
            "that specifically target this mutation with good response rates.\n\n"
            "Do you have questions about how this affects your treatment options?",
            ["Genomic Report", "OncoKB"]
        )

    # Default supportive response
    return (
        "Thank you for reaching out. I'm here to help you understand your care and answer "
        "questions about your treatment journey.\n\n"
        "I can help explain:\n"
        "- Your treatment plan and medications\n"
        "- Managing side effects\n"
        "- Clinical trial options\n"
        "- Your genetic test results\n"
        "- What to expect during treatment\n\n"
        "What would you like to know more about?",
        []
    )


# Chat System Prompt
CHAT_SYSTEM_PROMPT = """You are a compassionate and knowledgeable oncology care coordinator assistant. You are helping a cancer patient understand their condition and treatment.

You have access to the patient's medical information, analysis results, treatment history, and relevant medical knowledge provided below. Use this information to provide personalized, accurate responses.

IMPORTANT GUIDELINES:
1. Be empathetic and supportive in your responses
2. Use the patient's actual medical data to provide specific, relevant information
3. Reference their specific mutations, treatments, and clinical trial options when relevant
4. Always recommend consulting with the oncology team for medical decisions
5. If asked about prognosis, survival, or life expectancy, gently redirect to discuss with their doctor
6. For any emergency symptoms (severe pain, difficulty breathing, chest pain), advise immediate medical attention
7. Explain medical terms in simple language
8. Reference specific findings from their analysis when relevant
9. Suggest appropriate follow-up questions to help them understand their care
10. If the patient has ongoing treatments, acknowledge their treatment journey

Keep responses concise but helpful (2-4 paragraphs typically).

PATIENT CONTEXT:
{patient_context}

RECENT ANALYSIS RESULTS & TREATMENT HISTORY:
{analysis_context}

RELEVANT MEDICAL KNOWLEDGE:
{rag_context}

CONVERSATION HISTORY:
{chat_history}
"""


async def _get_chat_history_from_db(patient_id: str, limit: int = 20) -> List[ChatMessage]:
    """Get chat history from database.

    Args:
        patient_id: The patient ID
        limit: Maximum messages to return

    Returns:
        List of chat messages
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(ChatMessageDB)
                .where(ChatMessageDB.patient_id == patient_id)
                .order_by(desc(ChatMessageDB.created_at))
                .limit(limit)
            )
            db_messages = result.scalars().all()

            # Convert to ChatMessage and reverse to get chronological order
            messages = []
            for msg in reversed(db_messages):
                messages.append(ChatMessage(
                    id=str(msg.id),
                    patient_id=msg.patient_id,
                    timestamp=msg.created_at,
                    role=msg.role,
                    content=msg.content,
                    context_used=msg.context
                ))
            return messages
    except Exception as e:
        logger.error(f"Failed to get chat history from DB: {e}")
        return []


async def _save_message_to_db(patient_id: str, role: str, content: str, context: dict = None):
    """Save a chat message to database.

    Args:
        patient_id: The patient ID
        role: Message role (patient or assistant)
        content: Message content
        context: Optional context data
    """
    try:
        async with async_session_maker() as db:
            message = ChatMessageDB(
                patient_id=patient_id,
                role=role,
                content=content,
                context=context,
                created_at=datetime.now()
            )
            db.add(message)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to save message to DB: {e}")


async def _build_patient_context(patient_id: str, user_message: str = "") -> tuple[str, str, str]:
    """Build comprehensive patient context for chat including RAG retrieval.

    Args:
        patient_id: The patient ID
        user_message: The user's question (for RAG query)

    Returns:
        Tuple of (patient_context, analysis_context, rag_context)
    """
    patient_context = "Patient information not available."
    analysis_context = "No recent analysis available."
    rag_context = ""

    # Get patient data
    patient = await patient_service.get_by_id(patient_id)
    if patient:
        # Calculate age
        today = date.today()
        dob = patient.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        lines = [
            f"Name: {patient.first_name} {patient.last_name}",
            f"Age: {age} years old",
            f"Sex: {patient.sex}",
        ]

        if patient.cancer_details:
            cd = patient.cancer_details
            lines.extend([
                f"Cancer Type: {cd.cancer_type.value}",
                f"Subtype: {cd.subtype or 'Not specified'}",
                f"Stage: {cd.stage.value}",
                f"ECOG Status: {patient.ecog_status.value if patient.ecog_status else 'Not recorded'}",
            ])
            if cd.metastases:
                lines.append(f"Metastatic Sites: {', '.join(cd.metastases)}")

        if patient.comorbidities:
            comorbid_list = [c.condition for c in patient.comorbidities[:3]]
            lines.append(f"Key Comorbidities: {', '.join(comorbid_list)}")

        if patient.current_medications:
            med_list = patient.current_medications[:5]
            lines.append(f"Current Medications: {', '.join(med_list)}")

        patient_context = "\n".join(lines)

    # Get latest analysis and treatment history from database
    try:
        async with async_session_maker() as db:
            # Get latest analysis
            result = await db.execute(
                select(AnalysisResultDB)
                .where(AnalysisResultDB.patient_id == patient_id)
                .where(AnalysisResultDB.status == "completed")
                .order_by(desc(AnalysisResultDB.completed_at))
                .limit(1)
            )
            analysis = result.scalar_one_or_none()

            if analysis and analysis.result_data:
                data = analysis.result_data
                lines = []
                if data.get("summary"):
                    lines.append(f"Summary: {data['summary']}")
                if data.get("key_findings"):
                    lines.append(f"Key Findings: {', '.join(data['key_findings'][:4])}")
                if data.get("recommendations"):
                    lines.append(f"Recommendations: {', '.join(data['recommendations'][:3])}")
                if data.get("treatment_plan", {}).get("treatment_options"):
                    treatments = [t.get("name", "") for t in data["treatment_plan"]["treatment_options"][:2]]
                    lines.append(f"Recommended Treatments: {', '.join(treatments)}")

                # Add genomic info if available
                genomic = data.get("genomic_report", {})
                if genomic.get("mutations"):
                    mutations = [f"{m.get('gene', '')} {m.get('variant', '')}" for m in genomic["mutations"][:3]]
                    lines.append(f"Key Mutations: {', '.join(mutations)}")

                if lines:
                    analysis_context = "\n".join(lines)

            # Get treatment history
            result = await db.execute(
                select(TreatmentCycleDB)
                .where(TreatmentCycleDB.patient_id == patient_id)
                .order_by(desc(TreatmentCycleDB.start_date))
                .limit(5)
            )
            treatments = result.scalars().all()

            if treatments:
                treatment_lines = ["\nTreatment History:"]
                for t in treatments:
                    status_str = f"({t.status})" if t.status else ""
                    response_str = f", Response: {t.response}" if t.response else ""
                    treatment_lines.append(f"- {t.treatment_name} Cycle {t.cycle_number} {status_str}{response_str}")
                analysis_context += "\n".join(treatment_lines)

            # Get ALL upcoming scheduled procedures (no time limit for real-time updates)
            now = datetime.now()
            upcoming_result = await db.execute(
                select(TreatmentProcedureDB)
                .where(
                    and_(
                        TreatmentProcedureDB.patient_id == patient_id,
                        TreatmentProcedureDB.status == "scheduled",
                        TreatmentProcedureDB.scheduled_date >= now
                    )
                )
                .order_by(TreatmentProcedureDB.scheduled_date)
                .limit(20)  # Increased limit to include more procedures
            )
            upcoming = upcoming_result.scalars().all()

            if upcoming:
                proc_lines = ["\n\nAll Scheduled Procedures:"]
                for p in upcoming:
                    date_str = p.scheduled_date.strftime("%b %d, %Y")
                    time_str = f" at {p.scheduled_time}" if p.scheduled_time else ""
                    loc_str = f" - {p.location}" if p.location else ""
                    proc_lines.append(f"- {date_str}{time_str}: {p.procedure_name} ({p.procedure_type}){loc_str}")
                analysis_context += "\n".join(proc_lines)

            # Get recent completed procedures (last 14 days)
            recent_result = await db.execute(
                select(TreatmentProcedureDB)
                .where(
                    and_(
                        TreatmentProcedureDB.patient_id == patient_id,
                        TreatmentProcedureDB.status == "completed",
                        TreatmentProcedureDB.actual_date >= now - timedelta(days=14)
                    )
                )
                .order_by(desc(TreatmentProcedureDB.actual_date))
                .limit(5)
            )
            recent = recent_result.scalars().all()

            if recent:
                recent_lines = ["\n\nRecent Completed Procedures (Last 14 Days):"]
                for p in recent:
                    date_str = p.actual_date.strftime("%b %d") if p.actual_date else "Unknown"
                    dose_str = f", Dose: {p.actual_dose}" if p.actual_dose else ""
                    ae_count = len(p.adverse_events) if p.adverse_events else 0
                    ae_str = f", {ae_count} adverse event(s)" if ae_count > 0 else ""
                    recent_lines.append(f"- {date_str}: {p.procedure_name}{dose_str}{ae_str}")
                analysis_context += "\n".join(recent_lines)

            # Get clinical notes
            notes_result = await db.execute(
                select(ClinicalNoteDB)
                .where(ClinicalNoteDB.patient_id == patient_id)
                .order_by(desc(ClinicalNoteDB.created_at))
                .limit(10)
            )
            clinical_notes = notes_result.scalars().all()

            if clinical_notes:
                notes_lines = ["\n\nRecent Clinical Notes:"]
                for note in clinical_notes:
                    date_str = note.created_at.strftime("%b %d") if note.created_at else "Unknown"
                    type_label = note.note_type.replace("_", " ").title() if note.note_type else "General"
                    notes_lines.append(f"- [{type_label}] ({date_str}): {note.note_text}")
                analysis_context += "\n".join(notes_lines)

            # Get patient status
            result = await db.execute(
                select(PatientDB.status, PatientDB.closure_reason)
                .where(PatientDB.id == patient_id)
            )
            status_row = result.first()
            if status_row and status_row[0] == "closed":
                patient_context += f"\n\nPatient Status: CLOSED - {status_row[1] or 'Unknown reason'}"

    except Exception as e:
        logger.error(f"Failed to fetch analysis for chat context: {e}")

    # RAG retrieval for relevant medical knowledge
    if user_message:
        try:
            rag_lines = []

            # Search patient context (evidence, genomics, trials)
            rag_results = await vector_store_service.search_patient_context(
                patient_id=patient_id,
                query=user_message,
                top_k=3
            )

            if rag_results:
                rag_lines.append("Relevant Medical Information:")
                for result in rag_results:
                    # Truncate content for context
                    content = result.content[:300] + "..." if len(result.content) > 300 else result.content
                    rag_lines.append(f"- {content}")

            # Search procedures if question is about appointments/schedule/procedures
            procedure_keywords = ["appointment", "schedule", "procedure", "infusion", "lab", "imaging",
                                  "when", "next", "upcoming", "today", "tomorrow", "dose", "adverse", "side effect"]
            if any(kw in user_message.lower() for kw in procedure_keywords):
                procedure_results = await vector_store_service.search_patient_procedures(
                    patient_id=patient_id,
                    query=user_message,
                    top_k=3
                )
                if procedure_results:
                    rag_lines.append("\nProcedure Information:")
                    for result in procedure_results:
                        content = result.content[:300] + "..." if len(result.content) > 300 else result.content
                        rag_lines.append(f"- {content}")

            if rag_lines:
                rag_context = "\n".join(rag_lines)
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")

    return patient_context, analysis_context, rag_context


async def _get_llm_response(message: str, patient_id: str, chat_history: List[ChatMessage]) -> tuple[str, List[str], List[str]]:
    """Generate real LLM response with patient context and RAG retrieval.

    Args:
        message: User message
        patient_id: Patient ID for context
        chat_history: Recent chat history

    Returns:
        Tuple of (response_text, sources_used, suggested_followups)
    """
    try:
        # Build context with RAG retrieval
        patient_context, analysis_context, rag_context = await _build_patient_context(patient_id, message)

        # Format recent chat history
        history_lines = []
        for msg in chat_history[-6:]:  # Last 6 messages
            role = "Patient" if msg.role == "patient" else "Assistant"
            history_lines.append(f"{role}: {msg.content[:200]}")
        chat_history_text = "\n".join(history_lines) if history_lines else "No previous messages."

        # Build the full system prompt
        full_system_prompt = CHAT_SYSTEM_PROMPT.format(
            patient_context=patient_context,
            analysis_context=analysis_context,
            rag_context=rag_context or "No additional medical knowledge retrieved.",
            chat_history=chat_history_text
        )

        # Call LLM
        response_text = await llm_service.complete(
            prompt=f"Patient question: {message}\n\nProvide a helpful, empathetic response based on the patient context:",
            system_prompt=full_system_prompt,
            temperature=0.7,
            max_tokens=800
        )

        # Determine sources based on content and RAG results
        sources = []
        if "treatment" in message.lower() or "medication" in message.lower():
            sources.append("Treatment Plan")
        if "trial" in message.lower():
            sources.append("ClinicalTrials.gov")
        if "genetic" in message.lower() or "mutation" in message.lower():
            sources.append("Genomic Report")
        if "side effect" in message.lower() or "symptom" in message.lower():
            sources.append("Supportive Care Guidelines")
        if rag_context:
            sources.append("Patient Analysis")
        if not sources:
            sources.append("Patient Record")

        # Generate follow-up suggestions based on context
        followups = [
            "What side effects should I watch for?",
            "Can you explain my treatment options?",
            "Are there clinical trials I might qualify for?"
        ]

        return response_text, sources, followups

    except Exception as e:
        logger.error(f"LLM chat failed: {e}")
        # Fallback to mock response
        response, sources = _get_mock_response(message, patient_id)
        return response, sources, []


class SendMessageRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    context: Optional[dict] = None


class ChatHistoryResponse(BaseModel):
    """Response containing chat history."""
    patient_id: str
    messages: List[ChatMessage]
    total_messages: int


@router.post("/chat/{patient_id}/message", response_model=ChatResponse)
async def send_message(patient_id: str, request: SendMessageRequest):
    """Send a chat message and receive AI response.

    Args:
        patient_id: The patient ID
        request: Message to send

    Returns:
        AI response with sources
    """
    # Get chat history from database
    chat_history = await _get_chat_history_from_db(patient_id, limit=20)

    # Check for escalation
    should_escalate, escalation_reason = _should_escalate(request.message)

    # Save user message to database
    await _save_message_to_db(patient_id, "patient", request.message)

    # Generate response using real LLM with patient context
    if should_escalate:
        # For escalation, use a supportive but redirecting response
        response_text = (
            "I understand you're going through a difficult time. Your feelings are valid, "
            "and it's important that you talk to someone who can help. Please reach out to "
            "your care team or call the clinic right away. If this is an emergency, "
            "please call 911 or go to your nearest emergency room. Your oncology team "
            "is here to support you through this."
        )
        sources = []
        suggested_followups = []
    else:
        # Use real LLM with patient context and RAG
        response_text, sources, suggested_followups = await _get_llm_response(
            request.message,
            patient_id,
            chat_history
        )

    # Create response
    response = ChatResponse(
        patient_id=patient_id,
        response=response_text,
        sources_used=sources,
        escalate_to_human=should_escalate,
        escalation_reason=escalation_reason,
        suggested_followup=suggested_followups
    )

    # Save AI response to database
    await _save_message_to_db(
        patient_id,
        "assistant",
        response_text,
        {"sources": sources, "escalate": should_escalate}
    )

    return response


@router.get("/chat/{patient_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    patient_id: str,
    limit: int = 50
):
    """Get chat history for a patient from database.

    Args:
        patient_id: The patient ID
        limit: Maximum messages to return

    Returns:
        Chat message history
    """
    messages = await _get_chat_history_from_db(patient_id, limit=limit)

    # Get total count from database
    total_count = 0
    try:
        async with async_session_maker() as db:
            from sqlalchemy import func
            result = await db.execute(
                select(func.count(ChatMessageDB.id))
                .where(ChatMessageDB.patient_id == patient_id)
            )
            total_count = result.scalar() or 0
    except Exception as e:
        logger.error(f"Failed to get message count: {e}")
        total_count = len(messages)

    return ChatHistoryResponse(
        patient_id=patient_id,
        messages=messages,
        total_messages=total_count
    )


@router.delete("/chat/{patient_id}/history")
async def clear_chat_history(patient_id: str):
    """Clear chat history for a patient from database.

    Args:
        patient_id: The patient ID

    Returns:
        Confirmation of deletion
    """
    try:
        async with async_session_maker() as db:
            from sqlalchemy import delete
            result = await db.execute(
                delete(ChatMessageDB)
                .where(ChatMessageDB.patient_id == patient_id)
            )
            count = result.rowcount
            await db.commit()
            return {"patient_id": patient_id, "messages_deleted": count}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        return {"patient_id": patient_id, "messages_deleted": 0, "error": str(e)}


@router.websocket("/chat/{patient_id}/stream")
async def chat_stream(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for streaming chat responses.

    Args:
        websocket: WebSocket connection
        patient_id: The patient ID
    """
    await websocket.accept()
    logger.info(f"Chat WebSocket connected for patient {patient_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "No message provided"
                })
                continue

            # Check for escalation
            should_escalate, escalation_reason = _should_escalate(message)

            # Generate response
            response_text, sources = _get_mock_response(message, patient_id)

            # Stream response in chunks (simulating streaming)
            words = response_text.split()
            chunks = []
            current_chunk = []

            for word in words:
                current_chunk.append(word)
                if len(current_chunk) >= 5:  # Stream 5 words at a time
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            # Send chunks
            for i, chunk in enumerate(chunks):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk + " ",
                    "is_final": i == len(chunks) - 1
                })
                await asyncio.sleep(0.1)  # Simulate streaming delay

            # Send completion with metadata
            await websocket.send_json({
                "type": "complete",
                "sources": sources,
                "escalate": should_escalate,
                "escalation_reason": escalation_reason
            })

            # Store messages in history
            if patient_id not in _chat_histories:
                _chat_histories[patient_id] = []

            _chat_histories[patient_id].extend([
                ChatMessage(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    role="patient",
                    content=message
                ),
                ChatMessage(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    role="assistant",
                    content=response_text,
                    context_used={"sources": sources}
                )
            ])

    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        await websocket.close()
