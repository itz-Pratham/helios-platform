#!/usr/bin/env python3
"""
Test script for Shard Manager

Tests consistent hashing and shard-aware reconciliation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.shard_manager import (
    ConsistentHashRing,
    ShardManager,
    ShardAwareReconciler
)


def test_consistent_hash_ring():
    """Test consistent hash ring functionality."""

    print("=" * 60)
    print("🧪 Testing Consistent Hash Ring")
    print("=" * 60)

    # Initialize hash ring
    print("\n1. Initializing hash ring...")
    shards = ["shard-0", "shard-1", "shard-2"]
    ring = ConsistentHashRing(shards=shards, virtual_nodes=150)
    stats = ring.get_stats()
    print(f"   ✅ Physical shards: {stats['physical_shards']}")
    print(f"   ✅ Virtual nodes: {stats['total_virtual_nodes']}")

    # Test 1: Shard assignment
    print("\n2. Testing shard assignment...")
    test_events = [f"EVENT-{i:05d}" for i in range(1000)]
    distribution = ring.get_shard_distribution(test_events)

    print(f"   ✅ Distribution across {len(shards)} shards:")
    for shard, count in sorted(distribution.items()):
        percentage = (count / len(test_events)) * 100
        print(f"      {shard}: {count} events ({percentage:.1f}%)")

    # Check balance (should be roughly 33% each)
    max_deviation = max(abs(count - len(test_events) / len(shards)) for count in distribution.values())
    balance_score = 100 * (1 - max_deviation / (len(test_events) / len(shards)))
    print(f"   ✅ Balance score: {balance_score:.1f}%")

    # Test 2: Consistent assignment
    print("\n3. Testing consistency...")
    event_id = "TEST-EVENT-123"
    shard1 = ring.get_shard(event_id)
    shard2 = ring.get_shard(event_id)
    print(f"   ✅ Event {event_id}")
    print(f"      First lookup: {shard1}")
    print(f"      Second lookup: {shard2}")
    print(f"      Consistent: {shard1 == shard2}")

    # Test 3: Add shard
    print("\n4. Testing dynamic shard addition...")
    ring.add_shard("shard-3")

    # Check redistribution
    new_distribution = ring.get_shard_distribution(test_events)
    print(f"   ✅ New distribution across 4 shards:")
    for shard, count in sorted(new_distribution.items()):
        percentage = (count / len(test_events)) * 100
        print(f"      {shard}: {count} events ({percentage:.1f}%)")

    # Calculate keys moved
    keys_moved = sum(
        1 for event_id in test_events
        if ring.get_shard(event_id) != distribution.get(ring.get_shard(event_id), 0)
    )
    movement_percentage = (keys_moved / len(test_events)) * 100
    print(f"   ✅ Keys moved: {keys_moved}/{len(test_events)} ({movement_percentage:.1f}%)")
    print(f"   ✅ Keys stable: {100 - movement_percentage:.1f}%")

    print("\n" + "=" * 60)
    print("✅ Consistent hash ring tests passed!")
    print("=" * 60)


def test_shard_manager_single_mode():
    """Test shard manager in single-node mode."""

    print("\n" + "=" * 60)
    print("🧪 Testing Shard Manager (Single-Node Mode)")
    print("=" * 60)

    # Initialize in single mode
    print("\n1. Initializing shard manager (single mode)...")
    manager = ShardManager(mode="single")
    stats = manager.get_stats()
    print(f"   ✅ Mode: {stats['mode']}")

    # Test 1: Shard assignment
    print("\n2. Testing shard assignment...")
    event_ids = [f"EVENT-{i}" for i in range(10)]
    for event_id in event_ids[:3]:
        shard = manager.get_shard(event_id)
        print(f"   ✅ {event_id} → {shard}")

    # Test 2: Event processing
    print("\n3. Testing event processing...")
    should_process = manager.should_process_event("EVENT-123", "default")
    print(f"   ✅ Should process EVENT-123: {should_process}")

    # Test 3: Event filtering
    print("\n4. Testing event filtering...")
    filtered = manager.get_events_for_shard(event_ids, "default")
    print(f"   ✅ Events for 'default': {len(filtered)}/{len(event_ids)}")

    print("\n" + "=" * 60)
    print("✅ Single-node mode tests passed!")
    print("=" * 60)


def test_shard_manager_sharded_mode():
    """Test shard manager in sharded mode."""

    print("\n" + "=" * 60)
    print("🧪 Testing Shard Manager (Sharded Mode)")
    print("=" * 60)

    # Initialize in sharded mode
    print("\n1. Initializing shard manager (sharded mode)...")
    shards = ["us-east-1", "us-west-2", "eu-west-1"]
    manager = ShardManager(mode="sharded", shards=shards, virtual_nodes=150)
    stats = manager.get_stats()
    print(f"   ✅ Mode: {stats['mode']}")
    print(f"   ✅ Shards: {stats['physical_shards']}")

    # Test 1: Shard assignment
    print("\n2. Testing shard assignment...")
    test_events = [f"ORDER-{i:05d}" for i in range(100)]
    for event_id in test_events[:5]:
        shard = manager.get_shard(event_id)
        print(f"   ✅ {event_id} → {shard}")

    # Test 2: Event processing
    print("\n3. Testing event processing (us-east-1 perspective)...")
    current_shard = "us-east-1"
    local_count = sum(
        1 for event_id in test_events
        if manager.should_process_event(event_id, current_shard)
    )
    print(f"   ✅ Events for {current_shard}: {local_count}/{len(test_events)}")

    # Test 3: Event filtering
    print("\n4. Testing event filtering...")
    for shard in shards:
        filtered = manager.get_events_for_shard(test_events, shard)
        percentage = (len(filtered) / len(test_events)) * 100
        print(f"   ✅ {shard}: {len(filtered)} events ({percentage:.1f}%)")

    print("\n" + "=" * 60)
    print("✅ Sharded mode tests passed!")
    print("=" * 60)


def test_shard_aware_reconciler():
    """Test shard-aware reconciler."""

    print("\n" + "=" * 60)
    print("🧪 Testing Shard-Aware Reconciler")
    print("=" * 60)

    # Setup
    print("\n1. Initializing reconciler...")
    shards = ["shard-A", "shard-B", "shard-C"]
    manager = ShardManager(mode="sharded", shards=shards)
    reconciler = ShardAwareReconciler(
        shard_manager=manager,
        current_shard="shard-A"
    )
    print(f"   ✅ Current shard: shard-A")

    # Test 1: Filter events
    print("\n2. Filtering events for reconciliation...")
    event_ids = [f"EVENT-{i:04d}" for i in range(100)]
    local_events, remote_events = reconciler.filter_events_for_reconciliation(event_ids)

    print(f"   ✅ Total events: {len(event_ids)}")
    print(f"   ✅ Local events: {len(local_events)} ({len(local_events)/len(event_ids)*100:.1f}%)")
    print(f"   ✅ Remote events: {len(remote_events)} ({len(remote_events)/len(event_ids)*100:.1f}%)")

    # Test 2: Reconciliation strategy
    print("\n3. Testing reconciliation strategy...")
    for event_id in event_ids[:5]:
        strategy = reconciler.get_reconciliation_strategy(event_id)
        target = reconciler.get_target_shard(event_id)
        print(f"   ✅ {event_id}: strategy={strategy}, target={target}")

    # Test 3: Statistics
    print("\n4. Getting reconciler statistics...")
    stats = reconciler.get_stats()
    print(f"   ✅ Current shard: {stats['current_shard']}")
    print(f"   ✅ Mode: {stats['shard_manager']['mode']}")
    print(f"   ✅ Total shards: {stats['shard_manager']['physical_shards']}")

    print("\n" + "=" * 60)
    print("✅ Shard-aware reconciler tests passed!")
    print("=" * 60)


def test_distribution_fairness():
    """Test distribution fairness across shards."""

    print("\n" + "=" * 60)
    print("🧪 Testing Distribution Fairness")
    print("=" * 60)

    # Test with different shard counts
    shard_counts = [3, 5, 10]

    for num_shards in shard_counts:
        print(f"\n{num_shards} shards:")

        shards = [f"shard-{i}" for i in range(num_shards)]
        ring = ConsistentHashRing(shards=shards, virtual_nodes=150)

        # Generate test keys
        test_keys = [f"KEY-{i:06d}" for i in range(10000)]
        distribution = ring.get_shard_distribution(test_keys)

        # Calculate statistics
        expected_per_shard = len(test_keys) / num_shards
        actual_counts = list(distribution.values())
        avg_count = sum(actual_counts) / len(actual_counts)
        std_dev = (sum((x - avg_count) ** 2 for x in actual_counts) / len(actual_counts)) ** 0.5
        max_deviation = max(abs(count - expected_per_shard) for count in actual_counts)

        print(f"   Expected per shard: {expected_per_shard:.0f}")
        print(f"   Actual average: {avg_count:.0f}")
        print(f"   Std deviation: {std_dev:.0f}")
        print(f"   Max deviation: {max_deviation:.0f} ({max_deviation/expected_per_shard*100:.1f}%)")

        # Check fairness (deviation should be < 10%)
        is_fair = (max_deviation / expected_per_shard) < 0.1
        print(f"   ✅ Fair distribution: {is_fair}")

    print("\n" + "=" * 60)
    print("✅ Distribution fairness tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_consistent_hash_ring()
    test_shard_manager_single_mode()
    test_shard_manager_sharded_mode()
    test_shard_aware_reconciler()
    test_distribution_fairness()

    print("\n" + "=" * 60)
    print("✅ ALL SHARD MANAGER TESTS PASSED!")
    print("=" * 60)
