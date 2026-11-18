"""
MeetBrief AI — Tavily Research Engine & Date Validation Gate
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import dateutil.parser
import httpx

from backend.config import Settings, settings
from backend.models import ResearchFinding
from backend.research.dedup import DeduplicationRegister

logger = logging.getLogger(__name__)


# Domain authority classification sets
TIER_1_PATTERNS = [
    "sec.gov", "github.com", "linkedin.com", "crunchbase.com"
]

TIER_2_DOMAINS = [
    "reuters.com", "bloomberg.com", "techcrunch.com", "wsj.com",
    "ft.com", "forbes.com", "cnbc.com", "venturebeat.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com",
    "theverge.com", "wired.com", "arstechnica.com", "zdnet.com"
]


class TavilyEngine:
    """
    Executes search queries via Tavily API with date bounding,
    raw snippet extraction, domain tiering, and post-retrieval timestamp validation.
    """

    def __init__(self, cfg: Optional[Settings] = None, dedup: Optional[DeduplicationRegister] = None):
        self.config = cfg or settings
        self.dedup = dedup or DeduplicationRegister()
        self.base_url = "https://api.tavily.com"

    @staticmethod
    def classify_domain_tier(url: str, target_company: str = "") -> int:
        """
        Classifies domain into authority tiers:
        Tier 1: Company primary domain, SEC, official executive sources (w=1.0)
        Tier 2: Major established business/tech press and PR distribution wires (w=0.8)
        Tier 3: Aggregators, forums, and blogs (w=0.5)
        """
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Check if domain matches target company name (e.g., stripe.com for Stripe)
            clean_company = "".join(c for c in target_company.lower() if c.isalnum())
            if clean_company and clean_company in domain:
                return 1

            for pattern in TIER_1_PATTERNS:
                if pattern in domain:
                    return 1

            for t2 in TIER_2_DOMAINS:
                if domain == t2 or domain.endswith("." + t2):
                    return 2

            return 3
        except Exception:
            return 3

    @staticmethod
    def parse_published_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parses publication date string with timezone awareness, converting to UTC."""
        if not date_str:
            return None
        try:
            dt = dateutil.parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            return None

    async def search(
        self,
        query: str,
        category: str,
        target_company: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        t_start: Optional[datetime] = None,
        t_end: Optional[datetime] = None,
        max_results: int = 5
    ) -> Tuple[List[ResearchFinding], List[ResearchFinding]]:
        """
        Executes a Tavily search call with date bounding and post-retrieval validation.
        Returns a tuple: (in_window_findings, undated_findings).
        """
        if not self.config.TAVILY_API_KEY:
            logger.warning("Tavily API key not configured; returning empty search results.")
            return [], []

        payload: Dict[str, Any] = {
            "api_key": self.config.TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "include_raw_content": True,
            "max_results": max_results
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{self.base_url}/search", json=payload)
                if res.status_code != 200:
                    logger.error(f"Tavily search API error HTTP {res.status_code}: {res.text}")
                    return [], []

                data = res.json()
                results = data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to execute Tavily search: {e}")
            return [], []

        in_window_findings: List[ResearchFinding] = []
        undated_findings: List[ResearchFinding] = []

        now_utc = datetime.now(timezone.utc)

        for item in results:
            url = item.get("url", "")
            title = item.get("title", "Untitled Web Result")
            content = item.get("content", "")
            raw_content = item.get("raw_content") or content
            pub_date_str = item.get("published_date")

            # Check deduplication
            if await self.dedup.is_duplicate_or_add(url, content):
                continue

            tier = self.classify_domain_tier(url, target_company)
            parsed_dt = self.parse_published_date(pub_date_str)

            # Matched passage: extract representative passage (first 300 chars of raw content)
            matched_passage = raw_content[:400].strip() if raw_content else content[:400].strip()

            # For static background queries (no t_start / t_end specified), admit directly
            if not t_start or not t_end:
                finding = ResearchFinding(
                    category=category,  # type: ignore
                    title=title,
                    summary=content,
                    source_url=url,
                    source_title=title,
                    published_date=pub_date_str,
                    freshness_days_ago=None,
                    reliability_tier=tier,
                    matched_passage=matched_passage
                )
                in_window_findings.append(finding)
                continue

            # Temporal Gate Validation: [t_start, t_end]
            if parsed_dt is None:
                # Undated record -> route to separate undated bucket
                undated_finding = ResearchFinding(
                    category="undated",
                    title=f"[UNDATED] {title}",
                    summary=content,
                    source_url=url,
                    source_title=title,
                    published_date=None,
                    freshness_days_ago=None,
                    reliability_tier=tier,
                    matched_passage=matched_passage
                )
                undated_findings.append(undated_finding)
                continue

            # Exact Boundary Comparison in UTC
            if parsed_dt > t_end:
                # Future-dated / corrupted metadata -> reject
                logger.info(f"Rejected future-dated search item: {title} ({parsed_dt} > {t_end})")
                continue

            if parsed_dt < t_start:
                # Stale item older than 30 days -> reject from 30-day signals
                logger.info(f"Rejected stale search item: {title} ({parsed_dt} < {t_start})")
                continue

            # In-Window Admittance
            freshness_days = (now_utc - parsed_dt).days
            valid_finding = ResearchFinding(
                category=category,  # type: ignore
                title=title,
                summary=content,
                source_url=url,
                source_title=title,
                published_date=parsed_dt.strftime("%Y-%m-%d"),
                freshness_days_ago=max(0, freshness_days),
                reliability_tier=tier,
                matched_passage=matched_passage
            )
            in_window_findings.append(valid_finding)

        return in_window_findings, undated_findings
