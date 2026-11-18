"""
Unit Tests for Configuration & Environment Settings
"""

import pytest
from backend.config import Settings


def test_settings_defaults():
    s = Settings(
        TAVILY_API_KEY="tvly-mock",
        BIFROST_VIRTUAL_KEY="sk-bf-test",
        BIFROST_ENABLED=True,
        OPENAI_API_KEY="sk-test",
        GROQ_API_KEY="gsk_test"
    )
    assert s.BIFROST_BASE_URL == "http://localhost:8080/v1"
    assert s.BIFROST_PRIMARY_MODEL == "openai/gpt-4o"
    assert s.BIFROST_FAST_MODEL == "groq/llama-3.3-70b-versatile"
    assert s.PORT == 5000
    assert s.is_bifrost_configured() is True
    assert s.is_openai_configured() is True
    assert s.is_groq_configured() is True
    assert s.is_tavily_configured() is True


def test_base_url_trailing_slash_normalization():
    s = Settings(BIFROST_BASE_URL="http://localhost:8080/v1/")
    assert s.BIFROST_BASE_URL == "http://localhost:8080/v1"


def test_bifrost_disabled_check():
    s = Settings(BIFROST_ENABLED=False, BIFROST_VIRTUAL_KEY="sk-bf-test")
    assert s.is_bifrost_configured() is False


def test_key_prefix_validation():
    s_invalid = Settings(OPENAI_API_KEY="invalid-key", GROQ_API_KEY="invalid-key")
    assert s_invalid.is_openai_configured() is False
    assert s_invalid.is_groq_configured() is False
