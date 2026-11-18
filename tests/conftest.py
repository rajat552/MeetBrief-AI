"""
MeetBrief AI — Pytest Configuration & Mock Fixtures
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.config import Settings


@pytest.fixture
def mock_settings():
    """Provides isolated test settings."""
    return Settings(
        TAVILY_API_KEY="tvly-mock-test-key-12345",
        BIFROST_BASE_URL="http://localhost:8080/v1",
        BIFROST_VIRTUAL_KEY="sk-bf-test-virtual-key",
        BIFROST_ENABLED=True,
        BIFROST_PRIMARY_MODEL="openai/gpt-4o",
        BIFROST_FAST_MODEL="groq/llama-3.3-70b-versatile",
        BIFROST_FALLBACK_MODEL="openai/gpt-4o-mini",
        OPENAI_API_KEY="sk-proj-mock-openai-key-12345",
        GROQ_API_KEY="gsk_mock_groq_key_12345",
        ENVIRONMENT="test"
    )


@pytest.fixture
def mock_bifrost_completion_response():
    """Returns a realistic Bifrost HTTP response dict."""
    return {
        "id": "chatcmpl-bifrost-98765",
        "object": "chat.completion",
        "created": 1731940000,
        "model": "openai/gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Stripe is a leading financial infrastructure platform."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 12,
            "total_tokens": 54
        }
    }
