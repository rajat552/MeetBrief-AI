"""
Unit Tests for Evidence Grounding Engine & Verification Heuristics
"""

import pytest
from backend.models import ResearchFinding
from backend.verifier import EvidenceGroundingEngine


def test_atomic_entity_extraction():
    text = "Stripe raised $50M Series B in 2024 and launched Agentic Payments on November 12."
    entities = EvidenceGroundingEngine.extract_atomic_entities(text)

    assert "$50m" in entities or "$50" in "".join(entities)
    assert "2024" in entities
    assert any("agentic" in e for e in entities)


def test_verify_claim_verified_primary():
    # Tier 1 source: stripe.com
    finding = ResearchFinding(
        category="launches",
        title="Agentic Payments Released",
        summary="Stripe officially launched Agentic Payments SDK for autonomous AI agents.",
        source_url="https://stripe.com/news/agentic-payments",
        source_title="Stripe News",
        published_date="2026-11-12",
        reliability_tier=1,
        matched_passage="Stripe officially launched Agentic Payments SDK for autonomous AI agents on November 12."
    )

    claim = "Stripe launched Agentic Payments SDK for AI agents."
    verified = EvidenceGroundingEngine.verify_claim(claim, [finding])

    assert verified.verification_status == "VERIFIED_PRIMARY"
    assert verified.confidence_score >= 0.70
    assert verified.alignment_score >= 0.70
    assert verified.source_url == "https://stripe.com/news/agentic-payments"


def test_verify_claim_reported_secondary():
    # Tier 2 source: techcrunch.com
    finding = ResearchFinding(
        category="news",
        title="Stripe Explores New Markets",
        summary="TechCrunch reports Stripe is expanding presence in Southeast Asia.",
        source_url="https://techcrunch.com/2026/stripe-asia",
        source_title="TechCrunch",
        published_date="2026-11-10",
        reliability_tier=2,
        matched_passage="TechCrunch reports Stripe is expanding presence in Southeast Asia."
    )

    claim = "Stripe is expanding in Southeast Asia."
    verified = EvidenceGroundingEngine.verify_claim(claim, [finding])

    assert verified.verification_status == "REPORTED_SECONDARY"
    assert verified.confidence_score > 0.40
    assert verified.source_url == "https://techcrunch.com/2026/stripe-asia"


def test_verify_claim_unverified_on_mismatch():
    finding = ResearchFinding(
        category="company_background",
        title="Unrelated Article",
        summary="Discusses general payment processing history in the 1990s.",
        source_url="https://blog.example.com/payments",
        source_title="Payments History",
        reliability_tier=3,
        matched_passage="Discusses general payment processing history in the 1990s."
    )

    claim = "Stripe launched Quantum Cloud Processor yesterday."
    verified = EvidenceGroundingEngine.verify_claim(claim, [finding])

    assert verified.verification_status == "UNVERIFIED"
    assert verified.confidence_score < 0.50


def test_verify_claim_conflicted():
    finding_launch = ResearchFinding(
        category="launches",
        title="Product Launch",
        summary="Company announces full public release of new product.",
        source_url="https://stripe.com/launch",
        source_title="Company Announcement",
        reliability_tier=1,
        matched_passage="Company announces full public release of new product."
    )
    finding_conflict = ResearchFinding(
        category="news",
        title="Regulatory Delay",
        summary="Regulators delayed and blocked the planned launch.",
        source_url="https://reuters.com/delay",
        source_title="Reuters News",
        reliability_tier=2,
        matched_passage="Regulators delayed and blocked the planned launch."
    )

    claim = "Company launched new product."
    verified = EvidenceGroundingEngine.verify_claim(claim, [finding_launch, finding_conflict])

    assert verified.verification_status == "CONFLICTED"
    assert verified.conflict_notes is not None
