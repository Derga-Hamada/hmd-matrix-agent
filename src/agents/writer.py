"""
Writer Agent for generating video scripts from research data.
"""

import json
import logging
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from src.agents.base import BaseAgent
from src.config.settings import settings

logger = logging.getLogger("hmd_matrix")


class VideoScriptResult(BaseModel):
    hook: str = Field(description="An engaging, fast-paced 15-second intro hook to grab attention.")
    main_body: str = Field(description="The core script explaining the topic clearly, formatted for a speaker.")
    call_to_action: str = Field(description="A strong closing statement asking viewers to subscribe or take action.")


class WriterAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(name="WriterAgent")
        self.model = model_name
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Initializing WriterAgent [Model: {self.model}]")

    async def process(self, prompt: str) -> dict:
        """Transforms structured research data into a video script."""
        logger.info("WriterAgent generating video script...")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Transform this research data into a compelling YouTube video script:\n\n{prompt}",
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert YouTube scriptwriter for the HMD Matrix productivity channel. Write dynamic, clear, and highly engaging scripts.",
                    response_mime_type="application/json",
                    response_schema=VideoScriptResult,
                ),
            )

            return json.loads(response.text)

        except Exception as e:
            logger.error(f"WriterAgent failed: {str(e)}")
            return {"error": f"Script generation failed: {str(e)}"}