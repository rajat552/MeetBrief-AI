"""
Unit Tests for Concurrency-Safe Deduplication Register
"""

import asyncio
import pytest
from backend.research.dedup import DeduplicationRegister


@pytest.mark.asyncio
async def test_url_normalization():
    reg = DeduplicationRegister()
    url1 = "https://WWW.Stripe.com/news/agentic-payments/?utm_source=twitter&ref=blog#heading"
    url2 = "https://stripe.com/news/agentic-payments"

    # Both should normalize to the same canonical form
    assert reg.normalize_url(url1) == "https://stripe.com/news/agentic-payments"
    assert reg.normalize_url(url2) == "https://stripe.com/news/agentic-payments"


@pytest.mark.asyncio
async def test_deduplication_detection():
    reg = DeduplicationRegister()
    url = "https://stripe.com/news/feature-drop"

    # First attempt: not a duplicate -> returns False
    is_dup1 = await reg.is_duplicate_or_add(url, snippet="New feature released today.")
    assert is_dup1 is False

    # Second attempt with same canonical URL: duplicate -> returns True
    is_dup2 = await reg.is_duplicate_or_add("https://stripe.com/news/feature-drop?utm_medium=email")
    assert is_dup2 is True


@pytest.mark.asyncio
async def test_concurrency_safety():
    reg = DeduplicationRegister()
    url = "https://databricks.com/announcement"

    # Run 20 concurrent tasks attempting to register the exact same URL
    results = await asyncio.gather(*(reg.is_duplicate_or_add(url) for _ in range(20)))

    # Exactly ONE task must succeed in registering (False), the other 19 must detect duplicate (True)
    assert results.count(False) == 1
    assert results.count(True) == 19
