"""
Runtime Application Configuration.

Leverages Pydantic Settings for deterministic validation of environment inputs.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings populated via environment variables or .env file."""

    # Project Information
    PROJECT_NAME: str = Field(
        default="HMD Matrix Agentic Engine",
        description="Name of the agent engine instance.",
    )
    VERSION: str = Field(default="0.1.0", description="Semantic version number.")
    ENVIRONMENT: str = Field(
        default="development", description="Execution environment (development, staging, production)."
    )
    DEBUG: bool = Field(default=False, description="Enable verbose debug logging.")

    # Core Distributed Infrastructure Defaults
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Connection URL for task distribution broker.",
    )
    WORKER_CONCURRENCY: int = Field(
        default=4, description="Maximum concurrent agent processes per node."
    )

    # API Keys / External Provider Configs
    OPENAI_API_KEY: str = Field(
        default="", description="Secret key for LLM provider operations."
    )

    # Path Settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Global singleton instance for app-wide import
settings = Settings()