"""
Kafka Stream Processor (Production)

Provides production-grade stream processing with Apache Kafka.
Uses aiokafka for async Kafka operations.
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json
import structlog

from .base import StreamProcessorBackend, StreamMessage

logger = structlog.get_logger()

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("aiokafka_not_available")


class KafkaStreamProcessor(StreamProcessorBackend):
    """
    Kafka-based stream processor for production.

    Features:
    - High-throughput message processing
    - Persistent message storage
    - Consumer groups for load balancing
    - Automatic partition rebalancing
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "helios-stream-processor"
    ):
        """
        Initialize Kafka stream processor.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            client_id: Kafka client ID
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("aiokafka is required for Kafka stream processor")

        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id

        # Kafka clients
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: List[AIOKafkaConsumer] = []
        self.admin_client: Optional[AIOKafkaAdminClient] = None

        # Stats
        self.messages_published = 0
        self.messages_consumed = 0

        # Active consumer tasks
        self.consumer_tasks: List[asyncio.Task] = []

    async def connect(self) -> None:
        """Connect to Kafka."""
        try:
            # Initialize producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()

            # Initialize admin client
            self.admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-admin"
            )
            await self.admin_client.start()

            logger.info(
                "kafka_stream_processor_connected",
                bootstrap_servers=self.bootstrap_servers
            )

        except Exception as e:
            logger.error(
                "kafka_connection_failed",
                error=str(e),
                bootstrap_servers=self.bootstrap_servers
            )
            raise

    async def close(self) -> None:
        """Close Kafka connections."""
        # Cancel consumer tasks
        for task in self.consumer_tasks:
            task.cancel()

        if self.consumer_tasks:
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)

        # Stop consumers
        for consumer in self.consumers:
            await consumer.stop()

        # Stop producer
        if self.producer:
            await self.producer.stop()

        # Stop admin client
        if self.admin_client:
            await self.admin_client.close()

        logger.info(
            "kafka_stream_processor_closed",
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
        Publish message to Kafka topic.

        Args:
            topic: Kafka topic
            key: Message key
            value: Message payload
            headers: Optional headers
        """
        if not self.producer:
            raise RuntimeError("Producer not initialized. Call connect() first.")

        try:
            # Convert headers to Kafka format
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode('utf-8')) for k, v in headers.items()
                ]

            # Send message
            await self.producer.send(
                topic=topic,
                key=key,
                value=value,
                headers=kafka_headers
            )

            self.messages_published += 1

            logger.debug(
                "message_published_kafka",
                topic=topic,
                key=key
            )

        except Exception as e:
            logger.error(
                "kafka_publish_failed",
                error=str(e),
                topic=topic,
                key=key
            )
            raise

    async def subscribe(
        self,
        topics: List[str],
        callback: Callable[[StreamMessage], None],
        group_id: Optional[str] = None
    ) -> None:
        """
        Subscribe to Kafka topics.

        Args:
            topics: List of topics
            callback: Message callback
            group_id: Consumer group ID
        """
        group_id = group_id or f"{self.client_id}-consumer"

        try:
            # Create consumer
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )

            await consumer.start()
            self.consumers.append(consumer)

            logger.info(
                "subscribed_to_topics_kafka",
                topics=topics,
                group_id=group_id
            )

            # Start consumer task
            task = asyncio.create_task(
                self._consume_messages(consumer, callback, group_id)
            )
            self.consumer_tasks.append(task)

        except Exception as e:
            logger.error(
                "kafka_subscribe_failed",
                error=str(e),
                topics=topics
            )
            raise

    async def _consume_messages(
        self,
        consumer: AIOKafkaConsumer,
        callback: Callable[[StreamMessage], None],
        group_id: str
    ) -> None:
        """
        Consume messages from Kafka.

        Args:
            consumer: Kafka consumer
            callback: Message callback
            group_id: Consumer group ID
        """
        try:
            async for msg in consumer:
                # Convert to StreamMessage
                headers = {}
                if msg.headers:
                    headers = {k: v.decode('utf-8') for k, v in msg.headers}

                message = StreamMessage(
                    topic=msg.topic,
                    key=msg.key,
                    value=msg.value,
                    timestamp=datetime.fromtimestamp(msg.timestamp / 1000),
                    headers=headers,
                    partition=msg.partition,
                    offset=msg.offset
                )

                # Call callback
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)

                    self.messages_consumed += 1

                    logger.debug(
                        "message_consumed_kafka",
                        topic=msg.topic,
                        partition=msg.partition,
                        offset=msg.offset,
                        group_id=group_id
                    )

                except Exception as e:
                    logger.error(
                        "message_callback_error",
                        error=str(e),
                        topic=msg.topic,
                        group_id=group_id
                    )

        except asyncio.CancelledError:
            logger.info("kafka_consumer_cancelled", group_id=group_id)
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get Kafka statistics.

        Returns:
            Dictionary with stats
        """
        topics = await self.list_topics()

        return {
            "backend": "kafka",
            "bootstrap_servers": self.bootstrap_servers,
            "topics": topics,
            "topic_count": len(topics),
            "active_consumers": len(self.consumers),
            "messages_published": self.messages_published,
            "messages_consumed": self.messages_consumed
        }

    async def create_topic(
        self,
        topic: str,
        partitions: int = 1,
        replication_factor: int = 1
    ) -> None:
        """
        Create Kafka topic.

        Args:
            topic: Topic name
            partitions: Number of partitions
            replication_factor: Replication factor
        """
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized. Call connect() first.")

        try:
            new_topic = NewTopic(
                name=topic,
                num_partitions=partitions,
                replication_factor=replication_factor
            )

            await self.admin_client.create_topics([new_topic])

            logger.info(
                "topic_created_kafka",
                topic=topic,
                partitions=partitions,
                replication_factor=replication_factor
            )

        except Exception as e:
            logger.error(
                "kafka_create_topic_failed",
                error=str(e),
                topic=topic
            )
            raise

    async def delete_topic(self, topic: str) -> None:
        """
        Delete Kafka topic.

        Args:
            topic: Topic name
        """
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized. Call connect() first.")

        try:
            await self.admin_client.delete_topics([topic])
            logger.info("topic_deleted_kafka", topic=topic)

        except Exception as e:
            logger.error(
                "kafka_delete_topic_failed",
                error=str(e),
                topic=topic
            )
            raise

    async def list_topics(self) -> List[str]:
        """
        List all Kafka topics.

        Returns:
            List of topic names
        """
        if not self.admin_client:
            raise RuntimeError("Admin client not initialized. Call connect() first.")

        try:
            metadata = await self.admin_client.list_topics()
            # Filter out internal topics
            return [t for t in metadata if not t.startswith('_')]

        except Exception as e:
            logger.error("kafka_list_topics_failed", error=str(e))
            raise
