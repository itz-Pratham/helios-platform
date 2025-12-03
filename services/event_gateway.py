"""Event Gateway with deduplication and validation."""
from typing import Optional, Dict, Any
from datetime import timedelta
import structlog
import redis.asyncio as redis
from models import IngestEventRequest

logger = structlog.get_logger()


class EventGateway:
    """
    Event Gateway handles:
    - Event deduplication using Redis
    - Event validation
    - Rate limiting (future)
    - Schema validation (future)
    """

    def __init__(self, redis_url: str, dedup_ttl_seconds: int = 86400):
        """
        Initialize Event Gateway.

        Args:
            redis_url: Redis connection URL
            dedup_ttl_seconds: TTL for deduplication keys (default 24 hours)
        """
        self.redis_url = redis_url
        self.dedup_ttl = dedup_ttl_seconds
        self._redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Initialize Redis connection."""
        self._redis_client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("event_gateway_connected", redis_url=self.redis_url)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("event_gateway_closed")

    async def is_duplicate(self, event_id: str) -> bool:
        """
        Check if event has been processed before.

        Args:
            event_id: Unique event identifier

        Returns:
            bool: True if event is a duplicate
        """
        if not self._redis_client:
            raise RuntimeError("EventGateway not connected. Call connect() first.")

        key = f"event:dedup:{event_id}"
        exists = await self._redis_client.exists(key)

        if exists:
            logger.warning("duplicate_event_detected", event_id=event_id)
            return True

        return False

    async def mark_processed(self, event_id: str) -> None:
        """
        Mark event as processed to prevent future duplicates.

        Args:
            event_id: Unique event identifier
        """
        if not self._redis_client:
            raise RuntimeError("EventGateway not connected. Call connect() first.")

        key = f"event:dedup:{event_id}"
        await self._redis_client.setex(
            key,
            self.dedup_ttl,
            "1"
        )
        logger.debug("event_marked_processed", event_id=event_id)

    async def validate_event(self, event: IngestEventRequest) -> tuple[bool, Optional[str]]:
        """
        Validate event structure and business rules.

        Args:
            event: Event to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Basic validation
        if not event.payload:
            return False, "Event payload cannot be empty"

        # Order-related events must have order_id
        if event.event_type.value in ["OrderPlaced", "PaymentProcessed", "InventoryReserved"]:
            if "order_id" not in event.payload:
                return False, f"{event.event_type.value} event must contain order_id"

        # PaymentProcessed must have amount
        if event.event_type.value == "PaymentProcessed":
            if "amount" not in event.payload:
                return False, "PaymentProcessed event must contain amount"
            if not isinstance(event.payload["amount"], (int, float)):
                return False, "Payment amount must be a number"

        # OrderPlaced must have customer_id
        if event.event_type.value == "OrderPlaced":
            if "customer_id" not in event.payload:
                return False, "OrderPlaced event must contain customer_id"

        logger.debug("event_validated", event_id=event.event_type.value)
        return True, None

    async def get_event_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed events from Redis.

        Returns:
            dict: Event processing statistics
        """
        if not self._redis_client:
            raise RuntimeError("EventGateway not connected. Call connect() first.")

        # Count deduplication keys
        cursor = 0
        dedup_count = 0
        pattern = "event:dedup:*"

        while True:
            cursor, keys = await self._redis_client.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            dedup_count += len(keys)
            if cursor == 0:
                break

        return {
            "total_dedup_keys": dedup_count,
            "dedup_ttl_seconds": self.dedup_ttl
        }


# Singleton instance
_gateway_instance: Optional[EventGateway] = None


def get_event_gateway() -> EventGateway:
    """Get singleton EventGateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        from config import settings
        _gateway_instance = EventGateway(
            redis_url=settings.redis_url,
            dedup_ttl_seconds=86400  # 24 hours
        )
    return _gateway_instance
