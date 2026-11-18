"""
MeetBrief AI — Branch 2: Attendee & Executive Dossier Agent
"""

from typing import List, Tuple
from backend.models import ManualMeetingRequest, ResearchFinding
from backend.research.planner import ResearchPlan
from backend.research.tavily_engine import TavilyEngine


class PeopleResearchAgent:
    """
    Branch 2: Researches attendee career history, role, public talks, and quotes.
    Scope: Entity-disambiguated attendee background tied to company domain.
    Unbounded by time (historical career trajectory is valid).
    """

    def __init__(self, engine: TavilyEngine):
        self.engine = engine

    async def execute(self, request: ManualMeetingRequest, plan: ResearchPlan) -> Tuple[List[ResearchFinding], List[ResearchFinding]]:
        query = plan.queries["attendee_dossier"]
        return await self.engine.search(
            query=query,
            category="attendee_dossier",
            target_company=request.company_name,
            start_date=None,
            end_date=None,
            t_start=None,
            t_end=None,
            max_results=4
        )
