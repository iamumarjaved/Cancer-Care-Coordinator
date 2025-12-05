"""Base Agent class for all AI agents."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Any, Optional
from pydantic import BaseModel
import logging

from services.llm_service import LLMService

# Generic type variables for input and output
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentResult(BaseModel):
    """Base result model for agent outputs."""
    success: bool = True
    error_message: Optional[str] = None


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all AI agents.

    Provides common functionality for:
    - LLM interaction
    - Mock mode support
    - Logging
    - Error handling

    Subclasses must implement:
    - execute(): Main agent logic
    - get_system_prompt(): System prompt for LLM
    - _mock_execute(): Mock response for testing
    """

    def __init__(
        self,
        name: str,
        llm_service: LLMService,
        use_mock: bool = True
    ):
        """Initialize the agent.

        Args:
            name: Human-readable agent name
            llm_service: LLM service for completions
            use_mock: Whether to use mock responses
        """
        self.name = name
        self.llm_service = llm_service
        self._use_mock = use_mock
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute the agent's main task.

        Args:
            input_data: Input data model

        Returns:
            Output data model
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def _mock_execute(self, input_data: InputT) -> OutputT:
        """Execute with mock response for testing.

        Args:
            input_data: Input data model

        Returns:
            Mock output data model
        """
        pass

    async def _call_llm(
        self,
        prompt: str,
        output_model: Optional[Type[BaseModel]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Any:
        """Call the LLM with the agent's system prompt.

        Args:
            prompt: User prompt
            output_model: Optional Pydantic model for structured output
            temperature: LLM temperature
            max_tokens: Maximum tokens in response

        Returns:
            LLM response (string or structured model)
        """
        system_prompt = self.get_system_prompt()

        if output_model:
            return await self.llm_service.complete_structured(
                prompt=prompt,
                output_model=output_model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            return await self.llm_service.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

    async def run(self, input_data: InputT) -> OutputT:
        """Run the agent with error handling.

        This is the main entry point that handles mock mode
        and error handling.

        Args:
            input_data: Input data model

        Returns:
            Output data model
        """
        self.logger.info(f"Starting {self.name} execution")

        try:
            if self._use_mock:
                self.logger.debug(f"{self.name} using mock mode")
                result = self._mock_execute(input_data)
            else:
                result = await self.execute(input_data)

            self.logger.info(f"{self.name} execution completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"{self.name} execution failed: {str(e)}")
            raise

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', mock={self._use_mock})>"
