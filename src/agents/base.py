"""
Abstract Base Agent Architecture.

Provides the foundational interface that all domain-specific AI agents must inherit,
ensuring a unified asynchronous execution contract across the distributed engine.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.core.logger import logger
from src.core.schemas import AgentRequest, AgentResponse


class BaseAgent(ABC):
    """
    Abstract interface for AI execution nodes.
    """

    def __init__(self, agent_name: str, model_version: str = "default"):
        self.agent_name = agent_name
        self.model_version = model_version
        logger.info(f"Initializing {self.agent_name} [Model: {self.model_version}]")

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Asynchronously processes a task request.
        
        This method MUST be overridden by all child agent classes.
        
        Args:
            request (AgentRequest): The validated input payload.
            
        Returns:
            AgentResponse: The strictly typed output payload.
        """
        pass

    async def _handle_error(self, task_id: str, error: Exception) -> AgentResponse:
        """Standardized internal error handler for agent crash recovery."""
        logger.error(f"[{self.agent_name}] Task {task_id} failed: {str(error)}")
        return AgentResponse(
            task_id=task_id,
            status="failed",
            error_message=str(error)
        )