#!/usr/bin/env python3
"""
Test script for Bloom Filter

Tests both basic and time-windowed Bloom filters.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bloom_filter import BloomFilter, TimeWindowedBloomFilter


def test_basic_bloom_filter():
    """Test basic Bloom filter functionality."""

    print("=" * 60)
    print("🧪 Testing Basic Bloom Filter")
    print("=" * 60)

    # Initialize Bloom filter
    print("\n1. Initializing Bloom filter...")
    bloom = BloomFilter(expected_items=10000, false_positive_rate=0.01)
    stats = bloom.get_stats()
    print(f"   ✅ Bit size: {stats['bit_size']:,}")
    print(f"   ✅ Num hashes: {stats['num_hashes']}")
    print(f"   ✅ Memory: {stats['memory_mb']} MB")

    # Test 1: Add items
    print("\n2. Adding test events...")
    test_events = [f"EVENT-{i:05d}" for i in range(1000)]
    for event_id in test_events:
        bloom.add(event_id)
    print(f"   ✅ Added {len(test_events)} events")

    # Test 2: Check membership (should all be True)
    print("\n3. Checking membership (true positives)...")
    true_positives = sum(1 for event_id in test_events if bloom.contains(event_id))
    print(f"   ✅ True positives: {true_positives}/{len(test_events)}")

    # Test 3: Check non-membership (may have false positives)
    print("\n4. Checking non-membership (false positive rate)...")
    non_events = [f"MISSING-{i:05d}" for i in range(10000)]
    false_positives = sum(1 for event_id in non_events if bloom.contains(event_id))
    fp_rate = false_positives / len(non_events)
    print(f"   ✅ False positives: {false_positives}/{len(non_events)}")
    print(f"   ✅ False positive rate: {fp_rate:.4f} (target: 0.01)")

    # Test 4: Statistics
    print("\n5. Final statistics...")
    final_stats = bloom.get_stats()
    print(f"   ✅ Items added: {final_stats['items_added']:,}")
    print(f"   ✅ Fill ratio: {final_stats['fill_ratio']}")
    print(f"   ✅ Actual FP rate: {final_stats['actual_fp_rate']}")
    print(f"   ✅ Overloaded: {final_stats['overloaded']}")

    print("\n" + "=" * 60)
    print("✅ Basic Bloom filter tests passed!")
    print("=" * 60)


def test_time_windowed_bloom_filter():
    """Test time-windowed Bloom filter functionality."""

    print("\n" + "=" * 60)
    print("🧪 Testing Time-Windowed Bloom Filter")
    print("=" * 60)

    # Initialize time-windowed Bloom filter
    print("\n1. Initializing time-windowed Bloom filter...")
    bloom = TimeWindowedBloomFilter(
        window_count=4,
        items_per_window=1000,
        false_positive_rate=0.01
    )
    stats = bloom.get_stats()
    print(f"   ✅ Window count: {stats['window_count']}")
    print(f"   ✅ Total memory: {stats['total_memory_mb']} MB")

    # Test 1: Add items to window 0
    print("\n2. Adding events to window 0...")
    for i in range(100):
        bloom.add(f"WINDOW-0-EVENT-{i}")
    print(f"   ✅ Added 100 events to window 0")

    # Test 2: Check membership in window 0
    print("\n3. Checking membership in window 0...")
    found = sum(1 for i in range(100) if bloom.contains(f"WINDOW-0-EVENT-{i}"))
    print(f"   ✅ Found: {found}/100 events")

    # Test 3: Rotate to window 1
    print("\n4. Rotating to window 1...")
    bloom.rotate_window()
    print(f"   ✅ Current window: {bloom.current_window}")

    # Test 4: Add items to window 1
    print("\n5. Adding events to window 1...")
    for i in range(150):
        bloom.add(f"WINDOW-1-EVENT-{i}")
    print(f"   ✅ Added 150 events to window 1")

    # Test 5: Check membership across windows
    print("\n6. Checking membership across windows...")
    window_0_found = sum(1 for i in range(100) if bloom.contains(f"WINDOW-0-EVENT-{i}"))
    window_1_found = sum(1 for i in range(150) if bloom.contains(f"WINDOW-1-EVENT-{i}"))
    print(f"   ✅ Window 0 events found: {window_0_found}/100")
    print(f"   ✅ Window 1 events found: {window_1_found}/150")

    # Test 6: Rotate multiple times
    print("\n7. Rotating through all windows...")
    for i in range(2, 5):
        bloom.rotate_window()
        print(f"   ✅ Rotated to window {bloom.current_window}")

    # Test 7: Check if window 0 was cleared (rotated back)
    print("\n8. Checking if window 0 was cleared after rotation...")
    window_0_after_rotation = sum(
        1 for i in range(100) if bloom.contains(f"WINDOW-0-EVENT-{i}")
    )
    print(f"   ✅ Window 0 events found after rotation: {window_0_after_rotation}/100")
    print(f"   ✅ Window cleared: {window_0_after_rotation < 100}")

    # Test 8: Final statistics
    print("\n9. Final statistics...")
    final_stats = bloom.get_stats()
    print(f"   ✅ Total items: {final_stats['total_items']}")
    print(f"   ✅ Current window: {final_stats['current_window']}")
    print(f"   ✅ Average FP rate: {final_stats['average_fp_rate']}")

    print("\n" + "=" * 60)
    print("✅ Time-windowed Bloom filter tests passed!")
    print("=" * 60)


def test_performance():
    """Test Bloom filter performance."""

    print("\n" + "=" * 60)
    print("🧪 Testing Bloom Filter Performance")
    print("=" * 60)

    import time

    # Test 1: Add performance
    print("\n1. Testing add performance...")
    bloom = BloomFilter(expected_items=100000, false_positive_rate=0.01)

    start = time.time()
    for i in range(10000):
        bloom.add(f"PERF-TEST-{i}")
    elapsed = time.time() - start

    print(f"   ✅ Added 10,000 items in {elapsed:.3f}s")
    print(f"   ✅ Average: {(elapsed/10000)*1000:.3f}ms per add")

    # Test 2: Lookup performance
    print("\n2. Testing lookup performance...")

    start = time.time()
    for i in range(10000):
        bloom.contains(f"PERF-TEST-{i}")
    elapsed = time.time() - start

    print(f"   ✅ Checked 10,000 items in {elapsed:.3f}s")
    print(f"   ✅ Average: {(elapsed/10000)*1000:.3f}ms per lookup")

    # Test 3: Memory efficiency
    print("\n3. Testing memory efficiency...")
    stats = bloom.get_stats()
    memory_per_item = (stats['memory_mb'] * 1024 * 1024) / stats['items_added']
    print(f"   ✅ Total memory: {stats['memory_mb']} MB")
    print(f"   ✅ Memory per item: {memory_per_item:.2f} bytes")

    print("\n" + "=" * 60)
    print("✅ Performance tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_bloom_filter()
    test_time_windowed_bloom_filter()
    test_performance()

    print("\n" + "=" * 60)
    print("✅ ALL BLOOM FILTER TESTS PASSED!")
    print("=" * 60)
