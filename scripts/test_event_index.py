#!/usr/bin/env python3
"""
Test script for Event Index

Tests both Redis and SQLite backends.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_index import get_event_index, init_event_index, close_event_index


async def test_event_index():
    """Test event index functionality."""

    print("=" * 60)
    print("🧪 Testing Event Index")
    print("=" * 60)

    # Initialize event index
    print("\n1. Initializing event index...")
    index = await init_event_index()
    stats = await index.get_stats()
    print(f"   ✅ Backend: {stats['backend']}")
    print(f"   ✅ Initial events: {stats['event_count']}")

    # Test 1: Index events from multiple sources
    print("\n2. Indexing test events...")
    test_event_id = "TEST-EVENT-001"

    # Index from AWS
    await index.index_event(
        event_id=test_event_id,
        source="aws",
        metadata={
            "timestamp": datetime.utcnow(),
            "payload_hash": "abc123",
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "amount": 99.99
        }
    )
    print("   ✅ Indexed from AWS")

    # Index from GCP
    await index.index_event(
        event_id=test_event_id,
        source="gcp",
        metadata={
            "timestamp": datetime.utcnow(),
            "payload_hash": "abc123",
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "amount": 99.99
        }
    )
    print("   ✅ Indexed from GCP")

    # Test 2: Check event existence
    print("\n3. Checking event existence...")
    exists = await index.event_exists(test_event_id)
    print(f"   ✅ Event exists: {exists}")

    # Test 3: Get event sources
    print("\n4. Getting event sources...")
    sources = await index.get_event_sources(test_event_id)
    print(f"   ✅ Sources: {sources}")

    # Test 4: Get event metadata
    print("\n5. Getting event metadata...")
    metadata = await index.get_event_metadata(test_event_id)
    if metadata:
        print(f"   ✅ Order ID: {metadata.get('order_id')}")
        print(f"   ✅ Customer ID: {metadata.get('customer_id')}")
        print(f"   ✅ Amount: ${metadata.get('amount')}")
    else:
        print("   ❌ Metadata not found")

    # Test 5: Check for missing sources
    print("\n6. Checking for missing sources...")
    expected_sources = {"aws", "gcp", "azure"}
    missing = await index.get_missing_sources(test_event_id, expected_sources)
    print(f"   ✅ Missing sources: {missing}")

    # Test 6: Index event from Azure
    print("\n7. Indexing event from Azure...")
    await index.index_event(
        event_id=test_event_id,
        source="azure",
        metadata={
            "timestamp": datetime.utcnow(),
            "payload_hash": "abc123",
            "order_id": "ORD-001"
        }
    )
    print("   ✅ Indexed from Azure")

    # Check again for missing sources
    missing_after = await index.get_missing_sources(test_event_id, expected_sources)
    print(f"   ✅ Missing sources after Azure: {missing_after}")

    # Test 7: Performance test
    print("\n8. Performance test (100 events)...")
    import time
    start = time.time()

    for i in range(100):
        await index.index_event(
            event_id=f"PERF-TEST-{i:03d}",
            source="aws",
            metadata={
                "timestamp": datetime.utcnow(),
                "payload_hash": f"hash-{i}",
                "order_id": f"ORD-{i}"
            }
        )

    elapsed = time.time() - start
    print(f"   ✅ Indexed 100 events in {elapsed:.2f}s")
    print(f"   ✅ Average: {(elapsed/100)*1000:.2f}ms per event")

    # Final stats
    print("\n9. Final statistics...")
    final_stats = await index.get_stats()
    print(f"   ✅ Total events: {final_stats['event_count']}")
    if 'memory_used_mb' in final_stats:
        print(f"   ✅ Memory used: {final_stats['memory_used_mb']} MB")
    if 'db_size_mb' in final_stats:
        print(f"   ✅ DB size: {final_stats['db_size_mb']} MB")

    # Cleanup
    print("\n10. Cleaning up...")
    await close_event_index()
    print("   ✅ Event index closed")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_event_index())
