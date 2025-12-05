"""Patient Communication Agent for handling patient chat interactions."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from .base_agent import BaseAgent
from models.patient import PatientSummary
from models.messages import ChatMessage, ChatResponse
from services.llm_service import LLMService


class ConversationContext(BaseModel):
    """Context for patient conversation."""
    patient_id: str
    patient_summary: Optional[PatientSummary] = None
    treatment_plan_summary: Optional[str] = None
    recent_topics: List[str] = Field(default_factory=list)


class PatientCommInput(BaseModel):
    """Input for patient communication."""
    patient_id: str
    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    context: Optional[ConversationContext] = None


class PatientCommOutput(BaseModel):
    """Output from patient communication."""
    response: str
    sources_used: List[str] = Field(default_factory=list)
    escalate_to_human: bool = False
    escalation_reason: Optional[str] = None
    suggested_followups: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None  # "positive", "neutral", "concerned", "distressed"


class PatientCommunicationAgent(BaseAgent[PatientCommInput, PatientCommOutput]):
    """Agent that handles patient chat interactions.

    This agent:
    - Answers patient questions about their care
    - Explains medical concepts in plain language
    - Provides emotional support and empathy
    - Detects crisis situations for escalation
    - Never provides diagnoses, prescriptions, or prognoses
    - Directs clinical questions to the care team
    """

    # Crisis keywords that trigger immediate escalation
    CRISIS_KEYWORDS = [
        "suicide", "kill myself", "end my life", "want to die",
        "severe pain", "chest pain", "can't breathe", "difficulty breathing",
        "emergency", "911", "unconscious", "bleeding heavily",
        "overdose", "took too many", "allergic reaction", "swelling throat"
    ]

    # Keywords requiring escalation to care team
    ESCALATION_KEYWORDS = [
        "fever", "temperature", "infection", "new symptoms",
        "worse", "getting worse", "not working", "side effect",
        "can't eat", "can't sleep", "severe nausea", "vomiting blood",
        "blood in stool", "confusion", "falls", "fell down"
    ]

    # Topics that should be redirected to care team
    RESTRICTED_TOPICS = [
        "prognosis", "how long", "life expectancy", "survival",
        "should I take", "change my medication", "stop taking",
        "diagnosis", "do I have", "is it cancer"
    ]

    # Topics the bot can address
    ALLOWED_TOPICS = {
        "treatment_info": ["treatment", "therapy", "medication", "drug", "chemo", "immunotherapy"],
        "side_effects": ["side effect", "symptom", "nausea", "fatigue", "hair loss", "appetite"],
        "appointments": ["appointment", "visit", "schedule", "when", "next"],
        "general_support": ["scared", "worried", "anxious", "nervous", "stressed", "cope"],
        "clinical_trials": ["trial", "study", "research", "experimental"],
        "resources": ["support", "group", "help", "resource", "financial"],
    }

    def __init__(self, llm_service: LLMService, use_mock: bool = True):
        super().__init__(
            name="patient_communication",
            llm_service=llm_service,
            use_mock=use_mock
        )

    def get_system_prompt(self) -> str:
        return """You are a compassionate patient support AI for cancer patients.

STRICT RULES - YOU MUST FOLLOW:
1. NEVER diagnose conditions or suggest diagnoses
2. NEVER prescribe or recommend specific medications
3. NEVER provide prognosis or life expectancy information
4. NEVER make treatment decisions - always defer to the care team
5. NEVER dismiss patient concerns - take everything seriously
6. ALWAYS recommend contacting care team for medical concerns
7. ALWAYS escalate crisis situations immediately

YOUR ROLE:
- Provide information about treatments and side effects in plain language
- Offer emotional support and empathy
- Help patients understand their care plan
- Direct clinical questions to the appropriate care team member
- Suggest helpful resources and support services

COMMUNICATION STYLE:
- Use warm, empathetic language
- Explain medical terms simply
- Acknowledge emotions and concerns
- Be encouraging but realistic
- Keep responses focused and helpful"""

    async def execute(self, input_data: PatientCommInput) -> PatientCommOutput:
        """Execute patient communication using LLM."""
        # Check for crisis keywords first
        escalate, reason = self._check_for_crisis(input_data.message)
        if escalate:
            return PatientCommOutput(
                response=self._get_crisis_response(reason),
                escalate_to_human=True,
                escalation_reason=reason,
                sentiment="distressed"
            )

        prompt = self._build_conversation_prompt(input_data)

        response = await self._call_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )

        return self._process_llm_response(response, input_data)

    def _mock_execute(self, input_data: PatientCommInput) -> PatientCommOutput:
        """Generate mock patient communication response."""
        message = input_data.message.lower()

        # Check for crisis keywords
        escalate, reason = self._check_for_crisis(message)
        if escalate:
            return PatientCommOutput(
                response=self._get_crisis_response(reason),
                escalate_to_human=True,
                escalation_reason=reason,
                sentiment="distressed"
            )

        # Check for escalation keywords
        needs_escalation, esc_reason = self._check_for_escalation(message)

        # Check for restricted topics
        is_restricted, redirect_response = self._check_restricted_topic(message)
        if is_restricted:
            return PatientCommOutput(
                response=redirect_response,
                escalate_to_human=needs_escalation,
                escalation_reason=esc_reason if needs_escalation else None,
                suggested_followups=["Ask your oncologist about this at your next visit"],
                topics_discussed=["restricted_topic"],
                sentiment="neutral"
            )

        # Identify topic and generate response
        topic = self._identify_topic(message)
        response, sources, followups = self._generate_response(message, topic, input_data.context)

        # Determine sentiment
        sentiment = self._assess_patient_sentiment(message)

        return PatientCommOutput(
            response=response,
            sources_used=sources,
            escalate_to_human=needs_escalation,
            escalation_reason=esc_reason if needs_escalation else None,
            suggested_followups=followups,
            topics_discussed=[topic] if topic else [],
            sentiment=sentiment
        )

    def _check_for_crisis(self, message: str) -> tuple:
        """Check for crisis situations requiring immediate escalation."""
        message_lower = message.lower()

        for keyword in self.CRISIS_KEYWORDS:
            if keyword in message_lower:
                if any(term in keyword for term in ["suicide", "kill", "die", "end my life"]):
                    return True, "Mental health crisis detected"
                elif any(term in keyword for term in ["chest pain", "breathe", "911"]):
                    return True, "Medical emergency keywords detected"
                else:
                    return True, f"Crisis keyword detected: {keyword}"

        return False, None

    def _check_for_escalation(self, message: str) -> tuple:
        """Check for keywords requiring care team notification."""
        message_lower = message.lower()

        for keyword in self.ESCALATION_KEYWORDS:
            if keyword in message_lower:
                return True, f"Patient reported: {keyword}"

        return False, None

    def _check_restricted_topic(self, message: str) -> tuple:
        """Check if message asks about restricted topics."""
        message_lower = message.lower()

        for topic in self.RESTRICTED_TOPICS:
            if topic in message_lower:
                if "prognosis" in topic or "how long" in topic or "survival" in topic:
                    response = (
                        "I understand you have questions about what to expect. These are important "
                        "conversations to have with your oncologist, who can give you personalized "
                        "information based on your specific situation. I'd encourage you to write down "
                        "your questions and discuss them at your next appointment. Would you like me "
                        "to help you prepare questions for your care team?"
                    )
                elif "should I take" in topic or "medication" in topic:
                    response = (
                        "Medication decisions should always be made with your care team. "
                        "Please contact your oncologist or nurse before making any changes to your "
                        "medications. Is there something specific you're concerned about that I can "
                        "help explain?"
                    )
                else:
                    response = (
                        "That's an important question that your care team is best equipped to answer. "
                        "I'd recommend reaching out to your oncologist's office to discuss this. "
                        "Is there anything else I can help with in the meantime?"
                    )
                return True, response

        return False, None

    def _identify_topic(self, message: str) -> Optional[str]:
        """Identify the topic of the message."""
        message_lower = message.lower()

        for topic, keywords in self.ALLOWED_TOPICS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return topic

        return "general_support"  # Default to general support

    def _generate_response(
        self,
        message: str,
        topic: str,
        context: Optional[ConversationContext]
    ) -> tuple:
        """Generate response based on topic."""
        message_lower = message.lower()
        sources = []
        followups = []

        if topic == "treatment_info":
            if "what is" in message_lower or "tell me about" in message_lower:
                if "osimertinib" in message_lower or "tagrisso" in message_lower:
                    response = (
                        "Osimertinib (brand name Tagrisso) is a targeted therapy medication that works by "
                        "blocking a protein called EGFR that helps cancer cells grow. It's taken as a "
                        "pill once daily. Common side effects include diarrhea, skin rash, and dry skin, "
                        "which are usually manageable. Your care team can give you specific information "
                        "about how it relates to your treatment plan."
                    )
                    sources = ["NCCN Guidelines", "Drug manufacturer information"]
                    followups = [
                        "Would you like to know more about managing side effects?",
                        "Do you have questions about your treatment schedule?"
                    ]
                else:
                    response = (
                        "I'd be happy to help explain your treatment. Could you tell me which specific "
                        "treatment or medication you'd like to know more about? I can provide general "
                        "information about how treatments work and what to expect."
                    )
                    followups = ["What treatment would you like to know about?"]
            else:
                response = (
                    "I can help explain aspects of your treatment plan. What specific questions do you "
                    "have? For changes to your treatment plan, please speak with your oncologist."
                )
                followups = ["What aspect of your treatment would you like to discuss?"]

        elif topic == "side_effects":
            if any(se in message_lower for se in ["nausea", "sick", "throw up"]):
                response = (
                    "Nausea is a common side effect of many cancer treatments. Here are some tips "
                    "that may help:\n\n"
                    "- Eat small, frequent meals instead of large ones\n"
                    "- Try bland foods like crackers, toast, or bananas\n"
                    "- Stay hydrated with small sips of clear fluids\n"
                    "- Take anti-nausea medications as prescribed\n"
                    "- Avoid strong smells and greasy foods\n\n"
                    "If nausea is severe or you're unable to keep fluids down, please contact your "
                    "care team - they may be able to adjust your anti-nausea medications."
                )
                sources = ["Patient education materials", "Symptom management guidelines"]
                followups = [
                    "Are you taking anti-nausea medication?",
                    "Would you like tips for staying hydrated?"
                ]
            elif "fatigue" in message_lower or "tired" in message_lower:
                response = (
                    "Fatigue is very common during cancer treatment. Here are some strategies that "
                    "may help:\n\n"
                    "- Prioritize rest and don't hesitate to take naps\n"
                    "- Light physical activity, like short walks, can actually help boost energy\n"
                    "- Plan activities for times when you have the most energy\n"
                    "- Accept help from friends and family\n"
                    "- Stay hydrated and eat nutritious foods when possible\n\n"
                    "If fatigue is significantly impacting your daily life, mention it to your care "
                    "team - there may be underlying causes they can address."
                )
                sources = ["Patient education materials"]
                followups = [
                    "How has your energy level been compared to last week?",
                    "Would you like information about support services?"
                ]
            else:
                response = (
                    "Managing side effects is an important part of treatment. Could you tell me more "
                    "about what you're experiencing? I can provide general information and suggestions, "
                    "though your care team should be informed about any concerning symptoms."
                )
                followups = ["What symptoms are you experiencing?"]

        elif topic == "general_support":
            if any(emotion in message_lower for emotion in ["scared", "worried", "anxious", "nervous"]):
                response = (
                    "It's completely normal to feel worried or scared - these feelings are a natural "
                    "part of going through cancer treatment. You're dealing with a lot, and it takes "
                    "courage to face each day.\n\n"
                    "Some things that might help:\n"
                    "- Talk to someone you trust about your feelings\n"
                    "- Consider joining a support group with others who understand\n"
                    "- Practice relaxation techniques like deep breathing\n"
                    "- Focus on one day at a time\n\n"
                    "Would you like information about support resources or counseling services? "
                    "Your care team also includes social workers who specialize in emotional support."
                )
                sources = ["Patient support resources"]
                followups = [
                    "Would you like information about support groups?",
                    "Would talking to a counselor be helpful?"
                ]
            else:
                response = (
                    "I'm here to help and support you through your treatment journey. Please feel free "
                    "to ask me anything about your care - I can provide information, answer questions, "
                    "or just listen if you need someone to talk to."
                )
                followups = [
                    "Is there something specific on your mind?",
                    "Would you like information about support resources?"
                ]

        elif topic == "clinical_trials":
            response = (
                "Clinical trials can be an important option to consider. They offer access to new "
                "treatments and close monitoring by medical experts. Your care team has identified "
                "some trials that might be relevant to your situation based on your specific cancer "
                "type and genetic markers.\n\n"
                "I'd recommend discussing clinical trial options with your oncologist - they can "
                "explain which trials you might be eligible for and help you understand the potential "
                "benefits and considerations."
            )
            sources = ["Clinical trial information", "Patient treatment plan"]
            followups = [
                "Would you like to know what questions to ask about clinical trials?",
                "Would you like general information about how clinical trials work?"
            ]

        elif topic == "resources":
            response = (
                "There are many support resources available to you:\n\n"
                "- **Support Groups**: Connect with others going through similar experiences\n"
                "- **Financial Assistance**: Programs to help with treatment costs\n"
                "- **Social Workers**: Help navigating the healthcare system\n"
                "- **Nutritionists**: Guidance on eating well during treatment\n"
                "- **Mental Health**: Counselors who specialize in cancer patients\n\n"
                "Your care coordinator can help connect you with specific resources. Would you like "
                "more information about any of these?"
            )
            sources = ["Patient support services"]
            followups = [
                "Which type of support would be most helpful?",
                "Would you like contact information for specific services?"
            ]

        else:
            response = (
                "Thank you for reaching out. I'm here to help answer your questions about your care "
                "and provide support. Is there something specific I can help you with today?"
            )
            followups = ["What would you like to know?"]

        return response, sources, followups

    def _get_crisis_response(self, reason: str) -> str:
        """Get response for crisis situation."""
        if "mental health" in reason.lower():
            return (
                "I'm very concerned about what you've shared. Your feelings matter, and help is "
                "available right now.\n\n"
                "**Please call or text 988** (Suicide and Crisis Lifeline) - they're available 24/7.\n\n"
                "If you're in immediate danger, please call 911.\n\n"
                "I'm notifying your care team right away so they can reach out to support you. "
                "You don't have to face this alone."
            )
        else:
            return (
                "Based on what you've described, this sounds like it could be urgent. "
                "**Please call 911 or go to your nearest emergency room immediately.**\n\n"
                "I'm alerting your care team about this message. If you're unable to get to "
                "emergency care, please call your oncologist's office right away - they have "
                "after-hours support available.\n\n"
                "Your safety is the top priority."
            )

    def _assess_patient_sentiment(self, message: str) -> str:
        """Assess patient sentiment from message."""
        message_lower = message.lower()

        distress_words = ["scared", "terrified", "hopeless", "can't", "worst", "horrible"]
        concern_words = ["worried", "anxious", "nervous", "unsure", "confused"]
        positive_words = ["better", "good", "thank", "grateful", "hopeful", "improving"]

        if any(word in message_lower for word in distress_words):
            return "distressed"
        elif any(word in message_lower for word in concern_words):
            return "concerned"
        elif any(word in message_lower for word in positive_words):
            return "positive"
        else:
            return "neutral"

    def _process_llm_response(
        self,
        llm_response: str,
        input_data: PatientCommInput
    ) -> PatientCommOutput:
        """Process LLM response into structured output."""
        # Check for escalation in the LLM response
        needs_escalation, reason = self._check_for_escalation(input_data.message)

        return PatientCommOutput(
            response=llm_response,
            sources_used=["Patient education materials"],
            escalate_to_human=needs_escalation,
            escalation_reason=reason,
            suggested_followups=[],
            topics_discussed=[self._identify_topic(input_data.message)],
            sentiment=self._assess_patient_sentiment(input_data.message)
        )

    def _build_conversation_prompt(self, input_data: PatientCommInput) -> str:
        """Build conversation prompt."""
        history_text = ""
        if input_data.conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in input_data.conversation_history[-5:]  # Last 5 messages
            ])

        context_text = ""
        if input_data.context:
            context_text = f"""
Patient Context:
- Treatment Plan: {input_data.context.treatment_plan_summary or 'Not available'}
- Recent Topics: {', '.join(input_data.context.recent_topics) if input_data.context.recent_topics else 'None'}
"""

        return f"""Respond to this patient message with empathy and helpful information.

{context_text}

Conversation History:
{history_text if history_text else 'No previous messages'}

Patient Message: {input_data.message}

Remember:
- Be warm and supportive
- Use plain language
- Direct clinical questions to the care team
- Never diagnose, prescribe, or give prognosis
- Acknowledge emotions

Respond naturally and helpfully:"""
