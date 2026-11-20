"""
Unit Tests for Omnidimension Voice AI & Audio Briefing Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.config import Settings
from backend.models import (
    AttendeeDossier,
    CompanyProfile,
    OnePageBriefing,
    ResearchFinding,
    VerifiedClaim,
)
from backend.voice import AudioBriefingService


@pytest.fixture
def sample_briefing():
    return OnePageBriefing(
        briefing_id="brief_voice_test_123",
        target_company="Stripe",
        target_attendee="Patrick Collison",
        meeting_datetime="2026-11-20 15:00 UTC",
        meeting_goal="Explore global checkout partnership",
        card1_executive_snapshot="Stripe is accelerating enterprise market penetration and global terminal rollouts.",
        card2_company_profile=CompanyProfile(
            company_name="Stripe",
            business_model="B2B Financial Infrastructure",
            core_products=["Payments", "Billing", "Terminal"],
            target_market="Global Enterprises & Startups",
            competitive_moat="Developer APIs and scale",
            key_competitors=["Adyen", "PayPal"]
        ),
        card3_attendee_dossier=AttendeeDossier(
            name="Patrick Collison",
            verified_title="CEO",
            current_company="Stripe",
            career_history=["Co-founder & CEO of Stripe"],
            public_stances_and_quotes=["Focuses on industrial execution and engineering velocity."],
            likely_agenda="Explore partnership feasibility",
            communication_hook="Reference shared focus on infrastructure reliability"
        ),
        card4_recent_30d_signals=[
            ResearchFinding(
                category="news",
                title="Stripe Expands Terminal to 5 New Markets",
                summary="Stripe announces in-person payment hardware expansion in Europe.",
                source_url="https://stripe.com/news/terminal",
                source_title="Stripe News",
                published_date="2026-11-10",
                reliability_tier=1
            )
        ],
        card5_discussion_hooks=[
            "[Verified Signal] Congratulate on recent Terminal rollout across European markets.",
            "[Conditional Suggestion] Explore potential alignment between our platform and their checkout flow.",
            "[Role Discovery] Inquire about their upcoming architectural priorities for Q1."
        ],
        card6_risk_blindspots=[
            "? Authority Check: Verify if Patrick requires committee consensus for partnership approval.",
            "? Bandwidth: Confirm internal engineering capacity for Q1 integrations."
        ],
        verified_claims=[
            VerifiedClaim(
                claim="Stripe expanded terminal hardware.",
                verification_status="VERIFIED_PRIMARY",
                source_url="https://stripe.com/news/terminal",
                source_title="Stripe News",
                alignment_score=0.95,
                confidence_score=0.95
            )
        ],
        undated_signals=[],
        aggregate_confidence=0.95,
        inference_route="bifrost_gateway"
    )


def test_clean_text_for_speech():
    service = AudioBriefingService()
    dirty_text = "Check [Stripe News](https://stripe.com) **important** update: [Verified Signal] Great! *Scale* & more."
    cleaned = service.clean_text_for_speech(dirty_text)

    assert "https://" not in cleaned
    assert "[Verified Signal]" not in cleaned
    assert "**" not in cleaned
    assert "*" not in cleaned
    assert "Stripe News important update: Great! Scale & more." in cleaned


def test_spoken_script_generation_brevity_and_flow(sample_briefing):
    service = AudioBriefingService()
    script = service.build_spoken_script(sample_briefing)

    # 1. Must include key executive identifiers
    assert "Patrick Collison" in script
    assert "Stripe" in script
    assert "Explore global checkout partnership" in script

    # 2. Must omit raw URLs or uncleaned brackets
    assert "http" not in script
    assert "[" not in script
    assert "]" not in script

    # 3. Brevity check: Spoken scripts for a 90s brief must be strictly under 300 words
    word_count = len(script.split())
    assert 50 <= word_count <= 300, f"Word count was {word_count}, expected between 50 and 300 words"


@pytest.mark.asyncio
async def test_generate_audio_fallback_when_unconfigured(sample_briefing):
    """When Omnidimension API key is missing, service returns browser speech fallback."""
    cfg = Settings(_env_file=None, TAVILY_API_KEY="mock", OMNIDIMENSION_API_KEY="")
    service = AudioBriefingService(cfg=cfg)

    response = await service.generate_audio(sample_briefing)

    assert response.provider == "browser_tts_fallback"
    assert response.duration_estimated_seconds >= 30
    assert len(response.spoken_script) > 50
    assert response.audio_base64 is None
    assert response.audio_url is None


@pytest.mark.asyncio
async def test_generate_audio_omnidimension_success_mp3_stream(sample_briefing):
    """When Omnidimension API returns raw MP3 binary, response includes base64 data URI."""
    cfg = Settings(_env_file=None, TAVILY_API_KEY="mock", OMNIDIMENSION_API_KEY="omni_test_key_123")
    service = AudioBriefingService(cfg=cfg)

    mock_http_resp = MagicMock()
    mock_http_resp.status_code = 200
    mock_http_resp.headers = {"content-type": "audio/mpeg"}
    mock_http_resp.content = b"fake-mp3-binary-payload-data"

    with patch("httpx.AsyncClient.post", return_value=mock_http_resp) as mock_post:
        response = await service.generate_audio(sample_briefing)

        assert response.provider == "omnidimension"
        assert response.audio_base64 is not None
        assert response.audio_base64.startswith("data:audio/mp3;base64,")
        assert response.duration_estimated_seconds >= 30

        # Verify request headers
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer omni_test_key_123"


@pytest.mark.asyncio
async def test_generate_audio_omnidimension_api_failure_cascades_to_fallback(sample_briefing):
    """When Omnidimension API fails with HTTP 500 or network error, falls back cleanly to browser TTS."""
    cfg = Settings(_env_file=None, TAVILY_API_KEY="mock", OMNIDIMENSION_API_KEY="omni_test_key_123")
    service = AudioBriefingService(cfg=cfg)

    mock_http_resp = MagicMock()
    mock_http_resp.status_code = 500
    mock_http_resp.text = "Internal Server Error in Omnidimension cluster"

    with patch("httpx.AsyncClient.post", return_value=mock_http_resp):
        response = await service.generate_audio(sample_briefing)

        # Must not crash; must cleanly return browser_tts_fallback
        assert response.provider == "browser_tts_fallback"
        assert len(response.spoken_script) > 50
