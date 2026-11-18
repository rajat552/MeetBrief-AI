"""
Unit Tests for Tavily Engine, Domain Tiering & Exact Date Boundary Validation
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from backend.config import Settings
from backend.research.dedup import DeduplicationRegister
from backend.research.tavily_engine import TavilyEngine


def test_domain_tier_classification():
    engine = TavilyEngine()

    # Tier 1: Target company domain
    assert engine.classify_domain_tier("https://stripe.com/docs", target_company="Stripe") == 1
    assert engine.classify_domain_tier("https://investors.databricks.com", target_company="Databricks") == 1
    assert engine.classify_domain_tier("https://www.sec.gov/edgar/data/123", target_company="Apple") == 1
    assert engine.classify_domain_tier("https://linkedin.com/in/john-doe", target_company="Apple") == 1

    # Tier 2: Reputable business/tech press
    assert engine.classify_domain_tier("https://techcrunch.com/2026/11/ai", target_company="Stripe") == 2
    assert engine.classify_domain_tier("https://www.reuters.com/technology/news", target_company="Stripe") == 2
    assert engine.classify_domain_tier("https://www.prnewswire.com/news-releases", target_company="Stripe") == 2

    # Tier 3: Aggregators / Blogs
    assert engine.classify_domain_tier("https://random-blog.net/post", target_company="Stripe") == 3


@pytest.mark.asyncio
async def test_exact_date_boundary_admittance_and_rejection():
    """
    Tests exact boundary conditions in UTC:
    t_start = 2026-10-19T00:00:00Z
    t_end   = 2026-11-18T00:00:00Z
    """
    cfg = Settings(TAVILY_API_KEY="tvly-mock-valid-key")
    dedup = DeduplicationRegister()
    engine = TavilyEngine(cfg=cfg, dedup=dedup)

    t_start = datetime(2026, 10, 19, 0, 0, 0, tzinfo=timezone.utc)
    t_end = datetime(2026, 11, 18, 0, 0, 0, tzinfo=timezone.utc)

    # Mock response containing articles across the boundary spectrum
    mock_tavily_api_response = {
        "results": [
            {
                "url": "https://techcrunch.com/in-window-exact-start",
                "title": "Exact Start Date Article",
                "content": "Published on exact start date.",
                "published_date": "2026-10-19T00:00:00Z"
            },
            {
                "url": "https://techcrunch.com/in-window-exact-end",
                "title": "Exact End Date Article",
                "content": "Published on exact end date.",
                "published_date": "2026-11-18T00:00:00Z"
            },
            {
                "url": "https://reuters.com/stale-before-start",
                "title": "Stale Article",
                "content": "Published 1 second before start.",
                "published_date": "2026-10-18T23:59:59Z"  # 1s before t_start -> MUST BE REJECTED
            },
            {
                "url": "https://bloomberg.com/future-corrupted",
                "title": "Future Dated Article",
                "content": "Published in future.",
                "published_date": "2026-11-18T00:00:01Z"  # 1s after t_end -> MUST BE REJECTED
            },
            {
                "url": "https://forbes.com/undated-item",
                "title": "Undated News Item",
                "content": "No published date metadata.",
                "published_date": None  # Undated -> MUST ROUTE TO undated_signals
            }
        ]
    }

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = mock_tavily_api_response

    with patch("httpx.AsyncClient.post", return_value=mock_res):
        in_window, undated = await engine.search(
            query="Stripe news",
            category="news",
            target_company="Stripe",
            t_start=t_start,
            t_end=t_end
        )

        # In-window must contain EXACTLY the 2 boundary articles
        assert len(in_window) == 2
        in_window_urls = [f.source_url for f in in_window]
        assert "https://techcrunch.com/in-window-exact-start" in in_window_urls
        assert "https://techcrunch.com/in-window-exact-end" in in_window_urls

        # Stale and future must NOT be in in_window
        assert "https://reuters.com/stale-before-start" not in in_window_urls
        assert "https://bloomberg.com/future-corrupted" not in in_window_urls

        # Undated must be routed to separate undated bucket
        assert len(undated) == 1
        assert undated[0].source_url == "https://forbes.com/undated-item"
        assert undated[0].category == "undated"
