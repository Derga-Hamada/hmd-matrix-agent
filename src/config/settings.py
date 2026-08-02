"""
Application Configuration Settings.

Explicitly loads environment variables using python-dotenv.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Force Python to load the .env file in the root directory
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "HMD Matrix Agentic Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()