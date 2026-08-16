"""
Social Media Agent for transforming video scripts into platform-specific content.
"""
import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from src.agents.base import BaseAgent
from src.config.settings import settings

logger = logging.getLogger("hmd_matrix")

class SocialMediaResult(BaseModel):
    instagram_caption: str = Field(description="A highly engaging caption for Instagram with relevant emojis, formatting, and 5-7 strategic hashtags.")
    facebook_post: str = Field(description="A conversational, community-focused Facebook post designed to spark discussion, comments, and shares.")
    visual_idea: str = Field(description="A brief prompt describing the ideal graphic or video aesthetic to accompany these posts.")

class SocialAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-flash-latest"):
        super().__init__(name="SocialAgent")
        self.model = model_name
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Initializing SocialAgent [Model: {self.model}]")

    async def process(self, script_data: str) -> dict:
        """Transforms structured video script data into Instagram and Facebook posts."""
        logger.info("SocialAgent generating Instagram and Facebook content...")
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"Repurpose this video script into an Instagram caption and a Facebook post:\n\n{script_data}",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert social media manager for the HMD Matrix brand. "
                        "The brand focuses on analytical productivity and self-improvement for Generation Z. "
                        "Write dynamic, clear, and highly engaging copy tailored specifically for Instagram and Facebook audiences."
                    ),
                    response_mime_type="application/json",
                    response_schema=SocialMediaResult,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"SocialAgent failed: {str(e)}")
            return {"error": f"Social content generation failed: {str(e)}"}