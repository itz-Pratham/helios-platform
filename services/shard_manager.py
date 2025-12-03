"""
Shard Manager for Distributed Reconciliation

Uses consistent hashing for shard-aware reconciliation across distributed databases.
Supports hybrid config: single-node (local) vs. sharded (production).
"""

import hashlib
import bisect
from typing import List, Dict, Set, Optional, Tuple
import structlog

logger = structlog.get_logger()


class ConsistentHashRing:
    """
    Consistent hash ring for distributed shard assignment.

    Uses virtual nodes to ensure even distribution.
    Supports dynamic shard addition/removal with minimal rebalancing.

    Example:
        ring = ConsistentHashRing(shards=["shard-0", "shard-1", "shard-2"])
        shard = ring.get_shard("event-123")  # "shard-1"
    """

    def __init__(self, shards: List[str], virtual_nodes: int = 150):
        """
        Initialize consistent hash ring.

        Args:
            shards: List of shard identifiers
            virtual_nodes: Number of virtual nodes per physical shard
                          (higher = better distribution, more memory)
        """
        self.shards = shards
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

        # Build hash ring
        self._build_ring()

        logger.info(
            "consistent_hash_ring_initialized",
            shards=len(shards),
            virtual_nodes=virtual_nodes,
            total_nodes=len(self.ring)
        )

    def _hash(self, key: str) -> int:
        """
        Generate hash for key.

        Uses MD5 for speed (not cryptographic use case).

        Args:
            key: Key to hash

        Returns:
            32-bit hash value
        """
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def _build_ring(self) -> None:
        """Build hash ring with virtual nodes."""
        self.ring = {}

        for shard in self.shards:
            for i in range(self.virtual_nodes):
                # Create virtual node key
                virtual_key = f"{shard}:vnode-{i}"
                hash_value = self._hash(virtual_key)

                # Add to ring
                self.ring[hash_value] = shard

        # Sort keys for binary search
        self.sorted_keys = sorted(self.ring.keys())

        logger.debug(
            "hash_ring_built",
            physical_shards=len(self.shards),
            virtual_nodes=len(self.ring)
        )

    def get_shard(self, key: str) -> str:
        """
        Get shard for key using consistent hashing.

        Args:
            key: Key to look up (typically event_id)

        Returns:
            Shard identifier
        """
        if not self.ring:
            raise ValueError("Hash ring is empty")

        # Hash the key
        hash_value = self._hash(key)

        # Find position in ring (clockwise search)
        idx = bisect.bisect_right(self.sorted_keys, hash_value)

        # Wrap around if necessary
        if idx == len(self.sorted_keys):
            idx = 0

        # Get shard from ring
        shard = self.ring[self.sorted_keys[idx]]

        return shard

    def get_shard_distribution(self, keys: List[str]) -> Dict[str, int]:
        """
        Analyze shard distribution for given keys.

        Args:
            keys: List of keys to analyze

        Returns:
            Dictionary mapping shard -> count
        """
        distribution: Dict[str, int] = {shard: 0 for shard in self.shards}

        for key in keys:
            shard = self.get_shard(key)
            distribution[shard] += 1

        return distribution

    def add_shard(self, shard: str) -> None:
        """
        Add new shard to ring.

        Args:
            shard: Shard identifier
        """
        if shard in self.shards:
            logger.warning("shard_already_exists", shard=shard)
            return

        self.shards.append(shard)
        self._build_ring()

        logger.info("shard_added", shard=shard, total_shards=len(self.shards))

    def remove_shard(self, shard: str) -> None:
        """
        Remove shard from ring.

        Args:
            shard: Shard identifier
        """
        if shard not in self.shards:
            logger.warning("shard_not_found", shard=shard)
            return

        self.shards.remove(shard)
        self._build_ring()

        logger.info("shard_removed", shard=shard, total_shards=len(self.shards))

    def get_stats(self) -> Dict[str, any]:
        """
        Get hash ring statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "physical_shards": len(self.shards),
            "virtual_nodes_per_shard": self.virtual_nodes,
            "total_virtual_nodes": len(self.ring),
            "shards": self.shards
        }


class ShardManager:
    """
    Shard manager for distributed reconciliation.

    Supports two modes:
    1. Single-node mode: All events handled by single instance
    2. Sharded mode: Events distributed across multiple shards
    """

    def __init__(
        self,
        mode: str = "single",
        shards: Optional[List[str]] = None,
        virtual_nodes: int = 150
    ):
        """
        Initialize shard manager.

        Args:
            mode: "single" or "sharded"
            shards: List of shard identifiers (required for sharded mode)
            virtual_nodes: Virtual nodes per shard (for sharded mode)
        """
        self.mode = mode
        self.hash_ring: Optional[ConsistentHashRing] = None

        if mode == "sharded":
            if not shards:
                raise ValueError("Shards required for sharded mode")

            self.hash_ring = ConsistentHashRing(
                shards=shards,
                virtual_nodes=virtual_nodes
            )

            logger.info(
                "shard_manager_initialized",
                mode=mode,
                shards=len(shards)
            )
        else:
            logger.info("shard_manager_initialized", mode=mode)

    def get_shard(self, event_id: str) -> str:
        """
        Get shard for event.

        Args:
            event_id: Event identifier

        Returns:
            Shard identifier (or "default" in single-node mode)
        """
        if self.mode == "single":
            return "default"

        return self.hash_ring.get_shard(event_id)

    def should_process_event(
        self,
        event_id: str,
        current_shard: str
    ) -> bool:
        """
        Check if current shard should process event.

        Args:
            event_id: Event identifier
            current_shard: Current shard identifier

        Returns:
            True if event should be processed by current shard
        """
        if self.mode == "single":
            return True

        assigned_shard = self.hash_ring.get_shard(event_id)
        return assigned_shard == current_shard

    def get_events_for_shard(
        self,
        event_ids: List[str],
        shard: str
    ) -> List[str]:
        """
        Filter events that belong to specific shard.

        Args:
            event_ids: List of event identifiers
            shard: Shard identifier

        Returns:
            Filtered list of event IDs
        """
        if self.mode == "single":
            return event_ids

        return [
            event_id for event_id in event_ids
            if self.hash_ring.get_shard(event_id) == shard
        ]

    def get_shard_boundaries(self, shard: str) -> Optional[List[Tuple[int, int]]]:
        """
        Get hash ring boundaries for shard.

        Useful for database range queries.

        Args:
            shard: Shard identifier

        Returns:
            List of (start, end) hash ranges for shard
        """
        if self.mode == "single":
            return None

        if shard not in self.hash_ring.shards:
            raise ValueError(f"Unknown shard: {shard}")

        boundaries = []
        prev_key = None

        for key in self.hash_ring.sorted_keys:
            if self.hash_ring.ring[key] == shard:
                if prev_key is not None:
                    boundaries.append((prev_key, key))

            prev_key = key

        return boundaries

    def get_stats(self) -> Dict[str, any]:
        """
        Get shard manager statistics.

        Returns:
            Dictionary with stats
        """
        stats = {
            "mode": self.mode
        }

        if self.mode == "sharded":
            stats.update(self.hash_ring.get_stats())

        return stats


class ShardAwareReconciler:
    """
    Shard-aware reconciliation coordinator.

    Optimizes reconciliation by processing only events assigned to current shard.
    """

    def __init__(
        self,
        shard_manager: ShardManager,
        current_shard: str = "default"
    ):
        """
        Initialize shard-aware reconciler.

        Args:
            shard_manager: Shard manager instance
            current_shard: Current shard identifier
        """
        self.shard_manager = shard_manager
        self.current_shard = current_shard

        logger.info(
            "shard_aware_reconciler_initialized",
            mode=shard_manager.mode,
            current_shard=current_shard
        )

    def filter_events_for_reconciliation(
        self,
        event_ids: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Filter events into local vs. remote.

        Args:
            event_ids: List of event identifiers

        Returns:
            Tuple of (local_events, remote_events)
        """
        if self.shard_manager.mode == "single":
            return event_ids, []

        local_events = []
        remote_events = []

        for event_id in event_ids:
            if self.shard_manager.should_process_event(event_id, self.current_shard):
                local_events.append(event_id)
            else:
                remote_events.append(event_id)

        logger.debug(
            "events_filtered_by_shard",
            total=len(event_ids),
            local=len(local_events),
            remote=len(remote_events)
        )

        return local_events, remote_events

    def get_reconciliation_strategy(
        self,
        event_id: str
    ) -> str:
        """
        Get reconciliation strategy for event.

        Args:
            event_id: Event identifier

        Returns:
            "local" or "forward"
        """
        if self.shard_manager.should_process_event(event_id, self.current_shard):
            return "local"
        else:
            return "forward"

    def get_target_shard(self, event_id: str) -> str:
        """
        Get target shard for event.

        Args:
            event_id: Event identifier

        Returns:
            Target shard identifier
        """
        return self.shard_manager.get_shard(event_id)

    def get_stats(self) -> Dict[str, any]:
        """
        Get reconciler statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "current_shard": self.current_shard,
            "shard_manager": self.shard_manager.get_stats()
        }
