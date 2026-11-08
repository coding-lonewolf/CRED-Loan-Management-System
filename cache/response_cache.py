"""In-memory response caching for grounded policy queries.

Task 16 requirements:
- In-memory cache keyed by normalized query text.
- Normalization:
    def normalize_query(query: str) -> str:
        return " ".join(query.lower().split())
- Check cache before RAG retrieval or generation.
- Return cached grounded response on cache hit without redundant generation or tool invocation.
- Execute retrieval/generation on cache miss and store result in cache.
- Track hit/miss counters and timing statistics (before/after comparison).
- Critical safety rule: Cache ONLY general grounded policy responses.
  DO NOT cache personalized application-status responses (e.g. containing CL-XXXXX
  or query_type="loan_status"), which always require real-time fresh lookups.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


def normalize_query(query: str) -> str:
    """Normalize query text for deterministic cache key generation.

    Lowercases, collapses multiple consecutive whitespace characters,
    and strips leading/trailing punctuation and whitespace.
    """
    if not query:
        return ""
    # Strip leading/trailing whitespace
    text = query.strip().lower()
    # Remove trailing punctuation often varying across user inputs (? . !)
    text = re.sub(r"[?!.,;]+$", "", text).strip()
    # Collapse multiple spaces into a single space
    return " ".join(text.split())


@dataclass
class CacheEntry:
    """Represents a cached response along with metadata and timestamps."""

    key: str
    response: Any
    created_at: float = field(default_factory=time.time)
    hit_count: int = 0
    query_type: str = "policy"
    original_duration_ms: float = 0.0


class ResponseCache:
    """Thread-safe in-memory response cache with hit/miss tracking and timing metrics."""

    def __init__(self, max_size: int = 500) -> None:
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self.hits: int = 0
        self.misses: int = 0
        self.bypasses: int = 0
        self.total_time_saved_ms: float = 0.0

    def is_cacheable(self, query: str, query_type: Optional[str] = None) -> bool:
        """Determine whether a query qualifies for response caching.

        Returns False for loan status checks, specific application IDs (CL-XXXXX),
        or dynamic customer inquiries.
        """
        if query_type == "loan_status":
            return False

        # Exclude queries containing application IDs (CL-XXXXX)
        if re.search(r"\bCL-\d{5}\b", query, re.IGNORECASE):
            return False

        # Exclude explicit status lookup phrases
        lower_q = query.lower()
        if "my application" in lower_q or "application status" in lower_q:
            return False

        return True

    def get(self, query: str, query_type: Optional[str] = "policy") -> Tuple[Optional[Any], bool]:
        """Look up a normalized query in the cache.

        Args:
            query: Raw or sanitized user query.
            query_type: Classification of the query ("policy", "loan_status", etc.)

        Returns:
            Tuple of (cached_response, is_hit).
            If the query is non-cacheable, returns (None, False) and records a bypass.
        """
        if not self.is_cacheable(query, query_type):
            self.bypasses += 1
            return None, False

        key = normalize_query(query)
        if key in self._cache:
            entry = self._cache[key]
            entry.hit_count += 1
            self.hits += 1
            # Add estimated saved duration from the original execution
            self.total_time_saved_ms += entry.original_duration_ms
            return entry.response, True

        self.misses += 1
        return None, False

    def put(
        self,
        query: str,
        response: Any,
        query_type: str = "policy",
        execution_duration_ms: float = 0.0,
    ) -> bool:
        """Store a grounded generation response in the cache.

        Args:
            query: Raw or sanitized query text.
            response: Response object or dictionary to store.
            query_type: Classification of the query.
            execution_duration_ms: Time taken to compute the response on miss.

        Returns:
            True if stored; False if rejected due to non-cacheability.
        """
        if not self.is_cacheable(query, query_type):
            return False

        # Evict oldest entry if capacity is reached
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]

        key = normalize_query(query)
        self._cache[key] = CacheEntry(
            key=key,
            response=response,
            query_type=query_type,
            original_duration_ms=execution_duration_ms,
        )
        return True

    def clear(self) -> None:
        """Reset the cache and its statistics."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        self.bypasses = 0
        self.total_time_saved_ms = 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Return cache health and performance statistics."""
        total_evaluations = self.hits + self.misses
        hit_rate = (self.hits / total_evaluations * 100.0) if total_evaluations > 0 else 0.0
        return {
            "cached_entries_count": len(self._cache),
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "cache_bypasses": self.bypasses,
            "hit_rate_pct": round(hit_rate, 2),
            "total_time_saved_ms": round(self.total_time_saved_ms, 2),
        }


# Global singleton instance for application runtime
response_cache = ResponseCache()

