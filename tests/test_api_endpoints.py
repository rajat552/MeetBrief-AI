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
