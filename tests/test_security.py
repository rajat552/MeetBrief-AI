"""
MeetBrief AI — Security & Privacy Assurance Tests
Verifies input sanitization, prompt injection handling, SSE privacy (no agent_thought),
virtual key masking, and date boundary enforcement.
"""

import pytest
import re
from pydantic import ValidationError
from backend.models import ManualMeetingRequest, SSEEventPayload
from backend.gateway import BifrostClient
from backend.agent import MeetBriefOrchestrator
from backend.research.planner import SharedQueryPlanner


class TestSecurityAndInputSanitization:
    def test_clean_input_accepted(self):
        req = ManualMeetingRequest(
            company_name="Stripe",
            attendee_name="Patrick Collison",
            meeting_datetime="2026-11-20 14:00 UTC",
            meeting_goal="Explore agentic commerce partnership",
        )
        assert req.company_name == "Stripe"
        assert req.attendee_name == "Patrick Collison"

    def test_empty_or_whitespace_only_rejected(self):
        with pytest.raises(ValidationError):
            ManualMeetingRequest(
                company_name="   ",
                attendee_name="Patrick",
                meeting_datetime="2026-11-20 14:00 UTC",
            )

    def test_strip_html_script_tags(self):
        req = ManualMeetingRequest(
            company_name="<script>alert('pwned')</script>Acme Corp",
            attendee_name="Jane Doe <img src=x onerror=alert(1)>",
            meeting_datetime="2026-11-20 14:00 UTC",
            meeting_goal="<iframe src='malicious.com'></iframe>Partnership",
        )
        # HTML tags and inner script content should be stripped from entity names
        assert "<script>" not in req.company_name
        assert "alert(" not in req.company_name
        assert req.company_name == "Acme Corp"
        assert "<img" not in req.attendee_name
        assert "<iframe" not in (req.meeting_goal or "")
        assert "Partnership" in (req.meeting_goal or "")

    def test_control_character_sanitization(self):
        req = ManualMeetingRequest(
            company_name="Stripe\x00\x08Corp",
            attendee_name="Patrick\r\nCollison",
            meeting_datetime="2026-11-20 14:00 UTC",
        )
        assert "\x00" not in req.company_name
        assert "\x08" not in req.company_name


class TestPrivacyAndZeroThoughtLeakage:
    def test_sse_event_payload_schema_rejects_agent_thought(self):
        """SSEEventPayload schema strictly disallows agent_thought as an event type."""
        with pytest.raises(ValidationError):
            SSEEventPayload(
                event_type="agent_thought",  # type: ignore
                data={"thought": "Planning to search Stripe..."}
            )

    def test_allowed_event_types_only(self):
        allowed = [
            "stage_update",
            "tool_status",
            "source_discovered",
            "claims_verified",
            "streaming",
            "gateway_status",
            "complete",
            "error",
        ]
        for event in allowed:
            payload = SSEEventPayload(event_type=event, data={"test": True})
            assert payload.event_type == event

    @pytest.mark.asyncio
    async def test_orchestrator_stream_emits_no_private_thoughts(self):
        """Verifies full orchestrator SSE stream contains ZERO agent_thought or private reasoning tokens."""
        orchestrator = MeetBriefOrchestrator()
        req = ManualMeetingRequest(
            company_name="Stripe",
            attendee_name="Patrick Collison",
            meeting_datetime="2026-11-20 14:00 UTC",
        )

        emitted_events = []
        async for sse_chunk in orchestrator.execute_stream(req):
            emitted_events.append(sse_chunk)
            assert "agent_thought" not in sse_chunk.lower()
            assert "private_thinking" not in sse_chunk.lower()
            assert "chain_of_thought" not in sse_chunk.lower()

        assert len(emitted_events) > 0


class TestVirtualKeyMasking:
    def test_bifrost_client_repr_masks_virtual_key(self):
        client = BifrostClient()
        client.virtual_key = "sk-bf-sensitive-secret-token-123456"
        rep = repr(client)
        assert "sk-bf-sensitive-secret-token-123456" not in rep
        assert "sk-bf-..." in rep or "***" in rep or "active" in rep

    def test_error_formatting_does_not_leak_key(self):
        client = BifrostClient()
        client.virtual_key = "sk-bf-super-secret"
        err_msg = str(client)
        assert "sk-bf-super-secret" not in err_msg


class TestTemporalBoundaryEnforcement:
    def test_future_meeting_clamped_to_current(self):
        req = ManualMeetingRequest(
            company_name="Stripe",
            attendee_name="Patrick Collison",
            meeting_datetime="2030-12-31 23:59 UTC",
        )
        plan = SharedQueryPlanner.build_plan(req)
        # Effective upper bound should be clamped to current time, NOT 2030
        assert not plan.end_date_str.startswith("2030")

    def test_invalid_date_graceful_fallback(self):
        plan = SharedQueryPlanner.calculate_bounds("invalid-gibberish-date")
        # Should fallback to current time minus 30 days safely
        assert plan.start_date_str is not None
        assert plan.end_date_str is not None
