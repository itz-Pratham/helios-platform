"""
Stream Processor Package

Provides real-time event stream processing with Kafka (production) and in-memory (fallback).
Auto-detects which backend to use based on environment.
"""

from .factory import get_stream_processor, init_stream_processor, close_stream_processor
from .base import StreamProcessorBackend, StreamMessage

__all__ = [
    "get_stream_processor",
    "init_stream_processor",
    "close_stream_processor",
    "StreamProcessorBackend",
    "StreamMessage"
]
