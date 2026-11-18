"""
MeetBrief AI — Bifrost AI Gateway Client & Fallback Router
"""

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional
import httpx
from pydantic import BaseModel, Field

from backend.config import Settings, settings

logger = logging.getLogger(__name__)


class GatewayTelemetry(BaseModel):
    """Telemetry metadata captured from Bifrost response headers and execution."""
    request_id: Optional[str] = None
    latency_ms: Optional[float] = None
    upstream_latency_ms: Optional[float] = None
    cache_hit: bool = False
    provider: Optional[str] = None
    model: str
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    cost_usd: Optional[float] = None
    mode: Literal["bifrost_gateway", "fallback_direct"]


class GatewayResponse(BaseModel):
    """Unified response object returned by BifrostClient."""
    content: str
    telemetry: GatewayTelemetry
    raw_response: Optional[Dict[str, Any]] = None


class GatewayStatus(BaseModel):
    """Health and routing status of the AI Gateway."""
    is_healthy: bool
    mode: Literal["bifrost_gateway", "fallback_direct"]
    endpoint: str
    reason: Optional[str] = None
    available_models: List[str] = Field(default_factory=list)


class BifrostClient:
    """
    Client for interacting with Maxim AI's Bifrost AI Gateway.
    - Routes requests via OpenAI-compatible endpoint: http://localhost:8080/v1
    - Passes Virtual Key in headers: x-bf-vk: sk-bf-*
    - Tags custom dimension: x-bf-dim-app: meetbrief-ai
    - Extracts telemetry response headers: x-bifrost-request-id, x-bifrost-latency-ms, etc.
    - Transparently falls back to direct provider SDKs (OpenAI / Groq) if Bifrost is offline.
    """

    def __init__(self, cfg: Optional[Settings] = None):
        self.config = cfg or settings
        self._cached_status: Optional[GatewayStatus] = None
        self._status_checked_at: float = 0.0
        self._health_cache_ttl_seconds: float = 10.0

    @property
    def virtual_key(self) -> str:
        return self.config.BIFROST_VIRTUAL_KEY

    @virtual_key.setter
    def virtual_key(self, val: str) -> None:
        self.config.BIFROST_VIRTUAL_KEY = val

    def __repr__(self) -> str:
        masked_vk = f"{self.virtual_key[:6]}..." if self.virtual_key else "none"
        return f"<BifrostClient endpoint='{self.config.BIFROST_BASE_URL}' vk='{masked_vk}'>"

    def __str__(self) -> str:
        return self.__repr__()

    async def check_health(self, force_refresh: bool = False) -> GatewayStatus:
        """
        Queries Bifrost Gateway to verify connectivity and validate that the port
        is indeed running Bifrost (not another HTTP server).
        """
        now = time.time()
        if not force_refresh and self._cached_status and (now - self._status_checked_at < self._health_cache_ttl_seconds):
            return self._cached_status

        if not self.config.BIFROST_ENABLED:
            status = GatewayStatus(
                is_healthy=False,
                mode="fallback_direct",
                endpoint=self.config.BIFROST_BASE_URL,
                reason="Bifrost explicitly disabled in configuration (BIFROST_ENABLED=false)"
            )
            self._cached_status = status
            self._status_checked_at = now
            return status

        # Derive health endpoint: e.g. http://localhost:8080/health
        base = self.config.BIFROST_BASE_URL
        if base.endswith("/v1"):
            health_url = base[:-3] + "/health"
            models_url = base + "/models"
        else:
            health_url = base + "/health"
            models_url = base + "/v1/models"

        headers = {
            "x-bf-dim-app": "meetbrief-ai"
        }
        if self.config.BIFROST_VIRTUAL_KEY:
            headers["x-bf-vk"] = self.config.BIFROST_VIRTUAL_KEY
            headers["Authorization"] = f"Bearer {self.config.BIFROST_VIRTUAL_KEY}"

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(health_url, headers=headers)
                
                # Check for genuine Bifrost signature
                # Bifrost health returns 200 and often JSON or text 'OK'
                server_header = res.headers.get("server", "").lower()
                if "apache" in server_header or "nginx" in server_header and res.status_code == 404:
                    status = GatewayStatus(
                        is_healthy=False,
                        mode="fallback_direct",
                        endpoint=health_url,
                        reason=f"Port 8080 occupied by non-Bifrost server ({res.headers.get('server')})"
                    )
                    self._cached_status = status
                    self._status_checked_at = now
                    return status

                if res.status_code == 200:
                    # Query /models to verify model availability
                    available_models = []
                    try:
                        m_res = await client.get(models_url, headers=headers)
                        if m_res.status_code == 200:
                            m_data = m_res.json()
                            if isinstance(m_data, dict) and "data" in m_data:
                                available_models = [m.get("id") for m in m_data["data"] if isinstance(m, dict)]
                    except Exception:
                        pass

                    status = GatewayStatus(
                        is_healthy=True,
                        mode="bifrost_gateway",
                        endpoint=self.config.BIFROST_BASE_URL,
                        reason="Bifrost AI Gateway active and responding",
                        available_models=available_models
                    )
                else:
                    status = GatewayStatus(
                        is_healthy=False,
                        mode="fallback_direct",
                        endpoint=health_url,
                        reason=f"Bifrost Gateway returned status HTTP {res.status_code}"
                    )
        except httpx.ConnectError:
            status = GatewayStatus(
                is_healthy=False,
                mode="fallback_direct",
                endpoint=self.config.BIFROST_BASE_URL,
                reason="Cannot connect to Bifrost Gateway at port 8080 (Connection refused)"
            )
        except Exception as e:
            status = GatewayStatus(
                is_healthy=False,
                mode="fallback_direct",
                endpoint=self.config.BIFROST_BASE_URL,
                reason=f"Bifrost health check error: {str(e)}"
            )

        self._cached_status = status
        self._status_checked_at = now
        return status

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> GatewayResponse:
        """
        Executes a completion request.
        Tries Bifrost first; if unavailable, falls back to direct provider SDK.
        """
        target_model = model or self.config.BIFROST_PRIMARY_MODEL
        gateway_status = await self.check_health()

        if gateway_status.is_healthy:
            try:
                return await self._call_bifrost(
                    messages=messages,
                    model=target_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
            except Exception as e:
                logger.warning(f"Bifrost inference call failed: {e}. Initiating direct provider fallback.")
                return await self._call_direct_fallback(
                    messages=messages,
                    model=target_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    fallback_reason=f"Bifrost error: {str(e)}"
                )
        else:
            return await self._call_direct_fallback(
                messages=messages,
                model=target_model,
                temperature=temperature,
                max_tokens=max_tokens,
                fallback_reason=gateway_status.reason or "Bifrost Gateway offline"
            )

    async def _call_bifrost(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, Any]] = None
    ) -> GatewayResponse:
        """Executes completion directly against Bifrost Gateway."""
        endpoint = f"{self.config.BIFROST_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "x-bf-dim-app": "meetbrief-ai"
        }
        if self.config.BIFROST_VIRTUAL_KEY:
            headers["x-bf-vk"] = self.config.BIFROST_VIRTUAL_KEY
            headers["Authorization"] = f"Bearer {self.config.BIFROST_VIRTUAL_KEY}"

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(endpoint, headers=headers, json=payload)
            latency_ms = (time.perf_counter() - start_time) * 1000

            if res.status_code != 200:
                raise RuntimeError(f"Bifrost returned HTTP {res.status_code}: {res.text}")

            data = res.json()
            content = data["choices"][0]["message"]["content"] or ""

            # Extract headers populated via extra_fields_placement: "headers"
            req_id = res.headers.get("x-bifrost-request-id")
            gw_latency = res.headers.get("x-bifrost-latency-ms")
            up_latency = res.headers.get("x-bifrost-upstream-latency-ms")
            cache_hit_str = res.headers.get("x-bifrost-cache-hit", "false").lower()
            provider = res.headers.get("x-bifrost-routing-info-provider")
            cost_str = res.headers.get("x-bifrost-cost-usd")

            usage = data.get("usage", {})

            telemetry = GatewayTelemetry(
                request_id=req_id or data.get("id"),
                latency_ms=float(gw_latency) if gw_latency else round(latency_ms, 2),
                upstream_latency_ms=float(up_latency) if up_latency else None,
                cache_hit=(cache_hit_str == "true"),
                provider=provider or (model.split("/")[0] if "/" in model else "openai"),
                model=model,
                tokens_prompt=usage.get("prompt_tokens"),
                tokens_completion=usage.get("completion_tokens"),
                cost_usd=float(cost_str) if cost_str else None,
                mode="bifrost_gateway"
            )

            return GatewayResponse(content=content, telemetry=telemetry, raw_response=data)

    async def _call_direct_fallback(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        fallback_reason: str
    ) -> GatewayResponse:
        """
        Executes completion directly against provider SDK/API.
        Explicitly records mode='fallback_direct'.
        """
        clean_model = model.split("/")[-1] if "/" in model else model
        is_groq = "llama" in clean_model.lower() or "mixtral" in clean_model.lower()
        
        start_time = time.perf_counter()

        if is_groq and self.config.is_groq_configured():
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            actual_model = clean_model
            provider_name = "groq"
        elif self.config.is_openai_configured():
            endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            actual_model = clean_model if not is_groq else "gpt-4o-mini"
            provider_name = "openai"
        elif self.config.is_gemini_configured():
            endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            actual_model = "gemini-flash-latest"
            provider_name = "gemini"
        else:
            # Deterministic offline mock fallback if no direct keys are set
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return GatewayResponse(
                content=f"[FALLBACK DIRECT MODE: {fallback_reason}] Direct provider keys not configured.",
                telemetry=GatewayTelemetry(
                    request_id="mock_fallback_req",
                    latency_ms=round(elapsed_ms, 2),
                    upstream_latency_ms=None,
                    cache_hit=False,
                    provider="direct_unconfigured",
                    model=model,
                    tokens_prompt=0,
                    tokens_completion=0,
                    cost_usd=0.0,
                    mode="fallback_direct"
                ),
                raw_response={"mock": True, "fallback_reason": fallback_reason}
            )

        payload = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(endpoint, headers=headers, json=payload)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if res.status_code != 200:
                raise RuntimeError(f"Direct provider ({provider_name}) returned HTTP {res.status_code}: {res.text}")

            data = res.json()
            content = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})

            telemetry = GatewayTelemetry(
                request_id=data.get("id"),
                latency_ms=round(elapsed_ms, 2),
                upstream_latency_ms=None,
                cache_hit=False,
                provider=provider_name,
                model=actual_model,
                tokens_prompt=usage.get("prompt_tokens"),
                tokens_completion=usage.get("completion_tokens"),
                cost_usd=None,
                mode="fallback_direct"
            )

            return GatewayResponse(content=content, telemetry=telemetry, raw_response=data)

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams completion tokens safely.
        Emits clean chunks: {"type": "chunk", "content": text}
        Emits final telemetry: {"type": "telemetry", "data": GatewayTelemetry}
        """
        target_model = model or self.config.BIFROST_PRIMARY_MODEL
        gateway_status = await self.check_health()

        if gateway_status.is_healthy:
            endpoint = f"{self.config.BIFROST_BASE_URL}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "x-bf-dim-app": "meetbrief-ai"
            }
            if self.config.BIFROST_VIRTUAL_KEY:
                headers["x-bf-vk"] = self.config.BIFROST_VIRTUAL_KEY
                headers["Authorization"] = f"Bearer {self.config.BIFROST_VIRTUAL_KEY}"
            mode_label = "bifrost_gateway"
        else:
            yield {
                "type": "gateway_status",
                "data": {
                    "mode": "fallback_direct",
                    "reason": gateway_status.reason or "Bifrost Gateway offline"
                }
            }
            # Route to direct provider stream
            clean_model = target_model.split("/")[-1] if "/" in target_model else target_model
            if self.config.is_gemini_configured():
                endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.config.GEMINI_API_KEY}",
                    "Content-Type": "application/json"
                }
                clean_model = "gemini-flash-latest"
            elif self.config.is_groq_configured() and ("llama" in clean_model.lower() or "mixtral" in clean_model.lower()):
                endpoint = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            else:
                endpoint = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
            mode_label = "fallback_direct"

        payload = {
            "model": clean_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield {"type": "error", "content": f"HTTP {response.status_code}: {err_body.decode()}"}
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data_str)
                            delta = parsed.get("choices", [{}])[0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                yield {"type": "chunk", "content": token}
                        except Exception:
                            continue

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        yield {
            "type": "telemetry",
            "data": {
                "mode": mode_label,
                "model": target_model,
                "latency_ms": round(elapsed_ms, 2)
            }
        }
