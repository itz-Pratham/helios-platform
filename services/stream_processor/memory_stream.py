"""
In-Memory Stream Processor (Fallback)

Provides stream processing without external dependencies.
Uses Python asyncio queues for message passing.
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from collections import defaultdict
import structlog

from .base import StreamProcessorBackend, StreamMessage

logger = structlog.get_logger()


class InMemoryStreamProcessor(StreamProcessorBackend):
    """
    In-memory stream processor for local development/testing.

    Uses asyncio queues to simulate stream topics.
    Supports multiple subscribers per topic (fanout).
    No persistence - messages lost on restart.
    """

    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize in-memory stream processor.

        Args:
            max_queue_size: Maximum messages per topic queue
        """
        self.max_queue_size = max_queue_size

        # Topic queues: topic -> list of (consumer_group, queue)
        self.topics: Dict[str, List[tuple[str, asyncio.Queue]]] = defaultdict(list)

        # Message counters
        self.messages_published = 0
        self.messages_consumed = 0

        # Active consumers
        self.active_consumers: List[asyncio.Task] = []

        # Topic metadata
        self.topic_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self) -> None:
        """Connect to in-memory stream (no-op)."""
        logger.info(
            "inmemory_stream_processor_connected",
            max_queue_size=self.max_queue_size
        )

    async def close(self) -> None:
        """Close in-memory stream and cancel consumers."""
        # Cancel all active consumers
        for task in self.active_consumers:
            task.cancel()

        # Wait for cancellation
        if self.active_consumers:
            await asyncio.gather(*self.active_consumers, return_exceptions=True)

        logger.info(
            "inmemory_stream_processor_closed",
            messages_published=self.messages_published,
            messages_consumed=self.messages_consumed
        )

    async def publish(
        self,
        topic: str,
        key: str,
        value: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Publish message to in-memory topic.

        Args:
            topic: Topic name
            key: Message key
            value: Message payload
            headers: Optional headers
        """
        # Create message
        message = StreamMessage(
            topic=topic,
            key=key,
            value=value,
            timestamp=datetime.utcnow(),
            headers=headers,
            partition=0,
            offset=self.messages_published
        )

        # Send to all subscribers
        if topic in self.topics:
            for group_id, queue in self.topics[topic]:
                try:
                    # Non-blocking put (drop if queue full)
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning(
                        "queue_full_message_dropped",
                        topic=topic,
                        group_id=group_id,
                        queue_size=queue.qsize()
                    )

        self.messages_published += 1

        logger.debug(
            "message_published_memory",
            topic=topic,
            key=key,
            offset=message.offset
        )

    async def subscribe(
        self,
        topics: List[str],
        callback: Callable[[StreamMessage], None],
        group_id: Optional[str] = None
    ) -> None:
        """
        Subscribe to in-memory topics.

        Args:
            topics: List of topics
            callback: Message callback
            group_id: Consumer group ID
        """
        group_id = group_id or f"consumer-{len(self.active_consumers)}"

        # Create queue for this consumer
        queue = asyncio.Queue(maxsize=self.max_queue_size)

        # Register queue for each topic
        for topic in topics:
            self.topics[topic].append((group_id, queue))

        logger.info(
            "subscribed_to_topics_memory",
            topics=topics,
            group_id=group_id
        )

        # Start consumer task
        consumer_task = asyncio.create_task(
            self._consume_messages(queue, callback, group_id)
        )
        self.active_consumers.append(consumer_task)

    async def _consume_messages(
        self,
        queue: asyncio.Queue,
        callback: Callable[[StreamMessage], None],
        group_id: str
    ) -> None:
        """
        Consume messages from queue.

        Args:
            queue: Message queue
            callback: Message callback
            group_id: Consumer group ID
        """
        try:
            while True:
                # Get message from queue
                message = await queue.get()

                # Call callback
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)

                    self.messages_consumed += 1

                    logger.debug(
                        "message_consumed_memory",
                        topic=message.topic,
                        key=message.key,
                        group_id=group_id
                    )
                except Exception as e:
                    logger.error(
                        "message_callback_error",
                        error=str(e),
                        topic=message.topic,
                        group_id=group_id
                    )
                finally:
                    queue.task_done()

        except asyncio.CancelledError:
            logger.info("consumer_cancelled", group_id=group_id)
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get stream processor statistics.

        Returns:
            Dictionary with stats
        """
        # Calculate queue sizes
        queue_sizes = {}
        for topic, subscribers in self.topics.items():
            queue_sizes[topic] = sum(queue.qsize() for _, queue in subscribers)

        return {
            "backend": "in-memory",
            "topics": list(self.topics.keys()),
            "topic_count": len(self.topics),
            "active_consumers": len(self.active_consumers),
            "messages_published": self.messages_published,
            "messages_consumed": self.messages_consumed,
            "queue_sizes": queue_sizes,
            "max_queue_size": self.max_queue_size
        }

    async def create_topic(
        self,
        topic: str,
        partitions: int = 1,
        replication_factor: int = 1
    ) -> None:
        """
        Create in-memory topic (metadata only).

        Args:
            topic: Topic name
            partitions: Number of partitions (ignored)
            replication_factor: Replication factor (ignored)
        """
        if topic not in self.topic_metadata:
            self.topic_metadata[topic] = {
                "partitions": partitions,
                "replication_factor": replication_factor,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(
                "topic_created_memory",
                topic=topic,
                partitions=partitions
            )

    async def delete_topic(self, topic: str) -> None:
        """
        Delete in-memory topic.

        Args:
            topic: Topic name
        """
        if topic in self.topics:
            # Remove all subscribers
            del self.topics[topic]

        if topic in self.topic_metadata:
            del self.topic_metadata[topic]

        logger.info("topic_deleted_memory", topic=topic)

    async def list_topics(self) -> List[str]:
        """
        List all topics.

        Returns:
            List of topic names
        """
        return list(set(list(self.topics.keys()) + list(self.topic_metadata.keys())))

    def get_queue_for_topic(self, topic: str, group_id: str) -> Optional[asyncio.Queue]:
        """
        Get queue for specific topic and consumer group.

        Args:
            topic: Topic name
            group_id: Consumer group ID

        Returns:
            Queue if found, None otherwise
        """
        if topic in self.topics:
            for gid, queue in self.topics[topic]:
                if gid == group_id:
                    return queue
        return None
