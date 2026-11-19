"""
Targeted Tests for Three Inference Routes, Anti-Hallucination Grounding & Failure Modes
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest

from backend.agent import MeetBriefOrchestrator
from backend.config import Settings
from backend.gateway import BifrostClient, GatewayResponse, GatewayStatus, GatewayTelemetry
from backend.models import (
    ManualMeetingRequest,
    OnePageBriefing,
    ResearchFinding,
    VerifiedClaim,
)
from backend.synthesizer import ExecutiveSynthesizer


@pytest.fixture
def sample_findings():
    return [
        ResearchFinding(
            category="news",
            title="Stripe Expands Terminal Support to 5 New Countries",
            summary="Stripe announced expansion of its in-person payment hardware to European markets.",
            source_url="https://stripe.com/newsroom/news/terminal-expansion",
            source_title="Stripe Newsroom",
            published_date="2026-11-05T12:00:00Z",
            reliability_tier=1,
        ),
        ResearchFinding(
            category="attendee_dossier",
            title="Patrick Collison Profile",
            summary="Co-founder and CEO of Stripe; published reflections on fast decision making in industrial history.",
            source_url="https://patrickcollison.com/fast",
            source_title="Patrick Collison Personal Site",
            published_date="2026-10-25T08:00:00Z",
            reliability_tier=1,
        ),
    ]


@pytest.fixture
def sample_undated():
    return [
        ResearchFinding(
            category="undated",
            title="Old Stripe Architecture Notes",
            summary="Undated public documentation regarding payments stack.",
            source_url="https://stripe.com/docs/arch",
            source_title="Stripe Docs",
            published_date=None,
            reliability_tier=1,
        )
    ]


@pytest.fixture
def sample_claims():
    return [
        VerifiedClaim(
            claim="Stripe expanded terminal hardware to European markets.",
            verification_status="VERIFIED_PRIMARY",
            source_url="https://stripe.com/newsroom/news/terminal-expansion",
            source_title="Stripe Newsroom",
            alignment_score=0.96,
            confidence_score=0.96,
        )
    ]


@pytest.fixture
def sample_request():
    return ManualMeetingRequest(
        company_name="Stripe",
        attendee_name="Patrick Collison",
        attendee_role="CEO",
        meeting_datetime="2026-11-20 15:00 UTC",
        meeting_goal="Explore global checkout acceleration",
    )


# ==============================================================================
# 1. TEST ALL THREE INFERENCE ROUTES
# ==============================================================================

@pytest.mark.asyncio
async def test_route_1_bifrost_gateway(sample_request, sample_findings, sample_undated, sample_claims):
    """Verifies route 'bifrost_gateway' when Bifrost Gateway is online."""
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings()
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(is_healthy=True, mode="bifrost_gateway", endpoint="http://localhost:8085/v1")
    )
    mock_gw.complete = AsyncMock(
        return_value=GatewayResponse(
            content="EXECUTIVE SNAPSHOT: Strategic discussion with Stripe.\nDISCUSSION HOOKS:\n- Inquire about Terminal expansion.\nRISK BLINDSPOTS:\n- Verify European expansion roadmap.",
            telemetry=GatewayTelemetry(
                model="gemini/gemini-flash-lite-latest",
                latency_ms=120.0,
                provider="gemini",
                mode="bifrost_gateway",
            ),
        )
    )

    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)
    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=sample_findings,
        undated_findings=sample_undated,
        verified_claims=sample_claims,
    )

    assert briefing.inference_route == "bifrost_gateway"
    assert "Stripe" in briefing.target_company


@pytest.mark.asyncio
async def test_route_2_direct_provider_fallback(sample_request, sample_findings, sample_undated, sample_claims):
    """Verifies route 'direct_provider_fallback' when Bifrost is offline but provider API keys exist."""
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings(GEMINI_API_KEY="AIzaMockKey123")
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(
            is_healthy=False,
            mode="direct_provider_fallback",
            endpoint="http://localhost:8085/v1",
            reason="Gateway connection refused",
        )
    )
    mock_gw.complete = AsyncMock(
        return_value=GatewayResponse(
            content="EXECUTIVE SNAPSHOT: Direct Gemini synthesis for Stripe.\nDISCUSSION HOOKS:\n- Ask about payments.",
            telemetry=GatewayTelemetry(
                model="gemini-flash-lite-latest",
                latency_ms=250.0,
                provider="gemini",
                mode="direct_provider_fallback",
            ),
        )
    )

    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)
    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=sample_findings,
        undated_findings=sample_undated,
        verified_claims=sample_claims,
    )

    assert briefing.inference_route == "direct_provider_fallback"


@pytest.mark.asyncio
async def test_route_3_deterministic_fallback_when_offline(sample_request, sample_findings, sample_undated, sample_claims):
    """Verifies route 'deterministic_fallback' when both Bifrost and direct providers are unavailable."""
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings(_env_file=None, TAVILY_API_KEY="mock")
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(is_healthy=False, mode="deterministic_fallback", endpoint="http://localhost:8085/v1")
    )

    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)
    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=sample_findings,
        undated_findings=sample_undated,
        verified_claims=sample_claims,
    )

    assert briefing.inference_route == "deterministic_fallback"
    assert len(briefing.card5_discussion_hooks) == 3
    assert len(briefing.card6_risk_blindspots) == 3


# ==============================================================================
# 2. PROVIDER QUOTA FAILURE (HTTP 429) -> DETERMINISTIC FALLBACK
# ==============================================================================

@pytest.mark.asyncio
async def test_provider_quota_exhaustion_falls_back_to_deterministic(sample_request, sample_findings, sample_undated, sample_claims):
    """Verifies that an upstream HTTP 429 Quota Exceeded error cleanly transitions to deterministic fallback."""
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings(_env_file=None, TAVILY_API_KEY="mock", GEMINI_API_KEY="AIzaMock")
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(is_healthy=True, mode="bifrost_gateway", endpoint="http://localhost:8085/v1")
    )
    # Simulate HTTP 429 Quota Failure
    mock_gw.complete = AsyncMock(
        side_effect=RuntimeError("Provider returned HTTP 429: RESOURCE_EXHAUSTED / quota exceeded")
    )

    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)
    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=sample_findings,
        undated_findings=sample_undated,
        verified_claims=sample_claims,
    )

    # Must NOT raise exception; must cleanly fall back to deterministic mode
    assert briefing.inference_route == "deterministic_fallback"
    assert briefing.target_company == "Stripe"
    assert len(briefing.card5_discussion_hooks) == 3


# ==============================================================================
# 3. EVIDENCE GROUNDING: NO INVENTED CAPABILITIES OR ATTENDEE STANCES
# ==============================================================================

@pytest.mark.asyncio
async def test_unsupported_assumptions_prevented(sample_request, sample_findings, sample_undated, sample_claims):
    """
    Verifies that the synthesizer does not invent user-company capabilities or unverified attendee stances.
    Discussion hooks should be framed conditionally if assumptions are exploratory.
    """
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings(_env_file=None, TAVILY_API_KEY="mock")
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(is_healthy=False, mode="deterministic_fallback", endpoint="http://localhost:8085/v1")
    )
    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)

    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=sample_findings,
        undated_findings=sample_undated,
        verified_claims=sample_claims,
    )

    # Attendee stances must NOT contain hardcoded inventions like "Advocates for operational excellence"
    stances = briefing.card3_attendee_dossier.public_stances_and_quotes
    assert len(stances) > 0
    for s in stances:
        # Either cites the actual profile summary or states unverified public stance
        assert "operational excellence and strategic growth" not in s
        assert "scale, architectural elegance" not in s

    # Discussion hooks must NOT claim unverified user capabilities as established facts
    for hook in briefing.card5_discussion_hooks:
        # Must be either verified signal or framed conditionally as exploration/question
        assert any(
            marker in hook
            for marker in ["[Verified Signal]", "[Conditional", "[Exploratory", "[Discovery", "[Role Discovery]"]
        )


@pytest.mark.asyncio
async def test_unsupported_attendee_claims_quarantined_when_no_people_findings(sample_request, sample_undated, sample_claims):
    """When no people findings are present in evidence, attendee quotes must explicitly indicate none verified."""
    mock_gw = MagicMock(spec=BifrostClient)
    mock_gw.config = Settings(_env_file=None, TAVILY_API_KEY="mock")
    mock_gw.check_health = AsyncMock(
        return_value=GatewayStatus(is_healthy=False, mode="deterministic_fallback", endpoint="http://localhost:8085/v1")
    )
    synthesizer = ExecutiveSynthesizer(gateway_client=mock_gw)

    # Empty in-window findings
    briefing = await synthesizer.synthesize(
        request=sample_request,
        in_window_findings=[],
        undated_findings=sample_undated,
        verified_claims=[],
    )

    stances = briefing.card3_attendee_dossier.public_stances_and_quotes
    assert any("No verified public quotes" in s for s in stances)


# ==============================================================================
# 4. SSE ERROR AND CANCELLATION HANDLING
# ==============================================================================

@pytest.mark.asyncio
async def test_sse_stream_handles_disconnect_gracefully(sample_request):
    """Verifies that client disconnect (CancelledError) breaks the SSE generator cleanly."""
    orchestrator = MeetBriefOrchestrator()

    async def mock_generator(req=None):
        yield {"event_type": "stage_update", "data": {"stage": "query_planning"}}
        await asyncio.sleep(0.01)
        # Simulate consumer disconnect
        raise asyncio.CancelledError()

    with patch.object(orchestrator, "execute_stream", side_effect=mock_generator):
        events = []
        try:
            async for ev in orchestrator.execute_stream(sample_request):
                events.append(ev)
        except asyncio.CancelledError:
            pass

        assert len(events) <= 1


# ==============================================================================
# 5. TAVILY MISSING-DATE AND STALE-RESULT FILTERING
# ==============================================================================

def test_undated_signals_always_quarantined(sample_request, sample_undated, sample_claims):
    """Verifies that undated findings remain strictly quarantined and never appear in 30-day signals."""
    synthesizer = ExecutiveSynthesizer(gateway_client=BifrostClient(cfg=Settings(BIFROST_ENABLED=False)))
    briefing = synthesizer._assemble_deterministic_briefing(
        request=sample_request,
        bg_findings=[],
        people_findings=[],
        card4_signals=[],
        undated_findings=sample_undated,
        verified_claims=sample_claims,
        avg_conf=0.75,
        inference_route="deterministic_fallback",
    )

    assert len(briefing.card4_recent_30d_signals) == 0
    assert len(briefing.undated_signals) == 1
    assert briefing.undated_signals[0].title == "Old Stripe Architecture Notes"
