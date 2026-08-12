"""
Base Agent interface for the HMD Matrix Engine.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("hmd_matrix")


class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, prompt: str) -> dict:
        """Process an incoming task prompt and return a structured dictionary."""
        pass