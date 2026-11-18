"""
MeetBrief AI — LangGraph Orchestration & Parallel StateGraph Tests
Verifies asynchronous graph compilation, topology, parallel branch execution,
operator.add state reduction, and partial branch failure recovery.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.agent import MeetBriefOrchestrator, OrchestratorGraphState
from backend.models import ManualMeetingRequest, ResearchFinding
from backend.gateway import GatewayResponse, GatewayTelemetry


@pytest.fixture
def sample_request() -> ManualMeetingRequest:
    return ManualMeetingRequest(
        company_name="Stripe",
        attendee_name="Patrick Collison",
        attendee_role="CEO",
        meeting_datetime="2026-11-20 14:00 UTC",
        meeting_goal="Explore AI payment infrastructure",
    )


def test_graph_compilation_and_topology():
    """Verifies that the LangGraph StateGraph is compiled with all required nodes."""
    orchestrator = MeetBriefOrchestrator()
    assert orchestrator.graph is not None

    nodes = orchestrator.graph.nodes
    expected_nodes = [
        "plan",
        "branch_company",
        "branch_people",
        "branch_news",
        "branch_launches",
        "branch_hiring",
        "verify",
        "synthesize",
    ]
    for node in expected_nodes:
        assert node in nodes, f"Expected node '{node}' missing from LangGraph graph"


@pytest.mark.asyncio
async def test_langgraph_ainvoke_execution(sample_request):
    """Verifies that invoke_graph executes end-to-end and returns a complete state."""
    orchestrator = MeetBriefOrchestrator()

    mock_finding = ResearchFinding(
        category="company_background",
        title="Stripe Overview",
        summary="Stripe powers global internet commerce infrastructure.",
        source_url="https://stripe.com/about",
        source_title="About Stripe",
        reliability_tier=1,
    )

    mock_llm_response = GatewayResponse(
        content="### Strategic Executive Briefing\n\nStripe is an established financial infrastructure platform.",
        telemetry=GatewayTelemetry(
            model="gemini-flash-latest",
            latency_ms=10.0,
            mode="fallback_direct"
        )
    )

    # Mock all branch agents and gateway completion for deterministic, offline testing
    with patch.object(orchestrator.agent_company, "execute", new_callable=AsyncMock) as m_comp, \
         patch.object(orchestrator.agent_people, "execute", new_callable=AsyncMock) as m_peop, \
         patch.object(orchestrator.agent_news, "execute", new_callable=AsyncMock) as m_news, \
         patch.object(orchestrator.agent_launches, "execute", new_callable=AsyncMock) as m_laun, \
         patch.object(orchestrator.agent_hiring, "execute", new_callable=AsyncMock) as m_hire, \
         patch.object(orchestrator.gateway, "complete", new_callable=AsyncMock) as m_llm:

        m_comp.return_value = ([mock_finding], [])
        m_peop.return_value = ([], [])
        m_news.return_value = ([], [])
        m_laun.return_value = ([], [])
        m_hire.return_value = ([], [])
        m_llm.return_value = mock_llm_response

        result_state = await orchestrator.invoke_graph(sample_request)

        assert result_state["plan"] is not None
        assert len(result_state["in_window_findings"]) >= 1
        assert result_state["briefing"] is not None
        assert result_state["briefing"].target_company == "Stripe"
        assert result_state["briefing"].card2_company_profile.company_name == "Stripe"


@pytest.mark.asyncio
async def test_langgraph_partial_failure_tolerance(sample_request):
    """Verifies that if one branch fails, LangGraph records the error and synthesizes from other branches."""
    orchestrator = MeetBriefOrchestrator()

    mock_finding = ResearchFinding(
        category="company_background",
        title="Stripe Reliability",
        summary="Stripe processes hundreds of billions annually.",
        source_url="https://stripe.com/reliability",
        source_title="Stripe Infrastructure",
        reliability_tier=1,
    )

    with patch.object(orchestrator.agent_company, "execute", new_callable=AsyncMock) as m_comp, \
         patch.object(orchestrator.agent_news, "execute", new_callable=AsyncMock) as m_news, \
         patch.object(orchestrator.gateway, "complete", new_callable=AsyncMock) as m_llm:

        m_comp.return_value = ([mock_finding], [])
        m_news.side_effect = RuntimeError("Tavily rate limit exceeded on news branch")
        m_llm.side_effect = RuntimeError("Offline LLM mock")

        result_state = await orchestrator.invoke_graph(sample_request)

        # Graph did not crash
        assert result_state["briefing"] is not None
        # Error is recorded in state
        assert any("news:" in err for err in result_state.get("errors", []))
        # Successful findings from working branch are preserved
        assert len(result_state["in_window_findings"]) >= 1


@pytest.mark.asyncio
async def test_langgraph_safe_state_reduction(sample_request):
    """Verifies that operator.add reducer accumulates findings across all 5 branches."""
    orchestrator = MeetBriefOrchestrator()

    def make_finding(cat: str) -> ResearchFinding:
        return ResearchFinding(
            category=cat,  # type: ignore
            title=f"{cat} signal",
            summary=f"Summary for {cat}",
            source_url=f"https://stripe.com/{cat}",
            source_title=f"Source {cat}",
            reliability_tier=1,
        )

    with patch.object(orchestrator.agent_company, "execute", new_callable=AsyncMock) as m_comp, \
         patch.object(orchestrator.agent_people, "execute", new_callable=AsyncMock) as m_peop, \
         patch.object(orchestrator.agent_news, "execute", new_callable=AsyncMock) as m_news, \
         patch.object(orchestrator.agent_launches, "execute", new_callable=AsyncMock) as m_laun, \
         patch.object(orchestrator.agent_hiring, "execute", new_callable=AsyncMock) as m_hire, \
         patch.object(orchestrator.gateway, "complete", new_callable=AsyncMock) as m_llm:

        m_comp.return_value = ([make_finding("company_background")], [])
        m_peop.return_value = ([make_finding("attendee_dossier")], [])
        m_news.return_value = ([make_finding("news")], [])
        m_laun.return_value = ([make_finding("launches")], [])
        m_hire.return_value = ([make_finding("hiring")], [])
        m_llm.side_effect = RuntimeError("Offline LLM mock")

        result_state = await orchestrator.invoke_graph(sample_request)

        # Accumulator should have merged all 5 findings
        categories = {f.category for f in result_state["in_window_findings"]}
        assert len(categories) == 5
        assert "company_background" in categories
        assert "news" in categories
        assert "launches" in categories
        assert "hiring" in categories
        assert "attendee_dossier" in categories


@pytest.mark.asyncio
async def test_langgraph_zero_thought_leakage(sample_request):
    """Verifies that LangGraph execution state emits zero private reasoning or chain-of-thought tokens."""
    orchestrator = MeetBriefOrchestrator()
    with patch.object(orchestrator.gateway, "complete", new_callable=AsyncMock) as m_llm:
        m_llm.side_effect = RuntimeError("Offline LLM mock")
        result_state = await orchestrator.invoke_graph(sample_request)

        # State serialization check
        state_str = str(result_state).lower()
        assert "agent_thought" not in state_str
        assert "private_thinking" not in state_str
        assert "chain_of_thought" not in state_str
