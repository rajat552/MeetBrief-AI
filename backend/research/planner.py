"""
MeetBrief AI — Shared Query Planner & Temporal Boundary Calculator
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field
import dateutil.parser

from backend.models import ManualMeetingRequest


class ResearchPlan(BaseModel):
    """Encapsulates the disjoint 5-branch research queries and calculated date bounds."""
    t_meeting: datetime
    t_current: datetime
    t_start: datetime
    t_end: datetime
    query_start_date: str = Field(description="1-day buffered start date YYYY-MM-DD")
    start_date_str: str = Field(description="Strict 30-day window start YYYY-MM-DD")
    end_date_str: str = Field(description="Strict 30-day window end YYYY-MM-DD")
    queries: Dict[str, str] = Field(description="Disjoint query strings for Branches 1-5")


class SharedQueryPlanner:
    """
    Computes exact temporal research windows and generates mutually disjoint
    search strategies to eliminate redundant queries and cross-branch data collisions.
    """

    @staticmethod
    def parse_meeting_datetime(datetime_str: str) -> datetime:
        """Parses meeting datetime with timezone awareness, normalizing to UTC."""
        try:
            dt = dateutil.parser.parse(datetime_str)
            if dt.tzinfo is None:
                # If no timezone is specified, assume UTC
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception as e:
            # Fallback to current UTC if unparseable
            return datetime.now(timezone.utc)

    @classmethod
    def calculate_bounds(
        cls,
        meeting_datetime_str: str,
        current_datetime: Optional[datetime] = None
    ) -> ResearchPlan:
        """
        Calculates the rolling 30-day research window:
        T_end = min(T_meeting, T_current)
        T_start = T_end - 30 days
        Query_start = T_start - 1 day (Buffer for publication offsets)
        """
        t_current = current_datetime or datetime.now(timezone.utc)
        t_meeting = cls.parse_meeting_datetime(meeting_datetime_str)

        # Upper bound is clamped to min(meeting, current)
        t_end = min(t_meeting, t_current)
        t_start = t_end - timedelta(days=30)
        t_query_start = t_start - timedelta(days=1)

        return ResearchPlan(
            t_meeting=t_meeting,
            t_current=t_current,
            t_start=t_start,
            t_end=t_end,
            query_start_date=t_query_start.strftime("%Y-%m-%d"),
            start_date_str=t_start.strftime("%Y-%m-%d"),
            end_date_str=t_end.strftime("%Y-%m-%d"),
            queries={}
        )

    @classmethod
    def build_plan(
        cls,
        request: ManualMeetingRequest,
        current_datetime: Optional[datetime] = None
    ) -> ResearchPlan:
        """
        Generates disjoint search queries for all 5 research branches.
        Applies attendee entity disambiguation and job freshness filters.
        """
        plan = cls.calculate_bounds(request.meeting_datetime, current_datetime)
        company = request.company_name.strip()
        attendee = request.attendee_name.strip()
        role = (request.attendee_role or "").strip()

        # Attendee entity disambiguation: bind attendee to company and known role
        attendee_disambiguation = f'"{attendee}" "{company}"'
        if role:
            attendee_disambiguation += f' "{role}"'

        # Branch 1: Static Company Background (unbounded dates)
        q_company = f'"{company}" business model core products target customers competitors'

        # Branch 2: Attendee & Executive Dossier (unbounded dates)
        q_people = f'{attendee_disambiguation} background previous roles education public speaking podcast interview'

        # Branch 3: 30-Day News & Press Releases (strictly dated)
        # Uses negative keywords (-launch, -hiring) to prevent collision with Branches 4 & 5
        q_news = f'"{company}" news OR "press release" OR "partnership" -launch -released -hiring -careers'

        # Branch 4: 30-Day Product Launches & Feature Drops (strictly dated)
        q_launches = f'"{company}" "launch" OR "released" OR "changelog" OR "feature update" OR "new product"'

        # Branch 5: 30-Day Hiring Signals & Leadership Moves (strictly dated)
        # Distinguishes newly posted listings/hires from old crawl aggregators
        q_hiring = f'"{company}" ("new opening" OR "now hiring" OR "appointed" OR "joined as") -glassdoor -indeed -salary'

        plan.queries = {
            "company_background": q_company,
            "attendee_dossier": q_people,
            "news": q_news,
            "launches": q_launches,
            "hiring": q_hiring
        }

        return plan
