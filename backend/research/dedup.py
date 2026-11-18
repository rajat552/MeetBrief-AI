"""
MeetBrief AI — Concurrency-Safe Deduplication Register
"""

import asyncio
import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from typing import Set


class DeduplicationRegister:
    """
    Thread-safe and async-safe deduplication register.
    Prevents duplicate URL fetching and redundant finding ingestion across research branches.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._seen_url_hashes: Set[str] = set()
        self._seen_snippet_hashes: Set[str] = set()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Strips query tracking parameters, fragment, and trailing slashes."""
        try:
            parsed = urlparse(url.strip())
            # Strip common tracking query parameters
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items()
                if not k.lower().startswith("utm_") and k.lower() not in ("ref", "source", "fbclid", "gclid")
            }
            clean_query = urlencode(filtered_params, doseq=True)
            path = parsed.path.rstrip("/")
            
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            
            clean_url = urlunparse((
                parsed.scheme.lower(),
                netloc,
                path,
                "",  # params
                clean_query,
                ""   # fragment
            ))
            return clean_url
        except Exception:
            return url.strip().lower().rstrip("/")

    @staticmethod
    def hash_snippet(snippet: str) -> str:
        """Generates normalized hash from the first 128 alphanumeric characters."""
        normalized = re.sub(r"[^a-zA-Z0-9]", "", snippet.lower())[:128]
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def is_duplicate_or_add(self, url: str, snippet: str = "") -> bool:
        """
        Atomically checks if a URL or snippet has been processed.
        If not seen, registers it and returns False. If seen, returns True.
        """
        norm_url = self.normalize_url(url)
        url_hash = hashlib.sha256(norm_url.encode("utf-8")).hexdigest()
        snip_hash = self.hash_snippet(snippet) if snippet else None

        async with self._lock:
            if url_hash in self._seen_url_hashes:
                return True
            if snip_hash and snip_hash in self._seen_snippet_hashes:
                return True

            self._seen_url_hashes.add(url_hash)
            if snip_hash:
                self._seen_snippet_hashes.add(snip_hash)
            return False

    async def clear(self) -> None:
        """Resets the register."""
        async with self._lock:
            self._seen_url_hashes.clear()
            self._seen_snippet_hashes.clear()
