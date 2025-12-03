"""
Bloom Filter for Space-Efficient Missing Event Detection

Uses probabilistic data structure for fast membership testing.
Memory: ~1.2MB per 100k events (0.01% false positive rate)
Performance: O(k) where k = number of hash functions (typically 7)
"""

import hashlib
import math
from typing import List, Optional
import structlog

logger = structlog.get_logger()


class BloomFilter:
    """
    Bloom filter for probabilistic set membership testing.

    Use case: Quickly check if event_id has been seen before
    Trade-off: False positives possible, false negatives impossible

    Example:
        bloom = BloomFilter(expected_items=100000, false_positive_rate=0.01)
        bloom.add("event-123")
        bloom.contains("event-123")  # True
        bloom.contains("event-999")  # False (probably)
    """

    def __init__(
        self,
        expected_items: int = 100000,
        false_positive_rate: float = 0.01
    ):
        """
        Initialize Bloom filter.

        Args:
            expected_items: Expected number of items to store
            false_positive_rate: Target false positive rate (0.01 = 1%)
        """
        self.expected_items = expected_items
        self.false_positive_rate = false_positive_rate

        # Calculate optimal bit array size
        self.bit_size = self._calculate_bit_size(expected_items, false_positive_rate)

        # Calculate optimal number of hash functions
        self.num_hashes = self._calculate_num_hashes(self.bit_size, expected_items)

        # Initialize bit array
        self.bit_array = [False] * self.bit_size

        # Track items added
        self.items_added = 0

        logger.info(
            "bloom_filter_initialized",
            expected_items=expected_items,
            false_positive_rate=false_positive_rate,
            bit_size=self.bit_size,
            num_hashes=self.num_hashes,
            memory_mb=round(self.bit_size / 8 / 1024 / 1024, 2)
        )

    @staticmethod
    def _calculate_bit_size(n: int, p: float) -> int:
        """
        Calculate optimal bit array size.

        Formula: m = -(n * ln(p)) / (ln(2)^2)

        Args:
            n: Expected number of items
            p: Target false positive rate

        Returns:
            Optimal bit array size
        """
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)

    @staticmethod
    def _calculate_num_hashes(m: int, n: int) -> int:
        """
        Calculate optimal number of hash functions.

        Formula: k = (m/n) * ln(2)

        Args:
            m: Bit array size
            n: Expected number of items

        Returns:
            Optimal number of hash functions
        """
        k = (m / n) * math.log(2)
        return max(1, int(k))

    def _hash(self, item: str, seed: int) -> int:
        """
        Generate hash for item with seed.

        Uses SHA256 with seed for deterministic hashing.

        Args:
            item: Item to hash
            seed: Hash function seed

        Returns:
            Hash value modulo bit_size
        """
        # Combine item and seed
        data = f"{item}:{seed}".encode('utf-8')

        # Generate hash
        hash_value = int(hashlib.sha256(data).hexdigest(), 16)

        # Map to bit array index
        return hash_value % self.bit_size

    def add(self, item: str) -> None:
        """
        Add item to Bloom filter.

        Args:
            item: Item to add (typically event_id)
        """
        for i in range(self.num_hashes):
            index = self._hash(item, i)
            self.bit_array[index] = True

        self.items_added += 1

        logger.debug(
            "bloom_filter_item_added",
            item=item,
            items_added=self.items_added
        )

    def contains(self, item: str) -> bool:
        """
        Check if item might be in set.

        Args:
            item: Item to check (typically event_id)

        Returns:
            True if item might be in set (possible false positive)
            False if item definitely not in set (no false negatives)
        """
        for i in range(self.num_hashes):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False

        return True

    def get_false_positive_rate(self) -> float:
        """
        Calculate current false positive rate based on items added.

        Formula: (1 - e^(-kn/m))^k

        Returns:
            Current false positive rate
        """
        if self.items_added == 0:
            return 0.0

        m = self.bit_size
        n = self.items_added
        k = self.num_hashes

        # Calculate actual false positive rate
        exponent = -k * n / m
        rate = (1 - math.exp(exponent)) ** k

        return rate

    def get_stats(self) -> dict:
        """
        Get Bloom filter statistics.

        Returns:
            Dictionary with stats
        """
        bits_set = sum(self.bit_array)
        fill_ratio = bits_set / self.bit_size

        return {
            "expected_items": self.expected_items,
            "items_added": self.items_added,
            "bit_size": self.bit_size,
            "bits_set": bits_set,
            "fill_ratio": round(fill_ratio, 4),
            "num_hashes": self.num_hashes,
            "target_fp_rate": self.false_positive_rate,
            "actual_fp_rate": round(self.get_false_positive_rate(), 6),
            "memory_mb": round(self.bit_size / 8 / 1024 / 1024, 2),
            "overloaded": self.items_added > self.expected_items
        }

    def clear(self) -> None:
        """Clear all items from Bloom filter."""
        self.bit_array = [False] * self.bit_size
        self.items_added = 0
        logger.info("bloom_filter_cleared")


class TimeWindowedBloomFilter:
    """
    Time-windowed Bloom filter for TTL-based event tracking.

    Uses multiple Bloom filters in a sliding window.
    Each window represents a time period (e.g., 1 hour).
    Old windows are automatically discarded.

    Use case: Track events seen in last N hours
    """

    def __init__(
        self,
        window_count: int = 24,
        items_per_window: int = 10000,
        false_positive_rate: float = 0.01
    ):
        """
        Initialize time-windowed Bloom filter.

        Args:
            window_count: Number of time windows to maintain
            items_per_window: Expected items per window
            false_positive_rate: Target false positive rate
        """
        self.window_count = window_count
        self.items_per_window = items_per_window
        self.false_positive_rate = false_positive_rate

        # Initialize windows
        self.windows: List[BloomFilter] = []
        for _ in range(window_count):
            self.windows.append(
                BloomFilter(
                    expected_items=items_per_window,
                    false_positive_rate=false_positive_rate
                )
            )

        # Current window index
        self.current_window = 0

        logger.info(
            "time_windowed_bloom_filter_initialized",
            window_count=window_count,
            items_per_window=items_per_window,
            total_memory_mb=round(
                window_count * items_per_window * 10 / 8 / 1024 / 1024, 2
            )
        )

    def add(self, item: str) -> None:
        """
        Add item to current window.

        Args:
            item: Item to add
        """
        self.windows[self.current_window].add(item)

    def contains(self, item: str) -> bool:
        """
        Check if item exists in any window.

        Args:
            item: Item to check

        Returns:
            True if item might exist in any window
        """
        for window in self.windows:
            if window.contains(item):
                return True
        return False

    def rotate_window(self) -> None:
        """
        Rotate to next window (call this periodically, e.g., every hour).

        Old window is cleared and reused.
        """
        # Move to next window
        self.current_window = (self.current_window + 1) % self.window_count

        # Clear the new current window (oldest window)
        self.windows[self.current_window].clear()

        logger.info(
            "bloom_filter_window_rotated",
            current_window=self.current_window
        )

    def get_stats(self) -> dict:
        """
        Get aggregate statistics across all windows.

        Returns:
            Dictionary with stats
        """
        total_items = sum(w.items_added for w in self.windows)
        total_memory = sum(w.bit_size for w in self.windows) / 8 / 1024 / 1024

        return {
            "window_count": self.window_count,
            "current_window": self.current_window,
            "total_items": total_items,
            "items_per_window": [w.items_added for w in self.windows],
            "total_memory_mb": round(total_memory, 2),
            "average_fp_rate": round(
                sum(w.get_false_positive_rate() for w in self.windows) / self.window_count,
                6
            )
        }
