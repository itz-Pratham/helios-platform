"""
Stream Processor Factory

Auto-detects which backend to use based on environment configuration.
Falls back to in-memory if Kafka is unavailable.
"""

import os
from typing import Optional
import structlog

from .base import StreamProcessorBackend
from .kafka_stream import KafkaStreamProcessor, KAFKA_AVAILABLE
from .memory_stream import InMemoryStreamProcessor

logger = structlog.get_logger()

# Singleton instance
_stream_processor: Optional[StreamProcessorBackend] = None


def get_stream_processor() -> StreamProcessorBackend:
    """
    Get stream processor instance (singleton).

    Auto-detects backend:
    1. If KAFKA_BOOTSTRAP_SERVERS set → Use KafkaStreamProcessor
    2. Otherwise → Use InMemoryStreamProcessor (fallback)

    Returns:
        StreamProcessorBackend instance
    """
    global _stream_processor

    if _stream_processor is not None:
        return _stream_processor

    # Check for Kafka
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

    if kafka_servers and KAFKA_AVAILABLE:
        try:
            _stream_processor = KafkaStreamProcessor(
                bootstrap_servers=kafka_servers,
                client_id=os.getenv("KAFKA_CLIENT_ID", "helios-stream-processor")
            )
            logger.info(
                "stream_processor_backend_selected",
                backend="kafka",
                servers=kafka_servers
            )
        except Exception as e:
            logger.warning(
                "kafka_stream_processor_failed_fallback_to_memory",
                error=str(e)
            )
            _stream_processor = None

    # Fallback to in-memory
    if _stream_processor is None:
        max_queue_size = int(os.getenv("STREAM_MAX_QUEUE_SIZE", "10000"))
        _stream_processor = InMemoryStreamProcessor(max_queue_size=max_queue_size)
        logger.info(
            "stream_processor_backend_selected",
            backend="in-memory",
            max_queue_size=max_queue_size,
            reason="Kafka unavailable or not configured"
        )

    return _stream_processor


async def init_stream_processor() -> StreamProcessorBackend:
    """
    Initialize stream processor (call this on app startup).

    Returns:
        Initialized StreamProcessorBackend instance
    """
    processor = get_stream_processor()
    await processor.connect()
    logger.info("stream_processor_initialized")
    return processor


async def close_stream_processor() -> None:
    """Close stream processor connection (call this on app shutdown)."""
    global _stream_processor

    if _stream_processor is not None:
        await _stream_processor.close()
        _stream_processor = None
        logger.info("stream_processor_closed")


def reset_stream_processor() -> None:
    """Reset singleton (for testing only)."""
    global _stream_processor
    _stream_processor = None
