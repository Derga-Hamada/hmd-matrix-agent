"""
Application Configuration Settings.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file variables into environment
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "HMD Matrix Agentic Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()