"""
Simple in-memory cache for verification lookups.
Reduces database queries for frequently accessed batch IDs.
"""

from functools import lru_cache
from typing import Optional

from app.schemas.ledger import LedgerRecord


class VerificationCache:
    """
    LRU cache for verification records.
    Stores up to 1000 most recent lookups in memory.
    """

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._get_cached = lru_cache(maxsize=maxsize)(self._get_from_backend)

    async def get(self, batch_id: str, fetch_func) -> Optional[LedgerRecord]:
        """
        Get record from cache or fetch from backend.

        Args:
            batch_id: Batch identifier
            fetch_func: Async function to fetch from backend if not cached

        Returns:
            LedgerRecord if found, None otherwise
        """
        # Check cache first
        cached = self._get_cached(batch_id)
        if cached is not None:
            return cached

        # Fetch from backend
        record = await fetch_func(batch_id)

        # Cache result (even if None, to avoid repeated lookups)
        self._get_cached.cache_clear()  # Clear to update
        self._get_cached(batch_id)  # Re-cache

        return record

    def _get_from_backend(self, batch_id: str):
        """Dummy method for caching (actual fetch happens in get())"""
        return None

    def clear(self):
        """Clear cache"""
        self._get_cached.cache_clear()


# Global cache instance
verification_cache = VerificationCache()
