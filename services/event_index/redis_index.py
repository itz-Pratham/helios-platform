"""
Redis-based Event Index (Production)

Provides O(1) event lookups using Redis data structures.
Uses Redis SETs for sources and HASHes for metadata.
"""

import json
import redis.asyncio as aioredis
from typing import Set, Dict, Optional
from datetime import datetime
import structlog

from .base import EventIndexBackend, EventMetadata

logger = structlog.get_logger()


class RedisEventIndex(EventIndexBackend):
    """
    Redis-based event index for production use.

    Data Structure:
        evt:{event_id}:src → SET ["aws", "gcp", "azure"]
        evt:{event_id}:meta → HASH {timestamp, payload_hash, order_id, ...}
        evt:{event_id}:ttl → EXPIRE 86400  # 24h TTL

    Performance: O(1) for all operations
    """

    def __init__(self, redis_url: str, ttl_seconds: int = 86400):
        """
        Initialize Redis event index.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Time-to-live for events (default 24 hours)
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            logger.info(
                "redis_event_index_connected",
                url=self.redis_url,
                ttl_seconds=self.ttl_seconds
            )
        except Exception as e:
            logger.error(
                "redis_event_index_connection_failed",
                url=self.redis_url,
                error=str(e)
            )
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("redis_event_index_closed")

    def _sources_key(self, event_id: str) -> str:
        """Get Redis key for event sources SET."""
        return f"evt:{event_id}:src"

    def _metadata_key(self, event_id: str) -> str:
        """Get Redis key for event metadata HASH."""
        return f"evt:{event_id}:meta"

    async def index_event(
        self,
        event_id: str,
        source: str,
        metadata: Dict[str, any]
    ) -> None:
        """
        Index an event from a specific source.

        Args:
            event_id: Unique event identifier
            source: Source system (aws, gcp, azure)
            metadata: Event metadata
        """
        sources_key = self._sources_key(event_id)
        meta_key = self._metadata_key(event_id)

        # Use pipeline for atomic operations
        async with self.redis.pipeline(transaction=True) as pipe:
            # Add source to SET
            pipe.sadd(sources_key, source)
            pipe.expire(sources_key, self.ttl_seconds)

            # Store metadata as HASH
            # Convert datetime objects to ISO format
            metadata_serialized = {}
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    metadata_serialized[key] = value.isoformat()
                elif value is not None:
                    metadata_serialized[key] = str(value)

            if metadata_serialized:
                pipe.hset(meta_key, mapping=metadata_serialized)
                pipe.expire(meta_key, self.ttl_seconds)

            await pipe.execute()

        logger.debug(
            "event_indexed",
            event_id=event_id,
            source=source,
            ttl=self.ttl_seconds
        )

    async def get_event_sources(self, event_id: str) -> Set[str]:
        """
        Get all sources that have reported this event.

        Args:
            event_id: Event identifier

        Returns:
            Set of source names
        """
        sources_key = self._sources_key(event_id)
        sources = await self.redis.smembers(sources_key)
        return set(sources) if sources else set()

    async def get_event_metadata(self, event_id: str) -> Optional[Dict[str, any]]:
        """
        Get event metadata.

        Args:
            event_id: Event identifier

        Returns:
            Metadata dictionary or None
        """
        meta_key = self._metadata_key(event_id)
        metadata = await self.redis.hgetall(meta_key)

        if not metadata:
            return None

        # Convert timestamp back to datetime if present
        if "timestamp" in metadata:
            try:
                metadata["timestamp"] = datetime.fromisoformat(metadata["timestamp"])
            except (ValueError, TypeError):
                pass

        # Convert amount to float if present
        if "amount" in metadata:
            try:
                metadata["amount"] = float(metadata["amount"])
            except (ValueError, TypeError):
                pass

        return metadata

    async def event_exists(self, event_id: str) -> bool:
        """
        Check if event exists in index.

        Args:
            event_id: Event identifier

        Returns:
            True if event exists
        """
        sources_key = self._sources_key(event_id)
        exists = await self.redis.exists(sources_key)
        return bool(exists)

    async def get_missing_sources(
        self,
        event_id: str,
        expected_sources: Set[str]
    ) -> Set[str]:
        """
        Get sources that haven't reported this event.

        Args:
            event_id: Event identifier
            expected_sources: Expected sources

        Returns:
            Set of missing sources
        """
        actual_sources = await self.get_event_sources(event_id)
        return expected_sources - actual_sources

    async def cleanup_expired(self) -> int:
        """
        Cleanup expired events.

        Note: Redis handles TTL automatically via EXPIRE,
        so this is a no-op for Redis backend.

        Returns:
            0 (Redis auto-expires)
        """
        # Redis handles expiration automatically
        return 0

    async def get_stats(self) -> Dict[str, any]:
        """
        Get index statistics.

        Returns:
            Dictionary with stats (event count, memory usage, etc.)
        """
        # Count events (approximate - counts source keys)
        cursor = 0
        event_count = 0

        # Scan for evt:*:src keys
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match="evt:*:src",
                count=1000
            )
            event_count += len(keys)

            if cursor == 0:
                break

        # Get memory usage
        info = await self.redis.info("memory")
        memory_used_mb = info.get("used_memory", 0) / (1024 * 1024)

        return {
            "backend": "redis",
            "event_count": event_count,
            "memory_used_mb": round(memory_used_mb, 2),
            "ttl_seconds": self.ttl_seconds
        }
