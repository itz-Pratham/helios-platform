"""
Abstract base class for Event Index implementations.

Defines the interface that all event index backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class EventIndexBackend(ABC):
    """
    Abstract base class for event indexing.

    Provides O(1) lookup of events by event_id and tracks which sources
    (AWS, GCP, Azure) have reported each event.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to the backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection to the backend."""
        pass

    @abstractmethod
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
            metadata: Additional event metadata (timestamp, payload_hash, etc.)
        """
        pass

    @abstractmethod
    async def get_event_sources(self, event_id: str) -> Set[str]:
        """
        Get all sources that have reported this event.

        Args:
            event_id: Event identifier to lookup

        Returns:
            Set of source names (e.g., {"aws", "gcp"})
        """
        pass

    @abstractmethod
    async def get_event_metadata(self, event_id: str) -> Optional[Dict[str, any]]:
        """
        Get event metadata.

        Args:
            event_id: Event identifier to lookup

        Returns:
            Metadata dictionary or None if not found
        """
        pass

    @abstractmethod
    async def event_exists(self, event_id: str) -> bool:
        """
        Check if event exists in index.

        Args:
            event_id: Event identifier to check

        Returns:
            True if event exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_missing_sources(
        self,
        event_id: str,
        expected_sources: Set[str]
    ) -> Set[str]:
        """
        Get sources that haven't reported this event yet.

        Args:
            event_id: Event identifier
            expected_sources: Set of expected sources (e.g., {"aws", "gcp", "azure"})

        Returns:
            Set of missing sources
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired events (TTL-based cleanup).

        Returns:
            Number of events cleaned up
        """
        pass


class EventMetadata:
    """Event metadata structure."""

    def __init__(
        self,
        event_id: str,
        timestamp: datetime,
        payload_hash: str,
        order_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        amount: Optional[float] = None
    ):
        self.event_id = event_id
        self.timestamp = timestamp
        self.payload_hash = payload_hash
        self.order_id = order_id
        self.customer_id = customer_id
        self.amount = amount

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "payload_hash": self.payload_hash,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "EventMetadata":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload_hash=data["payload_hash"],
            order_id=data.get("order_id"),
            customer_id=data.get("customer_id"),
            amount=data.get("amount")
        )
