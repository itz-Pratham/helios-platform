"""Kafka producer for event streaming (mock implementation for now)."""
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
import json

logger = structlog.get_logger()


class KafkaProducer:
    """
    Mock Kafka Producer for event streaming.
    In production, this will use confluent-kafka or aiokafka.

    For now, it logs events that would be sent to Kafka.
    """

    def __init__(self, bootstrap_servers: str, topic_prefix: str = "helios"):
        """
        Initialize Kafka Producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic_prefix: Prefix for Kafka topics
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = topic_prefix
        self._connected = False

    async def connect(self) -> None:
        """Initialize Kafka connection (mock)."""
        logger.info(
            "kafka_producer_connected_mock",
            bootstrap_servers=self.bootstrap_servers,
            note="Using mock producer - no actual Kafka connection"
        )
        self._connected = True

    async def close(self) -> None:
        """Close Kafka connection (mock)."""
        logger.info("kafka_producer_closed_mock")
        self._connected = False

    async def produce(
        self,
        topic_suffix: str,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Produce event to Kafka topic (mock).

        Args:
            topic_suffix: Topic suffix (e.g., 'events.orders', 'events.payments')
            event_id: Unique event identifier
            event_type: Event type
            payload: Event payload
            metadata: Event metadata
        """
        if not self._connected:
            raise RuntimeError("KafkaProducer not connected. Call connect() first.")

        topic = f"{self.topic_prefix}.{topic_suffix}"

        # Mock Kafka message
        kafka_message = {
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "metadata": metadata or {},
            "produced_at": datetime.utcnow().isoformat(),
        }

        # In production, this would be:
        # await self.producer.send(topic, value=kafka_message)

        logger.info(
            "kafka_event_produced_mock",
            topic=topic,
            event_id=event_id,
            event_type=event_type,
            order_id=payload.get("order_id"),
            message_size=len(json.dumps(kafka_message)),
        )

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get producer metrics (mock).

        Returns:
            dict: Producer metrics
        """
        return {
            "connected": self._connected,
            "bootstrap_servers": self.bootstrap_servers,
            "topic_prefix": self.topic_prefix,
            "type": "mock",
        }


# Singleton instance
_producer_instance: Optional[KafkaProducer] = None


def get_kafka_producer() -> KafkaProducer:
    """Get singleton KafkaProducer instance."""
    global _producer_instance
    if _producer_instance is None:
        from config import settings
        _producer_instance = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            topic_prefix="helios"
        )
    return _producer_instance
