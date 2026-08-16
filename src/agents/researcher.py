import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from src.agents.base import BaseAgent
from src.config.settings import settings

logger = logging.getLogger("hmd_matrix")


class ResearchResult(BaseModel):
    topic: str = Field(description="The core subject analyzed.")
    core_mechanism: str = Field(description="How the topic works under the hood based on verified facts.")
    effectiveness_score: int = Field(description="Rating from 1-10 on productivity impact.")
    content_angles: list[str] = Field(description="3 high-performing content angles or takeaways.")


class ResearchAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-flash-latest"):
        super().__init__(name="ResearchAgent")
        self.model = model_name
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Initializing ResearchAgent with Web Search [Model: {self.model}]")

    async def process(self, prompt: str) -> dict:
        """Processes a prompt using Gemini equipped with Search Grounding (with fallback)."""
        logger.info(f"ResearchAgent searching web and analyzing: '{prompt}'")

        # Try with Web Search Grounding first
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Perform real-time research on this topic: {prompt}",
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert technical researcher. Search for accurate, up-to-date facts and distill them into structured analysis.",
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    response_mime_type="application/json",
                    response_schema=ResearchResult,
                ),
            )
            return json.loads(response.text)

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Search Grounding quota exceeded. Falling back to base model (without Web Search)...")
                try:
                    # Fallback: Run without google_search tool
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=f"Perform structured research on this topic: {prompt}",
                        config=types.GenerateContentConfig(
                            system_instruction="You are an expert technical researcher. Distill key facts into structured analysis.",
                            response_mime_type="application/json",
                            response_schema=ResearchResult,
                        ),
                    )
                    return json.loads(response.text)
                except Exception as fallback_err:
                    logger.error(f"ResearchAgent fallback failed: {str(fallback_err)}")
                    return {"error": f"Agent failed to generate a response: {str(fallback_err)}"}
            else:
                logger.error(f"ResearchAgent failed: {str(e)}")
                return {"error": f"Agent failed to generate a response: {str(e)}"}