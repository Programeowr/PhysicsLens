"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    gemini_api_key: str = Field(..., description="Google Gemini API key")
    rate_limit: str = Field(
        default="10/minute", description="Rate limit for /parse endpoint"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    gemini_model: str = Field(
        default="gemini-2.5-flash", description="Gemini model to use"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton instance
settings = Settings()
