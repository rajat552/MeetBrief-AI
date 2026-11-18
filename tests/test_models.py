"""
Unit Tests for Domain Models and Pydantic Schemas
"""

import pytest
from pydantic import ValidationError
from backend.models import (
    ManualMeetingRequest,
    ResearchFinding,
    VerifiedClaim,
    OnePageBriefing,
    CompanyProfile,
    AttendeeDossier
)


def test_manual_meeting_request_valid():
    req = ManualMeetingRequest(
        company_name="Stripe",
        attendee_name="Patrick Collison",
        attendee_role="CEO",
        meeting_datetime="2026-11-20 14:00 UTC",
        meeting_goal="Strategic Partnership"
    )
    assert req.company_name == "Stripe"
    assert req.attendee_name == "Patrick Collison"
    assert req.attendee_role == "CEO"


def test_manual_meeting_request_empty_fields():
    with pytest.raises(ValidationError):
        ManualMeetingRequest(
            company_name="   ",
            attendee_name="Patrick",
            meeting_datetime="2026-11-20"
        )

    with pytest.raises(ValidationError):
        ManualMeetingRequest(
            company_name="Stripe",
            attendee_name="",
            meeting_datetime="2026-11-20"
        )


def test_research_finding_schema():
    finding = ResearchFinding(
        category="news",
        title="Stripe Expands Agentic Payments",
        summary="Stripe launched an SDK for AI agent payments.",
        source_url="https://stripe.com/news/agentic",
        source_title="Stripe News",
        published_date="2026-11-12",
        freshness_days_ago=6,
        reliability_tier=1,
        matched_passage="Stripe today announced Agentic Payments SDK..."
    )
    assert finding.reliability_tier == 1
    assert finding.category == "news"


def test_verified_claim_status_constraint():
    claim = VerifiedClaim(
        claim="Stripe was founded in 2010.",
        verification_status="VERIFIED_PRIMARY",
        source_url="https://stripe.com/about",
        source_title="About Stripe",
        alignment_score=0.95,
        confidence_score=0.95
    )
    assert claim.verification_status == "VERIFIED_PRIMARY"

    with pytest.raises(ValidationError):
        VerifiedClaim(
            claim="Invalid status test",
            verification_status="INVALID_STATUS",  # type: ignore
            source_url="https://example.com",
            source_title="Example",
            alignment_score=0.5,
            confidence_score=0.5
        )
