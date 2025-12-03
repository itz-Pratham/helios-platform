"""
Event Index Factory

Auto-detects which backend to use based on environment configuration.
Falls back to SQLite if Redis is unavailable.
"""

import os
from typing import Optional
import structlog

from .base import EventIndexBackend
from .redis_index import RedisEventIndex
from .sqlite_index import SQLiteEventIndex

logger = structlog.get_logger()

# Singleton instance
_event_index: Optional[EventIndexBackend] = None


def get_event_index() -> EventIndexBackend:
    """
    Get event index instance (singleton).

    Auto-detects backend:
    1. If REDIS_URL set → Use RedisEventIndex
    2. Otherwise → Use SQLiteEventIndex (fallback)

    Returns:
        EventIndexBackend instance
    """
    global _event_index

    if _event_index is not None:
        return _event_index

    # Check for Redis
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        try:
            _event_index = RedisEventIndex(
                redis_url=redis_url,
                ttl_seconds=int(os.getenv("EVENT_INDEX_TTL", "86400"))
            )
            logger.info(
                "event_index_backend_selected",
                backend="redis",
                url=redis_url
            )
        except Exception as e:
            logger.warning(
                "redis_event_index_failed_fallback_to_sqlite",
                error=str(e)
            )
            _event_index = None

    # Fallback to SQLite
    if _event_index is None:
        db_path = os.getenv("EVENT_INDEX_DB_PATH", "data/event_index.db")
        _event_index = SQLiteEventIndex(
            db_path=db_path,
            ttl_seconds=int(os.getenv("EVENT_INDEX_TTL", "86400"))
        )
        logger.info(
            "event_index_backend_selected",
            backend="sqlite",
            db_path=db_path,
            reason="Redis unavailable or not configured"
        )

    return _event_index


async def init_event_index() -> EventIndexBackend:
    """
    Initialize event index (call this on app startup).

    Returns:
        Initialized EventIndexBackend instance
    """
    index = get_event_index()
    await index.connect()
    logger.info("event_index_initialized")
    return index


async def close_event_index() -> None:
    """Close event index connection (call this on app shutdown)."""
    global _event_index

    if _event_index is not None:
        await _event_index.close()
        _event_index = None
        logger.info("event_index_closed")


def reset_event_index() -> None:
    """Reset singleton (for testing only)."""
    global _event_index
    _event_index = None
