"""
Stream Processor Base Classes

Abstract interface for stream processing backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class StreamMessage:
    """
    Stream message data structure.

    Attributes:
        topic: Stream topic/channel
        key: Message key (for partitioning)
        value: Message payload
        timestamp: Message timestamp
        headers: Optional message headers
        partition: Partition number (if applicable)
        offset: Message offset (if applicable)
    """
    topic: str
    key: str
    value: Dict[str, Any]
    timestamp: datetime
    headers: Optional[Dict[str, str]] = None
    partition: Optional[int] = None
    offset: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "headers": self.headers,
            "partition": self.partition,
            "offset": self.offset
        }


class StreamProcessorBackend(ABC):
    """
    Abstract base class for stream processing backends.

    Implementations:
    - KafkaStreamProcessor: Production Kafka backend
    - InMemoryStreamProcessor: Fallback in-memory backend
    """

    @abstractmethod
    async def connect(self) -> None:
        """Connect to stream backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close stream backend connection."""
        pass

    @abstractmethod
    async def publish(
        self,
        topic: str,
        key: str,
        value: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Publish message to stream.

        Args:
            topic: Stream topic
            key: Message key (for partitioning)
            value: Message payload
            headers: Optional message headers
        """
        pass

    @abstractmethod
    async def subscribe(
        self,
        topics: List[str],
        callback: Callable[[StreamMessage], None],
        group_id: Optional[str] = None
    ) -> None:
        """
        Subscribe to stream topics.

        Args:
            topics: List of topics to subscribe to
            callback: Callback function for each message
            group_id: Consumer group ID (for load balancing)
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get stream processor statistics.

        Returns:
            Dictionary with stats
        """
        pass

    @abstractmethod
    async def create_topic(
        self,
        topic: str,
        partitions: int = 1,
        replication_factor: int = 1
    ) -> None:
        """
        Create stream topic.

        Args:
            topic: Topic name
            partitions: Number of partitions
            replication_factor: Replication factor
        """
        pass

    @abstractmethod
    async def delete_topic(self, topic: str) -> None:
        """
        Delete stream topic.

        Args:
            topic: Topic name
        """
        pass

    @abstractmethod
    async def list_topics(self) -> List[str]:
        """
        List all topics.

        Returns:
            List of topic names
        """
        pass
