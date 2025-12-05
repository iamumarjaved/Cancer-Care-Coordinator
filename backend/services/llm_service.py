"""LLM Service - Wrapper for LLM calls with mock/real mode support."""

import json
import hashlib
import logging
from typing import Type, Optional, Any
from pydantic import BaseModel

from config import settings
from services.tracing import get_tracer, _langsmith_enabled

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions with mock mode support."""

    def __init__(self, use_mock: bool = None, model: str = None):
        """Initialize LLM service.

        Args:
            use_mock: If True, return deterministic mock responses (defaults to config)
            model: LLM model to use (defaults to config setting)
        """
        self._use_mock = use_mock if use_mock is not None else settings.USE_MOCK_LLM
        self._model = model or settings.LLM_MODEL
        self._client = None

        if not self._use_mock:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        logger.info(f"LLMService initialized (mock={self._use_mock}, model={self._model})")

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        tracer = get_tracer()

        if self._use_mock:
            # Start tracing span for mock call
            span = tracer.start_llm_span(
                operation="chat.completion.mock",
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                metadata={"mock": True, "prompt_length": len(prompt)}
            )
            try:
                result = self._get_mock_response(prompt, system_prompt or "")
                tracer.complete_llm_span(span, response_text=result)
                return result
            except Exception as e:
                tracer.fail_llm_span(span, str(e))
                raise

        # Start tracing span for real LLM call
        span = tracer.start_llm_span(
            operation="chat.completion",
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            metadata={"prompt_length": len(prompt)}
        )

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use LangSmith tracing if available
            if _langsmith_enabled:
                response = await self._traced_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            result = response.choices[0].message.content

            # Extract usage data for tracing
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            tracer.complete_llm_span(span, response_text=result, usage=usage)
            return result

        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            tracer.fail_llm_span(span, str(e))
            raise

    async def _traced_completion(self, messages: list, temperature: float, max_tokens: int):
        """Make an OpenAI completion call with LangSmith tracing."""
        from langsmith import traceable

        @traceable(run_type="llm", name="openai_chat_completion")
        async def traced_call(messages, model, temperature, max_tokens):
            return await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

        return await traced_call(
            messages=messages,
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def complete_structured(
        self,
        prompt: str,
        output_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        retry_count: int = 2
    ) -> BaseModel:
        """Generate a structured output from the LLM.

        Args:
            prompt: The user prompt
            output_model: Pydantic model for output parsing
            system_prompt: Optional system prompt
            temperature: Sampling temperature (lower for structured output)
            max_tokens: Maximum tokens in response
            retry_count: Number of retries on failure

        Returns:
            Parsed Pydantic model instance
        """
        # Add schema to system prompt
        schema_prompt = f"""
You must respond with valid JSON that matches this schema:
{json.dumps(output_model.model_json_schema(), indent=2)}

Only respond with the JSON, no other text.
"""
        full_system_prompt = (system_prompt or "") + "\n\n" + schema_prompt

        if self._use_mock:
            return self._get_mock_structured_response(prompt, output_model)

        last_error = None
        response_text = None

        for attempt in range(retry_count + 1):
            try:
                response_text = await self.complete(
                    prompt=prompt,
                    system_prompt=full_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Check for empty response
                if not response_text or not response_text.strip():
                    logger.warning(f"LLM returned empty response (attempt {attempt + 1})")
                    if attempt < retry_count:
                        continue
                    raise ValueError("LLM returned empty response after retries")

                # Parse JSON from response - with robust extraction
                json_text = self._extract_json(response_text)

                if not json_text or not json_text.strip():
                    logger.warning(f"No JSON found in response (attempt {attempt + 1})")
                    if attempt < retry_count:
                        continue
                    raise ValueError("No JSON found in LLM response")

                data = json.loads(json_text)
                return output_model.model_validate(data)

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                logger.debug(f"Response text (first 500 chars): {response_text[:500] if response_text else 'None'}")
                if attempt < retry_count:
                    continue
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"LLM structured completion error (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    continue
                raise

        # Should not reach here, but just in case
        raise last_error or ValueError("Failed to get structured response")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response text robustly.

        Handles:
        - Markdown code blocks
        - Leading/trailing text
        - Nested braces/brackets
        """
        import re

        # Try markdown code blocks first
        if "```json" in text:
            match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if match:
                return match.group(1).strip()

        if "```" in text:
            match = re.search(r'```\s*([\s\S]*?)\s*```', text)
            if match:
                return match.group(1).strip()

        # Try to find JSON object or array
        text = text.strip()

        # Find the start of JSON (first { or [)
        obj_start = text.find('{')
        arr_start = text.find('[')

        if obj_start == -1 and arr_start == -1:
            return text  # No JSON found, return as-is

        # Use the first occurring JSON structure
        if obj_start == -1:
            start = arr_start
            start_char, end_char = '[', ']'
        elif arr_start == -1:
            start = obj_start
            start_char, end_char = '{', '}'
        elif obj_start < arr_start:
            start = obj_start
            start_char, end_char = '{', '}'
        else:
            start = arr_start
            start_char, end_char = '[', ']'

        # Find matching end by counting braces/brackets
        depth = 0
        end = start
        for i, char in enumerate(text[start:], start):
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        return text[start:end]

    def _get_mock_response(self, prompt: str, context: str) -> str:
        """Generate deterministic mock response based on prompt.

        Args:
            prompt: The user prompt
            context: Additional context (system prompt)

        Returns:
            Mock response string
        """
        # Create deterministic hash-based response
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

        # Detect intent from prompt keywords
        prompt_lower = prompt.lower()

        if "patient" in prompt_lower and "summary" in prompt_lower:
            return f"""Based on the patient data provided, here is a comprehensive summary:

**Demographics**: The patient is a 63-year-old male with a history of smoking (30 pack-years).

**Cancer Details**: Diagnosed with Stage IIIA Non-Small Cell Lung Cancer (Adenocarcinoma) located in the right upper lobe. TNM staging is T2N2M0 with mediastinal lymph node involvement.

**Key Comorbidities**:
- Type 2 Diabetes Mellitus (moderate)
- Chronic Kidney Disease Stage 3 (GFR 58)

**Treatment Considerations**:
- Renal dosing required for chemotherapy
- Diabetes management during treatment
- ECOG Performance Status 1 (restricted but ambulatory)

[Response ID: {prompt_hash}]"""

        elif "genomic" in prompt_lower or "mutation" in prompt_lower:
            return f"""Genomic Analysis Summary:

**Actionable Mutations Found**:
1. EGFR Exon 19 Deletion (p.E746_A750del)
   - Classification: Pathogenic, Actionable
   - Allele Frequency: 34%
   - FDA-approved therapies: Osimertinib, Erlotinib, Afatinib, Gefitinib

**Immunotherapy Markers**:
- PD-L1 Expression: 15% (low)
- TMB: 4 mutations/Mb (low)
- MSI Status: Stable

**Recommendation**: Given the EGFR exon 19 deletion, osimertinib (Tagrisso) is the preferred first-line therapy per NCCN guidelines.

[Response ID: {prompt_hash}]"""

        elif "trial" in prompt_lower or "clinical" in prompt_lower:
            return f"""Clinical Trial Matching Results:

**Matched Trials**: 8 trials identified, 3 highly relevant

1. **NCT04487080 - MARIPOSA-2** (Match Score: 94%)
   - Phase III study of amivantamab + lazertinib vs chemotherapy
   - Requires EGFR exon 19 deletion or L858R - PATIENT ELIGIBLE
   - Location: Memorial Sloan Kettering (12 miles)

2. **NCT05388669 - FLAURA3** (Match Score: 88%)
   - Phase III osimertinib combinations
   - EGFR-mutant NSCLC - PATIENT ELIGIBLE
   - Location: Dana-Farber Cancer Institute (215 miles)

3. **NCT04141644 - PAPILLON** (Match Score: 82%)
   - Amivantamab + chemo for EGFR+ NSCLC
   - Stage III-IV required - PATIENT ELIGIBLE

[Response ID: {prompt_hash}]"""

        elif "treatment" in prompt_lower or "recommendation" in prompt_lower:
            return f"""Treatment Recommendations:

**Rank 1: Osimertinib (Tagrisso)** - STRONGLY RECOMMENDED
- Confidence: 95%
- Rationale: EGFR exon 19 deletion with 80% response rate
- Patient-specific: No dose adjustment needed for CKD Stage 3
- Expected PFS: 18.9 months

**Rank 2: Clinical Trial MARIPOSA-2** - RECOMMENDED
- Confidence: 85%
- Rationale: Novel combination may improve outcomes
- Consideration: Requires travel, more monitoring

**Rank 3: Erlotinib + Chemotherapy** - ALTERNATIVE
- Confidence: 75%
- Rationale: FDA-approved for EGFR+ NSCLC
- Note: Less preferred than osimertinib per NCCN

[Response ID: {prompt_hash}]"""

        elif "chat" in prompt_lower or "explain" in prompt_lower or "question" in prompt_lower:
            return f"""I understand you have questions about your treatment. Here's some helpful information:

The treatment plan your oncology team has recommended is based on the specific characteristics of your cancer, including the genetic mutations found in your tumor. The EGFR mutation your cancer has means it may respond very well to a type of medication called a targeted therapy.

This is generally good news because targeted therapies often have fewer side effects than traditional chemotherapy and can be very effective for patients with this type of mutation.

Your care team will discuss all the options with you and help you make the best decision for your situation. Please don't hesitate to ask them any questions during your next appointment.

Is there anything specific you'd like me to explain further?

[Response ID: {prompt_hash}]"""

        else:
            return f"""Analysis complete. Based on the provided information, I have processed the request and generated relevant insights.

Key findings have been identified and documented. Please review the detailed output for specific recommendations and next steps.

[Response ID: {prompt_hash}]"""

    def _get_mock_structured_response(
        self,
        prompt: str,
        output_model: Type[BaseModel]
    ) -> BaseModel:
        """Generate deterministic mock structured response.

        Args:
            prompt: The user prompt
            output_model: Pydantic model for output

        Returns:
            Mock Pydantic model instance
        """
        # Get model field names and types
        fields = output_model.model_fields
        mock_data = {}

        for field_name, field_info in fields.items():
            field_type = field_info.annotation

            # Generate mock data based on field type
            if field_type == str:
                mock_data[field_name] = f"Mock {field_name}"
            elif field_type == int:
                mock_data[field_name] = 1
            elif field_type == float:
                mock_data[field_name] = 0.85
            elif field_type == bool:
                mock_data[field_name] = True
            elif field_type == list or str(field_type).startswith("list"):
                mock_data[field_name] = []
            elif field_type == dict or str(field_type).startswith("dict"):
                mock_data[field_name] = {}
            else:
                # Try to use default if available
                if field_info.default is not None:
                    mock_data[field_name] = field_info.default
                else:
                    mock_data[field_name] = None

        try:
            return output_model.model_validate(mock_data)
        except Exception as e:
            logger.warning(f"Could not create mock structured response: {e}")
            # Return with minimal required fields
            return output_model.model_construct(**mock_data)
