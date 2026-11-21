"""
MeetBrief AI — Executive Voice Briefing Engine (Omnidimension Voice AI)
Converts structured briefings into a 90-second spoken executive audio brief.
"""

import base64
import logging
import re
from typing import Optional
import httpx

from backend.config import Settings, settings
from backend.models import AudioBriefingResponse, OnePageBriefing

logger = logging.getLogger(__name__)


class AudioBriefingService:
    """
    Synthesizes executive briefing dossiers into high-fidelity spoken audio briefs.
    Utilizes Omnidimension Voice AI as the primary provider with transparent fallback
    to client-side Web Speech API metadata for offline resilience.
    """

    def __init__(self, cfg: Optional[Settings] = None):
        self.config = cfg or settings

    def clean_text_for_speech(self, text: str) -> str:
        """Removes markdown tags, bracketed citations, and raw URLs for natural text-to-speech cadence."""
        # 1. Remove markdown links: [label](url) -> label
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 2. Remove any remaining raw URLs
        text = re.sub(r'https?://\S+', '', text)
        # 3. Remove square bracket labels like [Verified Signal], [Conditional Exploration], etc.
        text = re.sub(r'\[[^\]]+\]', '', text)
        # Remove markdown formatting characters (*, _, #, `, ~, >)
        text = re.sub(r'[*_#`~>]', '', text)
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def build_spoken_script(self, briefing: OnePageBriefing) -> str:
        """
        Builds a crisp, natural 220-280 word executive spoken script designed for
        a 90-second pre-meeting commute briefing.
        """
        parts = []

        # 1. Opening hook
        attendee = briefing.target_attendee
        company = briefing.target_company
        meeting_goal = briefing.meeting_goal or "strategic partnership and alignment"
        parts.append(
            f"Here is your executive audio briefing for your upcoming meeting with {attendee} at {company}. "
            f"Your stated objective is {meeting_goal}."
        )

        # 2. Strategic Context / Snapshot
        clean_snapshot = self.clean_text_for_speech(briefing.card1_executive_snapshot)
        # Limit snapshot to first 2 sentences for brevity
        snapshot_sentences = [s.strip() for s in clean_snapshot.split('.') if len(s.strip()) > 5]
        parts.append("Strategic context: " + ". ".join(snapshot_sentences[:2]) + ".")

        # 3. Preceding 30-Day Signals
        if briefing.card4_recent_30d_signals:
            top_signals = briefing.card4_recent_30d_signals[:2]
            signal_texts = []
            for s in top_signals:
                clean_title = self.clean_text_for_speech(s.title)
                signal_texts.append(clean_title)
            parts.append("Recent verified developments include: " + "; ".join(signal_texts) + ".")

        # 4. Top Discussion Hooks
        if briefing.card5_discussion_hooks:
            clean_hooks = [self.clean_text_for_speech(h) for h in briefing.card5_discussion_hooks[:3]]
            parts.append(
                f"When leading the conversation, consider these angles. First: {clean_hooks[0]}. "
                f"Second: {clean_hooks[1] if len(clean_hooks) > 1 else 'align on technical timeline'}."
            )

        # 5. Key Blindspots / Discovery
        if briefing.card6_risk_blindspots:
            clean_risk = self.clean_text_for_speech(briefing.card6_risk_blindspots[0])
            parts.append(f"As a risk check: {clean_risk}.")

        # 6. Closing Outro
        parts.append(f"You are now primed for high-leverage engagement with {attendee}. Good luck with the meeting.")

        script = " ".join(parts)
        return self.clean_text_for_speech(script)

    async def generate_audio(self, briefing: OnePageBriefing) -> AudioBriefingResponse:
        """
        Generates spoken audio using Omnidimension Voice AI when configured,
        or packages structured speech metadata for instant Web Speech API playback.
        """
        script = self.build_spoken_script(briefing)
        word_count = len(script.split())
        # Average speaking speed: ~140 words per minute (2.33 words per second)
        estimated_seconds = max(30, int(word_count / 2.33))

        # If Omnidimension is configured, execute API call
        if self.config.is_omnidimension_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {self.config.OMNIDIMENSION_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "input": script,
                    "voice": self.config.OMNIDIMENSION_VOICE_ID,
                    "model": "omni-voice-v1",
                    "response_format": "mp3"
                }
                endpoint = f"{self.config.OMNIDIMENSION_BASE_URL}/audio/speech"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(endpoint, headers=headers, json=payload)
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "audio" in content_type or "octet-stream" in content_type:
                            audio_b64 = base64.b64encode(response.content).decode("utf-8")
                            return AudioBriefingResponse(
                                spoken_script=script,
                                duration_estimated_seconds=estimated_seconds,
                                provider="omnidimension",
                                voice_id=self.config.OMNIDIMENSION_VOICE_ID,
                                audio_base64=f"data:audio/mp3;base64,{audio_b64}"
                            )
                        # JSON response with audio URL
                        data = response.json()
                        audio_url = data.get("audio_url") or data.get("url")
                        return AudioBriefingResponse(
                            spoken_script=script,
                            duration_estimated_seconds=estimated_seconds,
                            provider="omnidimension",
                            voice_id=self.config.OMNIDIMENSION_VOICE_ID,
                            audio_url=audio_url
                        )
                    else:
                        logger.warning(
                            f"Omnidimension API returned status {response.status_code}: {response.text[:200]}. "
                            "Gracefully falling back to browser speech synthesis."
                        )
            except Exception as e:
                logger.warning(f"Omnidimension Voice API request error: {e}. Falling back to browser speech synthesis.")

        # Zero-lag Web Speech API fallback
        return AudioBriefingResponse(
            spoken_script=script,
            duration_estimated_seconds=estimated_seconds,
            provider="browser_tts_fallback",
            voice_id=self.config.OMNIDIMENSION_VOICE_ID
        )
