"""
MeetBrief AI — Branch 1: Static Company Background Agent
"""

from typing import List, Tuple
from backend.models import ManualMeetingRequest, ResearchFinding
from backend.research.planner import ResearchPlan
from backend.research.tavily_engine import TavilyEngine


class CompanyResearchAgent:
    """
    Branch 1: Researches foundational company background.
    Scope: Business model, core products, target customers, competitive moat, competitors.
    Unbounded by time (historical founding context is valid).
    """

    def __init__(self, engine: TavilyEngine):
        self.engine = engine

    async def execute(self, request: ManualMeetingRequest, plan: ResearchPlan) -> Tuple[List[ResearchFinding], List[ResearchFinding]]:
        query = plan.queries["company_background"]
        return await self.engine.search(
            query=query,
            category="company_background",
            target_company=request.company_name,
            start_date=None,
            end_date=None,
            t_start=None,
            t_end=None,
            max_results=4
        )
