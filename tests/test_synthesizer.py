"""
Unit Tests for Executive Synthesizer & One-Page Brevity Enforcement
"""

import pytest
from backend.models import ManualMeetingRequest, ResearchFinding, VerifiedClaim
from backend.synthesizer import ExecutiveSynthesizer


@pytest.mark.asyncio
async def test_synthesizer_structure_and_brevity():
    synthesizer = ExecutiveSynthesizer()

    req = ManualMeetingRequest(
        company_name="Databricks",
        attendee_name="Ali Ghodsi",
        attendee_role="CEO",
        meeting_datetime="2026-11-20 14:00 UTC",
        meeting_goal="Strategic AI Partnership"
    )

    findings = [
        ResearchFinding(
            category="company_background",
            title="Databricks Overview",
            summary="Databricks operates the Data Intelligence Platform built on Apache Spark.",
            source_url="https://databricks.com/about",
            source_title="About Databricks",
            reliability_tier=1
        ),
        ResearchFinding(
            category="news",
            title="Databricks Announces AI Innovations",
            summary="New platform features announced for generative AI workloads.",
            source_url="https://databricks.com/news/ai",
            source_title="Databricks News",
            published_date="2026-11-05",
            reliability_tier=1
        )
    ]

    claims = [
        VerifiedClaim(
            claim="Databricks operates the Data Intelligence Platform.",
            verification_status="VERIFIED_PRIMARY",
            source_url="https://databricks.com/about",
            source_title="About Databricks",
            alignment_score=0.95,
            confidence_score=0.95
        )
    ]

    undated = [
        ResearchFinding(
            category="undated",
            title="Historical Spark Whitepaper",
            summary="Academic paper on Spark architecture.",
            source_url="https://spark.apache.org/paper",
            source_title="Spark Paper",
            reliability_tier=2
        )
    ]

    briefing = await synthesizer.synthesize(
        request=req,
        in_window_findings=findings,
        undated_findings=undated,
        verified_claims=claims
    )

    # 1. Verify schema
    assert briefing.target_company == "Databricks"
    assert briefing.target_attendee == "Ali Ghodsi"
    assert len(briefing.card5_discussion_hooks) == 3
    assert len(briefing.card6_risk_blindspots) == 3
    assert len(briefing.undated_signals) == 1

    # 2. Verify Markdown formatting & word count
    md_output = synthesizer.format_markdown(briefing)
    word_count = len(md_output.split())

    assert "## 1. Executive Snapshot" in md_output
    assert "## 2. Strategic Target Profile" in md_output
    assert "## 3. Key Attendee Dossier" in md_output
    assert "## 4. Preceding 30-Day Signals" in md_output
    assert "## 5. Strategic Discussion Points" in md_output
    assert "## 6. Risk Blindspots & Open Questions" in md_output
    assert "Undated Public Records" in md_output

    # Brevity rule: Must be strictly under 600 words for executive scanning
    assert word_count < 600, f"Word count was {word_count}, expected < 600"
