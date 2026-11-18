"""
Unit Tests for Bifrost Gateway Client, Telemetry & Fallback Router
"""

import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from backend.config import Settings
from backend.gateway import BifrostClient, GatewayStatus, GatewayResponse, GatewayTelemetry


@pytest.mark.asyncio
async def test_gateway_health_online(mock_settings):
    """Verifies check_health when Bifrost Gateway is online and responds with 200."""
    client = BifrostClient(cfg=mock_settings)

    mock_res_health = MagicMock()
    mock_res_health.status_code = 200
    mock_res_health.headers = {"server": "bifrost/2.3.1"}

    mock_res_models = MagicMock()
    mock_res_models.status_code = 200
    mock_res_models.json.return_value = {
        "data": [{"id": "openai/gpt-4o"}, {"id": "groq/llama-3.3-70b-versatile"}]
    }

    with patch("httpx.AsyncClient.get", side_effect=[mock_res_health, mock_res_models]):
        status = await client.check_health(force_refresh=True)

        assert status.is_healthy is True
        assert status.mode == "bifrost_gateway"
        assert "openai/gpt-4o" in status.available_models
        assert "groq/llama-3.3-70b-versatile" in status.available_models


@pytest.mark.asyncio
async def test_gateway_health_detects_non_bifrost_server(mock_settings):
    """Verifies that non-Bifrost servers (e.g. Apache on 8080 returning 404) trigger fallback."""
    client = BifrostClient(cfg=mock_settings)

    mock_res = MagicMock()
    mock_res.status_code = 404
    mock_res.headers = {"server": "Apache/2.4.58"}

    with patch("httpx.AsyncClient.get", return_value=mock_res):
        status = await client.check_health(force_refresh=True)

        assert status.is_healthy is False
        assert status.mode == "fallback_direct"
        assert "Apache" in status.reason


@pytest.mark.asyncio
async def test_gateway_health_connection_error(mock_settings):
    """Verifies connection refusal triggers fallback without crashing."""
    client = BifrostClient(cfg=mock_settings)

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        status = await client.check_health(force_refresh=True)

        assert status.is_healthy is False
        assert status.mode == "fallback_direct"
        assert "Connection refused" in status.reason


@pytest.mark.asyncio
async def test_bifrost_completion_and_response_headers(mock_settings, mock_bifrost_completion_response):
    """Verifies full inference request parsing x-bifrost-* headers when extra_fields_placement='headers'."""
    client = BifrostClient(cfg=mock_settings)

    # Mock health check
    mock_res_health = MagicMock()
    mock_res_health.status_code = 200
    mock_res_health.headers = {"server": "bifrost/2.3.1"}

    # Mock Bifrost POST completion
    mock_res_post = MagicMock()
    mock_res_post.status_code = 200
    mock_res_post.json.return_value = mock_bifrost_completion_response
    mock_res_post.headers = {
        "x-bifrost-request-id": "req-bifrost-abc-123",
        "x-bifrost-latency-ms": "142.5",
        "x-bifrost-upstream-latency-ms": "138.2",
        "x-bifrost-cache-hit": "false",
        "x-bifrost-routing-info-provider": "openai",
        "x-bifrost-cost-usd": "0.00045"
    }

    with patch("httpx.AsyncClient.get", return_value=mock_res_health), \
         patch("httpx.AsyncClient.post", return_value=mock_res_post) as mock_post_call:

        response = await client.complete(
            messages=[{"role": "user", "content": "Tell me about Stripe"}],
            model="openai/gpt-4o"
        )

        assert response.content == "Stripe is a leading financial infrastructure platform."
        assert response.telemetry.mode == "bifrost_gateway"
        assert response.telemetry.request_id == "req-bifrost-abc-123"
        assert response.telemetry.latency_ms == 142.5
        assert response.telemetry.upstream_latency_ms == 138.2
        assert response.telemetry.cache_hit is False
        assert response.telemetry.provider == "openai"
        assert response.telemetry.cost_usd == 0.00045

        # Verify request headers
        call_kwargs = mock_post_call.call_args.kwargs
        headers = call_kwargs["headers"]
        assert headers["x-bf-vk"] == mock_settings.BIFROST_VIRTUAL_KEY
        assert headers["x-bf-dim-app"] == "meetbrief-ai"
        assert headers["Authorization"] == f"Bearer {mock_settings.BIFROST_VIRTUAL_KEY}"


@pytest.mark.asyncio
async def test_explicit_direct_provider_fallback_when_gateway_offline(mock_settings):
    """Verifies that when Bifrost is offline, client routes to direct provider and explicitly logs fallback."""
    client = BifrostClient(cfg=mock_settings)

    # Health check fails (Connection Refused)
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        # Mock direct OpenAI completion
        mock_direct_post = MagicMock()
        mock_direct_post.status_code = 200
        mock_direct_post.json.return_value = {
            "id": "chatcmpl-openai-direct-999",
            "choices": [{"message": {"content": "Direct OpenAI completion response."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

        with patch("httpx.AsyncClient.post", return_value=mock_direct_post) as mock_post_call:
            response = await client.complete(
                messages=[{"role": "user", "content": "Test prompt"}],
                model="openai/gpt-4o"
            )

            assert response.content == "Direct OpenAI completion response."
            # Mode MUST be explicitly labeled fallback_direct (never falsely claiming bifrost)
            assert response.telemetry.mode == "fallback_direct"
            assert response.telemetry.provider == "openai"
            assert response.telemetry.request_id == "chatcmpl-openai-direct-999"

            # Check that URL was direct OpenAI
            call_url = mock_post_call.call_args.args[0]
            assert "api.openai.com" in call_url


@pytest.mark.asyncio
async def test_explicit_direct_groq_fallback(mock_settings):
    """Verifies direct Groq fallback for Llama models when Bifrost is offline."""
    client = BifrostClient(cfg=mock_settings)

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Gateway offline")):
        mock_groq_post = MagicMock()
        mock_groq_post.status_code = 200
        mock_groq_post.json.return_value = {
            "id": "chatcmpl-groq-direct-888",
            "choices": [{"message": {"content": "Direct Groq Llama completion."}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 8}
        }

        with patch("httpx.AsyncClient.post", return_value=mock_groq_post) as mock_post_call:
            response = await client.complete(
                messages=[{"role": "user", "content": "Fast extraction"}],
                model="groq/llama-3.3-70b-versatile"
            )

            assert response.content == "Direct Groq Llama completion."
            assert response.telemetry.mode == "fallback_direct"
            assert response.telemetry.provider == "groq"
            call_url = mock_post_call.call_args.args[0]
            assert "api.groq.com" in call_url


@pytest.mark.asyncio
async def test_stream_emits_fallback_status_event_on_gateway_offline(mock_settings):
    """Verifies that streaming emits gateway_status fallback notice when Bifrost is offline."""
    client = BifrostClient(cfg=mock_settings)

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Bifrost down")):
        # Mock streaming context
        async def mock_aiter_text():
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"Streamed \"}}]}\n\n"
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"token.\"}}]}\n\n"
            yield "data: [DONE]\n\n"

        mock_stream_ctx = MagicMock()
        mock_stream_resp = MagicMock()
        mock_stream_resp.status_code = 200
        mock_stream_resp.aiter_text = mock_aiter_text
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_resp)
        mock_stream_ctx.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
            events = []
            async for ev in client.stream(messages=[{"role": "user", "content": "hello"}]):
                events.append(ev)

            # First event must be gateway_status explicitly alerting the fallback
            assert events[0]["type"] == "gateway_status"
            assert events[0]["data"]["mode"] == "fallback_direct"
            
            # Subsequent events are clean chunk tokens
            tokens = [e["content"] for e in events if e["type"] == "chunk"]
            assert "".join(tokens) == "Streamed token."

            # Final event is telemetry
            last = events[-1]
            assert last["type"] == "telemetry"
            assert last["data"]["mode"] == "fallback_direct"
