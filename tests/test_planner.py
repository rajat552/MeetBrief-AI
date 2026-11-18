"""
Unit Tests for Shared Query Planner & Temporal Date Bounds
"""

from datetime import datetime, timedelta, timezone
import pytest
from backend.models import ManualMeetingRequest
from backend.research.planner import SharedQueryPlanner


def test_timezone_normalization_to_utc():
    # Eastern Standard Time: UTC-5
    dt_str = "2026-11-20 14:00:00-05:00"
    parsed = SharedQueryPlanner.parse_meeting_datetime(dt_str)
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 19  # 14 + 5 = 19 UTC


def test_future_meeting_date_clamping():
    # Meeting is 7 days in the future
    t_current = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
    meeting_str = "2026-11-25 15:00:00Z"

    plan = SharedQueryPlanner.calculate_bounds(meeting_str, current_datetime=t_current)

    # Upper bound MUST be clamped to t_current (2026-11-18)
    assert plan.t_end == t_current
    assert plan.end_date_str == "2026-11-18"
    assert plan.start_date_str == "2026-10-19"  # 18 - 30 days = Oct 19
    assert plan.query_start_date == "2026-10-18"  # 1-day buffer = Oct 18


def test_past_meeting_bounds():
    # Meeting occurred in the past
    t_current = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
    meeting_str = "2026-11-10 10:00:00Z"

    plan = SharedQueryPlanner.calculate_bounds(meeting_str, current_datetime=t_current)

    # Upper bound is the past meeting time
    assert plan.t_end == datetime(2026, 11, 10, 10, 0, 0, tzinfo=timezone.utc)
    assert plan.end_date_str == "2026-11-10"
    assert plan.start_date_str == "2026-10-11"
    assert plan.query_start_date == "2026-10-10"


def test_disjoint_query_generation():
    req = ManualMeetingRequest(
        company_name="Databricks",
        attendee_name="Ali Ghodsi",
        attendee_role="CEO",
        meeting_datetime="2026-11-20 14:00:00Z"
    )
    t_current = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
    plan = SharedQueryPlanner.build_plan(req, current_datetime=t_current)

    queries = plan.queries
    assert "company_background" in queries
    assert "attendee_dossier" in queries
    assert "news" in queries
    assert "launches" in queries
    assert "hiring" in queries

    # Attendee disambiguation: binds person to company and role
    assert '"Ali Ghodsi" "Databricks" "CEO"' in queries["attendee_dossier"]

    # News branch includes negative terms to prevent overlap with launches/hiring
    assert "-launch" in queries["news"]
    assert "-hiring" in queries["news"]

    # Hiring branch targets active new openings
    assert '"new opening"' in queries["hiring"] or '"now hiring"' in queries["hiring"]
