"""
MeetBrief AI — Branch 5: 30-Day Hiring & Leadership Moves Agent
"""

from typing import List, Tuple
from backend.models import ManualMeetingRequest, ResearchFinding
from backend.research.planner import ResearchPlan
from backend.research.tavily_engine import TavilyEngine


class HiringResearchAgent:
    """
    Branch 5: Scans newly posted job openings, executive appointments, and headcount surges.
    Strictly bounded to rolling 30-day window [T_start, T_end].
    """

    def __init__(self, engine: TavilyEngine):
        self.engine = engine

    async def execute(self, request: ManualMeetingRequest, plan: ResearchPlan) -> Tuple[List[ResearchFinding], List[ResearchFinding]]:
        query = plan.queries["hiring"]
        return await self.engine.search(
            query=query,
            category="hiring",
            target_company=request.company_name,
            start_date=plan.query_start_date,
            end_date=plan.end_date_str,
            t_start=plan.t_start,
            t_end=plan.t_end,
            max_results=5
        )
