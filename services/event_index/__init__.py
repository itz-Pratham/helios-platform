"""
Event Index Package

Provides O(1) event lookups with Redis (production) and SQLite (fallback).
Auto-detects which backend to use based on environment.
"""

from .factory import get_event_index, init_event_index, close_event_index, reset_event_index
from .base import EventIndexBackend

__all__ = [
    "get_event_index",
    "init_event_index",
    "close_event_index",
    "reset_event_index",
    "EventIndexBackend"
]
