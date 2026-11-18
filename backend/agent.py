"""
MeetBrief AI — LangGraph Multi-Agent Orchestrator & Safe Streaming Pipeline
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from backend.config import Settings, settings
from backend.gateway import BifrostClient
from backend.models import (
    ManualMeetingRequest,
    OnePageBriefing,
    ResearchFinding,
    SSEEventPayload,
    VerifiedClaim,
)
from backend.research.company_agent import CompanyResearchAgent
from backend.research.dedup import DeduplicationRegister
from backend.research.hiring_agent import HiringResearchAgent
from backend.research.launches_agent import LaunchesResearchAgent
from backend.research.news_agent import NewsResearchAgent
from backend.research.people_agent import PeopleResearchAgent
from backend.research.planner import ResearchPlan, SharedQueryPlanner
from backend.research.tavily_engine import TavilyEngine
from backend.synthesizer import ExecutiveSynthesizer
from backend.verifier import EvidenceGroundingEngine

logger = logging.getLogger(__name__)


class MeetBriefOrchestrator:
    """
    Coordinates the complete multi-agent pipeline:
    1. Input normalization & temporal date bounding ([min(T_meet, T_curr)-30d, min(T_meet, T_curr)])
    2. Parallel 5-branch research fan-out via asyncio.gather with deduplication
    3. Deterministic evidence grounding & claim verification
    4. One-page executive briefing synthesis (< 600 words)
    5. Safe SSE event streaming (strictly withholding private model reasoning)
    """

    def __init__(self, cfg: Optional[Settings] = None):
        self.config = cfg or settings
        self.gateway = BifrostClient(cfg=self.config)
        self.dedup = DeduplicationRegister()
        self.tavily = TavilyEngine(cfg=self.config, dedup=self.dedup)
        self.synthesizer = ExecutiveSynthesizer(gateway_client=self.gateway)

        # 5 Research Agents
        self.agent_company = CompanyResearchAgent(self.tavily)
        self.agent_people = PeopleResearchAgent(self.tavily)
        self.agent_news = NewsResearchAgent(self.tavily)
        self.agent_launches = LaunchesResearchAgent(self.tavily)
        self.agent_hiring = HiringResearchAgent(self.tavily)

    async def execute_stream(
        self,
        request: ManualMeetingRequest
    ) -> AsyncGenerator[str, None]:
        """
        Executes the end-to-end agent workflow, yielding SSE frames:
        'event: <event_type>\ndata: <json_data>\n\n'
        """
        # Helper to format SSE message
        def sse_frame(event_type: str, data: Any) -> str:
            payload = data if isinstance(data, (dict, list, str, int, float, bool)) else data.model_dump()
            return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

        try:
            # ------------------------------------------------------------------
            # Stage 0: Gateway Health Check & Inference Route Status
            # ------------------------------------------------------------------
            gw_status = await self.gateway.check_health()
            yield sse_frame("gateway_status", {
                "mode": gw_status.mode,
                "endpoint": gw_status.endpoint,
                "reason": gw_status.reason,
                "available_models": gw_status.available_models
            })

            # ------------------------------------------------------------------
            # Stage 1: Context Normalization & Temporal Date Bounding
            # ------------------------------------------------------------------
            yield sse_frame("stage_update", {
                "stage": "query_planning",
                "status": "active",
                "description": "Calculating rolling 30-day temporal window and disjoint search queries..."
            })

            plan: ResearchPlan = SharedQueryPlanner.build_plan(request)
            await self.dedup.clear()

            yield sse_frame("stage_update", {
                "stage": "query_planning",
                "status": "done",
                "description": f"Target interval: {plan.start_date_str} to {plan.end_date_str} (UTC)"
            })

            # ------------------------------------------------------------------
            # Stage 2: Parallel 5-Branch Research Fan-Out
            # ------------------------------------------------------------------
            yield sse_frame("stage_update", {
                "stage": "parallel_research",
                "status": "active",
                "description": "Executing 5 disjoint research branches concurrently..."
            })

            yield sse_frame("tool_status", {
                "tool": "tavily",
                "target": "all_5_branches",
                "status": "running"
            })

            # Execute all 5 branches concurrently
            results: List[Any] = await asyncio.gather(
                self.agent_company.execute(request, plan),
                self.agent_people.execute(request, plan),
                self.agent_news.execute(request, plan),
                self.agent_launches.execute(request, plan),
                self.agent_hiring.execute(request, plan),
                return_exceptions=True
            )

            in_window_findings: List[ResearchFinding] = []
            undated_findings: List[ResearchFinding] = []

            branch_names = ["company_background", "attendee_dossier", "news", "launches", "hiring"]

            for idx, res in enumerate(results):
                b_name = branch_names[idx]
                if isinstance(res, Exception):
                    logger.error(f"Branch {b_name} failed: {res}")
                    continue
                if isinstance(res, tuple) and len(res) == 2:
                    in_win, undated = res
                    in_window_findings.extend(in_win)
                    undated_findings.extend(undated)

                    for f in in_win:
                        yield sse_frame("source_discovered", {
                            "url": f.source_url,
                            "title": f.source_title,
                            "category": f.category,
                            "tier": f.reliability_tier,
                            "published_date": f.published_date
                        })

            yield sse_frame("stage_update", {
                "stage": "parallel_research",
                "status": "done",
                "description": f"Retrieved {len(in_window_findings)} verified in-window signals and {len(undated_findings)} undated records."
            })

            # ------------------------------------------------------------------
            # Stage 3: Deterministic Evidence Grounding & Claim Verification
            # ------------------------------------------------------------------
            yield sse_frame("stage_update", {
                "stage": "evidence_verification",
                "status": "active",
                "description": "Grounding material claims against source snippets and checking contradictions..."
            })

            verified_claims: List[VerifiedClaim] = EvidenceGroundingEngine.ground_findings(in_window_findings)

            verified_count = sum(1 for c in verified_claims if c.verification_status == "VERIFIED_PRIMARY")
            reported_count = sum(1 for c in verified_claims if c.verification_status == "REPORTED_SECONDARY")
            conflicted_count = sum(1 for c in verified_claims if c.verification_status == "CONFLICTED")

            yield sse_frame("claims_verified", {
                "total": len(verified_claims),
                "verified_count": verified_count,
                "reported_count": reported_count,
                "conflicted_count": conflicted_count
            })

            yield sse_frame("stage_update", {
                "stage": "evidence_verification",
                "status": "done",
                "description": f"Verified {verified_count} primary, {reported_count} secondary claims ({conflicted_count} conflicts detected)."
            })

            # ------------------------------------------------------------------
            # Stage 4: Executive Synthesis & Briefing Streaming
            # ------------------------------------------------------------------
            yield sse_frame("stage_update", {
                "stage": "dossier_synthesis",
                "status": "active",
                "description": "Synthesizing Scannable One-Page Executive Briefing (< 600 words)..."
            })

            briefing: OnePageBriefing = await self.synthesizer.synthesize(
                request=request,
                in_window_findings=in_window_findings,
                undated_findings=undated_findings,
                verified_claims=verified_claims
            )

            # Render markdown and stream chunks cleanly
            formatted_md = ExecutiveSynthesizer.format_markdown(briefing)
            lines = formatted_md.split("\n")
            for line in lines:
                yield sse_frame("streaming", {"content": line + "\n"})
                await asyncio.sleep(0.01)

            yield sse_frame("stage_update", {
                "stage": "dossier_synthesis",
                "status": "done",
                "description": "One-Page Executive Briefing ready."
            })

            # ------------------------------------------------------------------
            # Stage 5: Complete Event with Structured Payload
            # ------------------------------------------------------------------
            yield sse_frame("complete", briefing.model_dump())

        except Exception as e:
            logger.exception("Unexpected error in MeetBriefOrchestrator")
            yield sse_frame("error", {
                "code": "EXECUTION_ERROR",
                "message": f"Pipeline error: {str(e)}",
                "recoverable": False
            })
