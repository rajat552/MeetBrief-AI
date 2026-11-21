"""
Integration Tests for FastAPI Endpoints & Safe SSE Event Streaming
"""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from app import app


@pytest.mark.asyncio
async def test_api_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "MeetBrief AI"
        assert "gateway" in data
        assert "mode" in data["gateway"]


@pytest.mark.asyncio
async def test_api_calendar_fallback():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/briefings/calendar", json={"date": "2026-11-20"})
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        text = res.text
        assert "calendar_status" in text
        assert "unavailable" in text


@pytest.mark.asyncio
async def test_api_generate_briefing_sse_stream():
    payload = {
        "company_name": "Stripe",
        "attendee_name": "Patrick Collison",
        "attendee_role": "CEO",
        "meeting_datetime": "2026-11-20 14:00 UTC",
        "meeting_goal": "Strategic Discussion"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/briefings/generate", json=payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]

        body_text = res.text
        # Verify event frame markers
        assert "event: gateway_status" in body_text
        assert "event: stage_update" in body_text
        assert "event: streaming" in body_text
        assert "event: complete" in body_text

        # Verify strict privacy: zero agent_thought leaked
        assert "agent_thought" not in body_text
        assert "<thought>" not in body_text


@pytest.mark.asyncio
async def test_api_audio_briefing_endpoint():
    """Verifies POST /api/briefings/audio returns structured audio payload."""
    from backend.models import OnePageBriefing, CompanyProfile, AttendeeDossier

    briefing = OnePageBriefing(
        briefing_id="brief_test_audio_endpoint",
        target_company="Databricks",
        target_attendee="Ali Ghodsi",
        meeting_datetime="2026-11-20 16:00 UTC",
        meeting_goal="AI Partnership",
        card1_executive_snapshot="Databricks is expanding its Data Intelligence Platform.",
        card2_company_profile=CompanyProfile(
            company_name="Databricks",
            business_model="B2B Software",
            core_products=["Data Platform"],
            target_market="Enterprise",
            competitive_moat="Spark Ecosystem",
            key_competitors=["Snowflake"]
        ),
        card3_attendee_dossier=AttendeeDossier(
            name="Ali Ghodsi",
            verified_title="CEO",
            current_company="Databricks",
            career_history=["CEO"],
            public_stances_and_quotes=["Focused on AI scale."],
            likely_agenda="Platform viability",
            communication_hook="Shared focus on AI"
        ),
        card4_recent_30d_signals=[],
        card5_discussion_hooks=["Align on product roadmap."],
        card6_risk_blindspots=["Clarify adoption timeframe."],
        verified_claims=[],
        undated_signals=[],
        aggregate_confidence=0.90,
        inference_route="bifrost_gateway"
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/briefings/audio", json=briefing.model_dump())
        assert res.status_code == 200
        data = res.json()
        assert "spoken_script" in data
        assert "duration_estimated_seconds" in data
        assert data["provider"] in ("omnidimension", "browser_tts_fallback")
        assert "Databricks" in data["spoken_script"]
