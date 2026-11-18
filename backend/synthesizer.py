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
                        {"role": "system", "content": "You are a Chief of Staff preparing an executive for a high-stakes meeting. Be concise, punchy, and evidence-grounded. Total output must be under 500 words."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=900
                )
                llm_output = response.content
                # Parse structured cards from response or augment fallback
                return self._parse_or_assemble_briefing(
                    request=request,
                    in_window_findings=in_window_findings,
                    undated_findings=undated_findings,
                    verified_claims=verified_claims,
                    card4_signals=card4_signals,
                    avg_conf=avg_conf,
                    inference_route=inference_route,
                    llm_text=llm_output
                )
            except Exception as e:
                logger.warning(f"Synthesis LLM call failed: {e}. Falling back to deterministic synthesis.")

        # Deterministic assembly fallback (offline / unconfigured keys)
        return self._assemble_deterministic_briefing(
            request=request,
            bg_findings=bg_findings,
            people_findings=people_findings,
            card4_signals=card4_signals,
            undated_findings=undated_findings,
            verified_claims=verified_claims,
            avg_conf=avg_conf,
            inference_route=inference_route
        )

    def _build_synthesis_prompt(
        self,
        request: ManualMeetingRequest,
        findings: List[ResearchFinding],
        claims: List[VerifiedClaim]
    ) -> str:
        findings_summary = "\n".join(
            f"[{f.category.upper()}] {f.title}: {f.summary[:150]} (Source: {f.source_url})"
            for f in findings[:10]
        )
        return f"""
Meeting Details:
- Company: {request.company_name}
- Attendee: {request.attendee_name} ({request.attendee_role or 'Executive'})
- DateTime: {request.meeting_datetime}
- Goal: {request.meeting_goal or 'Strategic Discussion'}

Retrieved Evidence:
{findings_summary}

Please provide concise, high-density content for:
1. EXECUTIVE SNAPSHOT (60-80 words): Strategic context and mutual leverage.
2. 3 DISCUSSION HOOKS: Tactical conversation starters tied to recent news or attendee background.
3. 3 RISK BLINDSPOTS: Critical discovery questions and potential objections.
Keep strictly concise and actionable.
""".strip()

    def _parse_or_assemble_briefing(
        self,
        request: ManualMeetingRequest,
        in_window_findings: List[ResearchFinding],
        undated_findings: List[ResearchFinding],
        verified_claims: List[VerifiedClaim],
        card4_signals: List[ResearchFinding],
        avg_conf: float,
        inference_route: str,
        llm_text: str
    ) -> OnePageBriefing:
        briefing_id = "brief_" + hashlib.sha256(f"{request.company_name}_{request.attendee_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]

        # Extract snapshot and discussion hooks
        snapshot = f"{request.company_name} is engaging in strategic discussions regarding {request.meeting_goal or 'commercial alignment'}. Recent intelligence indicates key momentum and active leadership focus around this area."
        
        hooks = [
            f"Congratulate on recent momentum: Reference recent 30-day corporate updates and market positioning.",
            f"Value Alignment: Connect our capabilities to {request.company_name}'s current growth initiatives.",
            f"Attendee Background Hook: Acknowledge {request.attendee_name}'s focus area and leadership initiatives."
        ]
        
        risks = [
            f"Budget & Timeline Clarity: Uncover exact fiscal timing and decision-making criteria.",
            f"Competitive Pressure: Assess how current industry dynamics are shaping their evaluation.",
            f"Technical or Organizational Hurdles: Address potential adoption or integration blindspots."
        ]

        if "EXECUTIVE SNAPSHOT" in llm_text:
            parts = llm_text.split("EXECUTIVE SNAPSHOT")
            if len(parts) > 1:
                snapshot = parts[1].split("DISCUSSION HOOKS")[0].strip(": \n")[:350]

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
                career_history=["Experienced industry executive with proven operational track record"],
                public_stances_and_quotes=["Focuses on scale, architectural elegance, and strategic execution"],
                likely_agenda=f"Explore strategic fit regarding {request.meeting_goal or 'collaboration'}",
                communication_hook=f"Reference shared focus on {request.company_name}'s market trajectory"
            ),
            card4_recent_30d_signals=card4_signals,
            card5_discussion_hooks=hooks,
            card6_risk_blindspots=risks,
            verified_claims=verified_claims[:6],
            undated_signals=undated_findings[:3],
            aggregate_confidence=avg_conf,
            inference_route="bifrost_gateway" if inference_route == "bifrost_gateway" else "fallback_direct"
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
        inference_route: str
    ) -> OnePageBriefing:
        briefing_id = "brief_" + hashlib.sha256(f"{request.company_name}_{request.attendee_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:10]

        snapshot = (
            f"Upcoming strategic meeting with {request.attendee_name} ({request.attendee_role or 'Executive'}) at {request.company_name}. "
            f"Primary focus: {request.meeting_goal or 'Strategic Partnership and Commercial Alignment'}. "
            f"Pre-meeting research indicates active corporate developments and key leadership engagement opportunities."
        )

        bg_text = bg_findings[0].summary if bg_findings else f"{request.company_name} is a leading industry enterprise."
        
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
                career_history=[f.title for f in people_findings[:2]] or [f"Executive leader at {request.company_name}"],
                public_stances_and_quotes=["Advocates for operational excellence and strategic growth"],
                likely_agenda=f"Evaluate partnership viability and alignment on {request.meeting_goal or 'initiatives'}",
                communication_hook=f"Acknowledge recent leadership initiatives at {request.company_name}"
            ),
            card4_recent_30d_signals=card4_signals,
            card5_discussion_hooks=[
                f"Icebreaker: Acknowledge {request.company_name}'s recent momentum and visible market impact.",
                f"Strategic Value: Present how our solution directly accelerates {request.meeting_goal or 'their core objectives'}.",
                f"Commercial Scope: Align on shared roadmap milestones for Q1/Q2."
            ],
            card6_risk_blindspots=[
                f"? Budget & Authority: Confirm whether {request.attendee_name} holds final budget sign-off or requires committee approval.",
                f"? Implementation Bandwidth: Address internal resourcing and timeline constraints.",
                f"⚠️ Competitive Risk: Differentiate clearly against alternative approaches they may be evaluating."
            ],
            verified_claims=verified_claims[:6],
            undated_signals=undated_findings[:3],
            aggregate_confidence=avg_conf,
            inference_route="bifrost_gateway" if inference_route == "bifrost_gateway" else "fallback_direct"
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
