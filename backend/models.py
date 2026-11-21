"""
MeetBrief AI — Domain Models & Pydantic v2 Schemas
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ManualMeetingRequest(BaseModel):
    """Primary meeting preparation request input."""
    company_name: str = Field(..., min_length=1, description="Target company or organization name")
    attendee_name: str = Field(..., min_length=1, description="Primary meeting participant name")
    attendee_email: Optional[str] = Field(default=None, description="Optional attendee corporate email")
    attendee_role: Optional[str] = Field(default=None, description="Known attendee role or title")
    meeting_datetime: str = Field(..., min_length=1, description="Scheduled date and time of the meeting")
    meeting_title: Optional[str] = Field(default="Strategic Discussion", description="Title or topic")
    meeting_goal: Optional[str] = Field(default=None, description="User's objective for the meeting")

    @field_validator("company_name", "attendee_name", "meeting_datetime", "attendee_role", "meeting_title", "meeting_goal", mode="before")
    @classmethod
    def sanitize_input(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Strip control characters (null bytes, bell, backspace, etc.)
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
            # Strip script/style/iframe tags and their inner contents
            cleaned = re.sub(r"<(script|style|iframe)[^>]*>.*?</\1>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            # Strip any remaining HTML tags (e.g. <img src=...>)
            cleaned = re.sub(r"<[^>]*>", "", cleaned).strip()
            return cleaned
        return v

    @field_validator("company_name", "attendee_name", "meeting_datetime")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


class ResearchFinding(BaseModel):
    """An individual research signal retrieved from web intelligence."""
    category: Literal["company_background", "attendee_dossier", "news", "launches", "hiring", "undated"]
    title: str
    summary: str
    source_url: str
    source_title: str
    published_date: Optional[str] = None
    freshness_days_ago: Optional[int] = None
    reliability_tier: int = Field(default=2, ge=1, le=3, description="1=Primary, 2=Reputable Press, 3=Aggregator")
    matched_passage: Optional[str] = Field(default=None, description="Exact passage snippet from source content")


class VerifiedClaim(BaseModel):
    """Atomic factual proposition evaluated by the evidence grounding engine."""
    claim: str
    verification_status: Literal["VERIFIED_PRIMARY", "REPORTED_SECONDARY", "UNVERIFIED", "CONFLICTED"]
    source_url: str
    source_title: str
    source_passage: Optional[str] = None
    source_date: Optional[str] = None
    alignment_score: float = Field(ge=0.0, le=1.0, description="Heuristic semantic alignment score")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall factual grounding confidence")
    conflict_notes: Optional[str] = None


class AttendeeDossier(BaseModel):
    """Structured executive intelligence card."""
    name: str
    verified_title: Optional[str] = None
    current_company: str
    career_history: List[str] = Field(default_factory=list)
    public_stances_and_quotes: List[str] = Field(default_factory=list)
    likely_agenda: Optional[str] = None
    communication_hook: Optional[str] = None


class CompanyProfile(BaseModel):
    """Structured static company background card."""
    company_name: str
    business_model: str
    core_products: List[str] = Field(default_factory=list)
    target_market: str
    competitive_moat: str
    key_competitors: List[str] = Field(default_factory=list)


class OnePageBriefing(BaseModel):
    """
    Standardized Scannable One-Page Executive Intelligence Dossier (< 600 words).
    Engineered for executive review in under 2 minutes.
    """
    briefing_id: str
    target_company: str
    target_attendee: str
    meeting_datetime: str
    meeting_goal: Optional[str] = None
    
    # 6 Core Executive Cards
    card1_executive_snapshot: str = Field(description="~80 words context on strategic importance")
    card2_company_profile: CompanyProfile
    card3_attendee_dossier: AttendeeDossier
    card4_recent_30d_signals: List[ResearchFinding] = Field(default_factory=list)
    card5_discussion_hooks: List[str] = Field(default_factory=list, description="3 tactical icebreakers & value points")
    card6_risk_blindspots: List[str] = Field(default_factory=list, description="3 discovery questions & risks")
    
    # Evidence & Verification Grounding
    verified_claims: List[VerifiedClaim] = Field(default_factory=list)
    undated_signals: List[ResearchFinding] = Field(default_factory=list, description="Preserved undated records with warning")
    aggregate_confidence: float = Field(ge=0.0, le=1.0)
    
    inference_route: Literal["bifrost_gateway", "direct_provider_fallback", "deterministic_fallback"]
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SSEEventPayload(BaseModel):
    """Safe Server-Sent Event payload."""
    event_type: Literal[
        "gateway_status",
        "stage_update",
        "tool_status",
        "source_discovered",
        "claims_verified",
        "streaming",
        "complete",
        "error"
    ]
    data: Dict[str, Any]


class AudioBriefingResponse(BaseModel):
    """
    Spoken Executive Briefing payload generated by Omnidimension Voice AI
    or formatted for resilient zero-lag Web Speech API playback.
    """
    spoken_script: str
    duration_estimated_seconds: int
    provider: Literal["omnidimension", "browser_tts_fallback"]
    voice_id: str
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
