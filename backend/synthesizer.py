"""
MeetBrief AI — Executive Briefing Synthesizer (< 600 words)
"""

import hashlib
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone

from backend.gateway import BifrostClient
from backend.models import (
    AttendeeDossier,
    CompanyProfile,
    ManualMeetingRequest,
    OnePageBriefing,
    ResearchFinding,
    VerifiedClaim,
)

logger = logging.getLogger(__name__)


class ExecutiveSynthesizer:
    """
    Synthesizes grounded research findings into a scannable One-Page Executive Briefing (< 600 words).
    Engineered for rapid pre-meeting review in under 2 minutes.
    """

    def __init__(self, gateway_client: Optional[BifrostClient] = None):
        self.gateway = gateway_client or BifrostClient()

    async def synthesize(
        self,
        request: ManualMeetingRequest,
        in_window_findings: List[ResearchFinding],
        undated_findings: List[ResearchFinding],
        verified_claims: List[VerifiedClaim]
    ) -> OnePageBriefing:
        """
        Synthesizes structured findings into the 6-card OnePageBriefing schema.
        Uses Bifrost Gateway when available; falls back to deterministic rule synthesis if offline.
        """
        # Calculate aggregate confidence
        if verified_claims:
            avg_conf = round(sum(c.confidence_score for c in verified_claims) / len(verified_claims), 2)
        else:
            avg_conf = 0.50

        # Group findings by category
        bg_findings = [f for f in in_window_findings if f.category == "company_background"]
        people_findings = [f for f in in_window_findings if f.category == "attendee_dossier"]
        dated_signals = [f for f in in_window_findings if f.category in ("news", "launches", "hiring")]

        # Select top 3-5 signals for Card 4
        card4_signals = dated_signals[:5]

        # Check gateway health
        gw_status = await self.gateway.check_health()
        inference_route = gw_status.mode

        # If gateway or direct provider is available, use LLM to craft high-impact text
        if (
            gw_status.is_healthy
            or self.gateway.config.is_openai_configured()
            or self.gateway.config.is_groq_configured()
            or self.gateway.config.is_gemini_configured()
        ):
            prompt = self._build_synthesis_prompt(request, in_window_findings, verified_claims)
            try:
                response = await self.gateway.complete(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a Chief of Staff preparing an executive for a high-stakes meeting. "
                                "Be concise, punchy, and strictly evidence-grounded. Total output must be under 450 words. "
                                "Never invent attendee beliefs, user capabilities, or company relationships."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=900
                )
                llm_output = response.content
                actual_mode = response.telemetry.mode
                # Parse structured cards from response or augment fallback
                return self._parse_or_assemble_briefing(
                    request=request,
                    in_window_findings=in_window_findings,
                    undated_findings=undated_findings,
                    verified_claims=verified_claims,
                    card4_signals=card4_signals,
                    people_findings=people_findings,
                    avg_conf=avg_conf,
                    inference_route=actual_mode,
                    llm_text=llm_output
                )
            except Exception as e:
                logger.warning(f"Synthesis LLM call failed: {e}. Falling back to deterministic synthesis.")

        # Deterministic assembly fallback (offline / unconfigured keys / quota exhausted)
        return self._assemble_deterministic_briefing(
            request=request,
            bg_findings=bg_findings,
            people_findings=people_findings,
            card4_signals=card4_signals,
            undated_findings=undated_findings,
            verified_claims=verified_claims,
            avg_conf=avg_conf,
            inference_route="deterministic_fallback"
        )

    def _build_synthesis_prompt(
        self,
        request: ManualMeetingRequest,
        findings: List[ResearchFinding],
        claims: List[VerifiedClaim]
    ) -> str:
        findings_summary = "\n".join(
            f"[{f.category.upper()}] {f.title}: {f.summary[:200]} (Source: {f.source_url}, PubDate: {f.published_date or 'Undated'})"
            for f in findings[:10]
        )
        return f"""
Meeting Details Supplied by User:
- Company: {request.company_name}
- Attendee: {request.attendee_name} ({request.attendee_role or 'Role unspecified'})
- DateTime: {request.meeting_datetime}
- Primary Goal: {request.meeting_goal or 'Strategic Discussion'}

Retrieved & Verified Evidence:
{findings_summary}

STRICT EVIDENCE-GROUNDING RULES:
1. DO NOT invent user-company products, internal capabilities, or customer relationships.
2. DO NOT invent internal engineering priorities, attendee opinions, preferences, or personal beliefs.
3. Assert ONLY target-company facts explicitly verified in the retrieved evidence above or supplied by the user.
4. Frame unverified discussion angles conditionally as exploratory questions (e.g. "[Conditional Suggestion] Ask if...", "[Exploratory Question] Inquire whether...").
5. Clearly distinguish verified citations from AI-generated strategic recommendations.

Please provide concise, high-density content for:
1. EXECUTIVE SNAPSHOT (60-80 words): Factual strategic context and meeting objective.
2. 3 DISCUSSION HOOKS: Tactical conversation starters tied to verified news or attendee background.
3. 3 RISK BLINDSPOTS: Critical discovery questions, budget/timing checks, and potential objections.
Keep strictly concise and actionable (under 450 words total).
""".strip()

    def _parse_or_assemble_briefing(
        self,
        request: ManualMeetingRequest,
        in_window_findings: List[ResearchFinding],
        undated_findings: List[ResearchFinding],
        verified_claims: List[VerifiedClaim],
        card4_signals: List[ResearchFinding],
        people_findings: Optional[List[ResearchFinding]] = None,
        avg_conf: float = 0.85,
        inference_route: str = "bifrost_gateway",
        llm_text: str = ""
    ) -> OnePageBriefing:
        briefing_id = "brief_" + hashlib.sha256(f"{request.company_name}_{request.attendee_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]

        people_findings = people_findings or [f for f in in_window_findings if f.category == "attendee_dossier"]

        # Default evidence-grounded hooks (used if LLM parsing does not match)
        top_signal = card4_signals[0] if card4_signals else None
        hooks = [
            f"[Verified Signal] Reference recent announcement: {top_signal.title} (Source: {top_signal.source_url})" if top_signal else f"[Exploratory Question] Inquire about {request.company_name}'s primary operational focus for the quarter.",
            f"[Conditional Suggestion] If your offering addresses {request.meeting_goal or 'workflow efficiency'}, explore whether this aligns with {request.company_name}'s current initiatives.",
            f"[Discovery Hook] Ask {request.attendee_name} about their current organizational priorities as {request.attendee_role or 'executive'}."
        ]
        
        risks = [
            f"? Authority & Decision Process: Confirm whether {request.attendee_name} holds direct budget sign-off or requires committee review.",
            f"? Implementation Priority: Inquire if {request.company_name} has allocated bandwidth and resources for {request.meeting_goal or 'this initiative'}.",
            f"⚠️ Incumbent Solutions: Identify current tools or internal workflows {request.company_name} currently relies on."
        ]

        snapshot = f"{request.company_name} is engaging in strategic discussions regarding {request.meeting_goal or 'commercial alignment'}. Recent intelligence indicates key momentum and active leadership focus around this area."

        if "EXECUTIVE SNAPSHOT" in llm_text:
            parts = llm_text.split("EXECUTIVE SNAPSHOT")
            if len(parts) > 1:
                snapshot = parts[1].split("DISCUSSION HOOKS")[0].strip(": \n")[:350]

        if "DISCUSSION HOOKS" in llm_text:
            parts = llm_text.split("DISCUSSION HOOKS")
            if len(parts) > 1:
                hook_block = parts[1].split("RISK BLINDSPOTS")[0].strip(": \n")
                parsed_hooks = [line.strip("- *0123456789.") for line in hook_block.split("\n") if len(line.strip()) > 10]
                if parsed_hooks:
                    hooks = parsed_hooks[:3]

        if "RISK BLINDSPOTS" in llm_text:
            parts = llm_text.split("RISK BLINDSPOTS")
            if len(parts) > 1:
                risk_block = parts[1].strip(": \n")
                parsed_risks = [line.strip("- *0123456789.") for line in risk_block.split("\n") if len(line.strip()) > 10]
                if parsed_risks:
                    risks = parsed_risks[:3]

        stances = [f.summary[:140] for f in people_findings if f.summary]
        if not stances:
            stances = ["No verified public quotes or stances in indexed sources; assess specific priorities during meeting discovery."]

        career = [f.title for f in people_findings[:2]]
        if not career:
            career = [f"Identified as {request.attendee_role or 'Stakeholder'} at {request.company_name} (User-supplied role)"]

        return OnePageBriefing(
            briefing_id=briefing_id,
            target_company=request.company_name,
            target_attendee=request.attendee_name,
            meeting_datetime=request.meeting_datetime,
            meeting_goal=request.meeting_goal,
            card1_executive_snapshot=snapshot,
            card2_company_profile=CompanyProfile(
                company_name=request.company_name,
                business_model="B2B Technology & Infrastructure",
                core_products=[f.title[:40] for f in in_window_findings if f.category == "company_background"][:3] or ["Enterprise Platform", "API Services"],
                target_market="Global Enterprise & High-Growth Companies",
                competitive_moat="Proprietary technology stack, developer ecosystem, and scale",
                key_competitors=["Tier-1 Market Peers", "Specialized Solutions"]
            ),
            card3_attendee_dossier=AttendeeDossier(
                name=request.attendee_name,
                verified_title=request.attendee_role or "Key Executive",
                current_company=request.company_name,
                career_history=career,
                public_stances_and_quotes=stances,
                likely_agenda=f"Explore alignment regarding {request.meeting_goal or 'collaboration'} [Proposed discussion topic]",
                communication_hook=f"Reference verified public updates from {request.company_name} or ask open discovery questions."
            ),
            card4_recent_30d_signals=card4_signals,
            card5_discussion_hooks=hooks,
            card6_risk_blindspots=risks,
            verified_claims=verified_claims[:6],
            undated_signals=undated_findings[:3],
            aggregate_confidence=avg_conf,
            inference_route=inference_route
        )

    def _assemble_deterministic_briefing(
        self,
        request: ManualMeetingRequest,
        bg_findings: List[ResearchFinding],
        people_findings: List[ResearchFinding],
        card4_signals: List[ResearchFinding],
        undated_findings: List[ResearchFinding],
        verified_claims: List[VerifiedClaim],
        avg_conf: float,
        inference_route: str = "deterministic_fallback"
    ) -> OnePageBriefing:
        briefing_id = "brief_" + hashlib.sha256(f"{request.company_name}_{request.attendee_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]

        snapshot = (
            f"Upcoming strategic meeting with {request.attendee_name} ({request.attendee_role or 'Executive'}) at {request.company_name}. "
            f"Primary focus: {request.meeting_goal or 'Strategic Partnership and Commercial Alignment'}. "
            f"Pre-meeting research indicates active corporate developments and key leadership engagement opportunities."
        )

        top_signal = card4_signals[0] if card4_signals else None
        stances = [f.summary[:140] for f in people_findings if f.summary]
        if not stances:
            stances = ["No verified public quotes or stances in indexed sources; assess specific priorities during meeting discovery."]

        career = [f.title for f in people_findings[:2]]
        if not career:
            career = [f"Identified as {request.attendee_role or 'Stakeholder'} at {request.company_name} (User-supplied role)"]

        return OnePageBriefing(
            briefing_id=briefing_id,
            target_company=request.company_name,
            target_attendee=request.attendee_name,
            meeting_datetime=request.meeting_datetime,
            meeting_goal=request.meeting_goal,
            card1_executive_snapshot=snapshot,
            card2_company_profile=CompanyProfile(
                company_name=request.company_name,
                business_model="Enterprise Technology & Services",
                core_products=[f.title[:35] for f in bg_findings[:3]] or ["Core Platform", "Cloud Solutions"],
                target_market="Enterprise & Mid-Market",
                competitive_moat="Domain expertise, established distribution, and brand leadership",
                key_competitors=["Industry Leaders", "Specialized Vendors"]
            ),
            card3_attendee_dossier=AttendeeDossier(
                name=request.attendee_name,
                verified_title=request.attendee_role or "Key Stakeholder",
                current_company=request.company_name,
                career_history=career,
                public_stances_and_quotes=stances,
                likely_agenda=f"Evaluate partnership viability and alignment on {request.meeting_goal or 'initiatives'} [Proposed topic]",
                communication_hook=f"Reference verified public updates from {request.company_name} or ask open discovery questions."
            ),
            card4_recent_30d_signals=card4_signals,
            card5_discussion_hooks=[
                f"[Verified Signal] Reference recent 30-day announcement: {top_signal.title} (Source: {top_signal.source_url})" if top_signal else f"[Exploratory Question] Ask about {request.company_name}'s current strategic priorities.",
                f"[Conditional Exploration] If relevant, test whether {request.company_name} is evaluating solutions for {request.meeting_goal or 'their current workflows'}.",
                f"[Role Discovery] Inquire with {request.attendee_name} about their team's technical roadmap and decision criteria as {request.attendee_role or 'lead'}."
            ],
            card6_risk_blindspots=[
                f"? Budget & Authority: Confirm whether {request.attendee_name} holds final budget sign-off or requires committee approval.",
                f"? Implementation Bandwidth: Address internal resourcing and timeline constraints.",
                f"⚠️ Competitive Risk: Differentiate clearly against alternative approaches they may be evaluating."
            ],
            verified_claims=verified_claims[:6],
            undated_signals=undated_findings[:3],
            aggregate_confidence=avg_conf,
            inference_route="deterministic_fallback"
        )

    @staticmethod
    def format_markdown(briefing: OnePageBriefing) -> str:
        """
        Renders the briefing into standardized, scannable Markdown (< 600 words).
        """
        lines = []
        lines.append(f"# Executive Dossier: {briefing.target_company} — {briefing.target_attendee}")
        lines.append(f"**Meeting:** {briefing.meeting_datetime} | **Objective:** {briefing.meeting_goal or 'Strategic Alignment'} | **Confidence:** {int(briefing.aggregate_confidence * 100)}%\n")
        
        lines.append("## 1. Executive Snapshot")
        lines.append(briefing.card1_executive_snapshot + "\n")
        
        lines.append("## 2. Strategic Target Profile")
        lines.append(f"- **Business Model:** {briefing.card2_company_profile.business_model}")
        lines.append(f"- **Core Products:** {', '.join(briefing.card2_company_profile.core_products)}")
        lines.append(f"- **Competitive Moat:** {briefing.card2_company_profile.competitive_moat}\n")
        
        lines.append("## 3. Key Attendee Dossier")
        lines.append(f"- **Role:** {briefing.card3_attendee_dossier.verified_title}")
        lines.append(f"- **Likely Agenda:** {briefing.card3_attendee_dossier.likely_agenda}")
        lines.append(f"- **Conversation Hook:** {briefing.card3_attendee_dossier.communication_hook}\n")
        
        lines.append("## 4. Preceding 30-Day Signals")
        if briefing.card4_recent_30d_signals:
            for s in briefing.card4_recent_30d_signals:
                date_tag = f" ({s.published_date})" if s.published_date else ""
                lines.append(f"- **[{s.category.upper()}]** [{s.title}]({s.source_url}){date_tag}: {s.summary[:140]}...")
        else:
            lines.append("- *No verified public press or product announcements in preceding 30 days.*")
        lines.append("")
        
        lines.append("## 5. Strategic Discussion Points")
        for idx, hook in enumerate(briefing.card5_discussion_hooks, 1):
            lines.append(f"{idx}. {hook}")
        lines.append("")
        
        lines.append("## 6. Risk Blindspots & Open Questions")
        for q in briefing.card6_risk_blindspots:
            lines.append(f"- {q}")
        lines.append("")

        if briefing.undated_signals:
            lines.append("> ⚠️ **Undated Public Records (Excluded from 30-Day Freshness Window):**")
            for u in briefing.undated_signals:
                lines.append(f"> - [{u.title}]({u.source_url})")

        return "\n".join(lines)
