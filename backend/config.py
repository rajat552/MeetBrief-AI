"""
MeetBrief AI — Configuration & Environment Validation
"""

import os
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings with strict validation.
    Loads from process environment or .env file if present.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --------------------------------------------------------------------------
    # Tavily Web Research Configuration
    # --------------------------------------------------------------------------
    TAVILY_API_KEY: str = Field(
        default="",
        description="API key for Tavily Search API"
    )

    # --------------------------------------------------------------------------
    # Bifrost AI Gateway Configuration (Primary Inference Route)
    # --------------------------------------------------------------------------
    BIFROST_BASE_URL: str = Field(
        default="http://localhost:8080/v1",
        description="OpenAI-compatible base URL for Bifrost AI Gateway"
    )
    BIFROST_VIRTUAL_KEY: str = Field(
        default="",
        description="Virtual key formatted as sk-bf-* for Bifrost authentication"
    )
    BIFROST_ENABLED: bool = Field(
        default=True,
        description="Toggle whether to attempt Bifrost Gateway routing"
    )
    BIFROST_PRIMARY_MODEL: str = Field(
        default="openai/gpt-4o",
        description="Primary model identifier routed through Bifrost"
    )
    BIFROST_FAST_MODEL: str = Field(
        default="groq/llama-3.3-70b-versatile",
        description="Fast extraction/verification model routed through Bifrost"
    )
    BIFROST_FALLBACK_MODEL: str = Field(
        default="openai/gpt-4o-mini",
        description="Lightweight model identifier routed through Bifrost"
    )

    # --------------------------------------------------------------------------
    # Direct Provider Fallback Configuration
    # --------------------------------------------------------------------------
    OPENAI_API_KEY: str = Field(
        default="",
        description="Direct OpenAI API key used when Bifrost is offline/disabled"
    )
    GROQ_API_KEY: str = Field(
        default="",
        description="Direct Groq API key used when Bifrost is offline/disabled"
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Direct Google Gemini API key used when Bifrost is offline/disabled"
    )

    # --------------------------------------------------------------------------
    # Omnidimension Voice AI Configuration (Community Partner)
    # --------------------------------------------------------------------------
    OMNIDIMENSION_API_KEY: str = Field(
        default="",
        description="API key for Omnidimension Voice AI executive audio briefings"
    )
    OMNIDIMENSION_BASE_URL: str = Field(
        default="https://api.omnidimension.ai/v1",
        description="Base URL for Omnidimension Voice AI endpoint"
    )
    OMNIDIMENSION_VOICE_ID: str = Field(
        default="executive-en-neutral",
        description="Voice persona ID for executive narration"
    )

    # --------------------------------------------------------------------------
    # Server & Runtime Configuration
    # --------------------------------------------------------------------------
    HOST: str = Field(default="127.0.0.1", description="API server host")
    PORT: int = Field(default=5000, description="API server port")
    ENVIRONMENT: Literal["development", "production", "test"] = Field(
        default="development",
        description="Runtime environment"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging verbosity")

    @field_validator("BIFROST_BASE_URL")
    @classmethod
    def normalize_base_url(cls, v: str) -> str:
        if v.endswith("/"):
            return v[:-1]
        return v

    def is_bifrost_configured(self) -> bool:
        """Checks if Bifrost gateway parameters are set."""
        return bool(self.BIFROST_ENABLED and self.BIFROST_BASE_URL and self.BIFROST_VIRTUAL_KEY)

    def is_openai_configured(self) -> bool:
        """Checks if direct OpenAI API key is set."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith("sk-"))

    def is_groq_configured(self) -> bool:
        """Checks if direct Groq API key is set."""
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY.startswith("gsk_"))

    def is_gemini_configured(self) -> bool:
        """Checks if direct Gemini API key is set."""
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY) > 10)

    def is_tavily_configured(self) -> bool:
        """Checks if Tavily search API key is set."""
        return bool(self.TAVILY_API_KEY and len(self.TAVILY_API_KEY) > 5)

    def is_omnidimension_configured(self) -> bool:
        """Checks if Omnidimension Voice AI API key is set."""
        return bool(self.OMNIDIMENSION_API_KEY and len(self.OMNIDIMENSION_API_KEY.strip()) > 5)


# Global settings singleton
settings = Settings()
