"""
Research Agent implementation using Google Gemini.
"""

import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.config.settings import settings

logger = logging.getLogger("hmd_matrix")


# Define the exact JSON schema required from Gemini
class ResearchResult(BaseModel):
    analyzed_topic: str = Field(description="The core topic analyzed.")
    core_mechanism: str = Field(
        description="A concise explanation of how the framework works."
    )
    effectiveness_score: str = Field(
        description="A rating of its effectiveness (e.g., 'High', 'Medium') with a brief reason."
    )
    content_angles: list[str] = Field(
        description="3-5 actionable angles for content creation based on the topic."
    )


class ResearchAgent(BaseAgent):

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(name="ResearchAgent")
        self.model = model_name

        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is empty! Please check your .env file."
            )

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Initializing ResearchAgent [Model: {self.model}]")

    async def process(self, prompt: str) -> dict:
        """Sends prompt to Gemini and enforces strict Pydantic JSON output."""
        logger.info(f"Agent processing prompt: '{prompt}'")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are an elite productivity and systems research analyst. Provide highly analytical, structured insights.",
                    response_mime_type="application/json",
                    response_schema=ResearchResult,
                ),
            )

            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Gemini LLM Processing failed: {str(e)}")
            return {"error": f"Agent failed to generate a response: {str(e)}"}