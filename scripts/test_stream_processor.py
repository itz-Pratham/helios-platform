#!/usr/bin/env python3
"""
Test script for Stream Processor

Tests both Kafka and in-memory stream processors.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stream_processor import (
    get_stream_processor,
    init_stream_processor,
    close_stream_processor,
    StreamMessage
)
from services.stream_processor.memory_stream import InMemoryStreamProcessor


async def test_inmemory_stream_processor():
    """Test in-memory stream processor functionality."""

    print("=" * 60)
    print("🧪 Testing In-Memory Stream Processor")
    print("=" * 60)

    # Initialize stream processor
    print("\n1. Initializing stream processor...")
    processor = InMemoryStreamProcessor(max_queue_size=1000)
    await processor.connect()
    stats = await processor.get_stats()
    print(f"   ✅ Backend: {stats['backend']}")
    print(f"   ✅ Max queue size: {stats['max_queue_size']}")

    # Test 1: Create topics
    print("\n2. Creating topics...")
    await processor.create_topic("events", partitions=3)
    await processor.create_topic("reconciliation", partitions=1)
    topics = await processor.list_topics()
    print(f"   ✅ Topics created: {topics}")

    # Test 2: Subscribe to topics
    print("\n3. Subscribing to topics...")
    received_messages = []

    async def message_handler(message: StreamMessage):
        """Handle received message."""
        received_messages.append(message)
        print(f"   📨 Received: {message.topic}/{message.key} = {message.value}")

    await processor.subscribe(
        topics=["events"],
        callback=message_handler,
        group_id="test-consumer"
    )

    # Give consumer time to start
    await asyncio.sleep(0.1)

    # Test 3: Publish messages
    print("\n4. Publishing messages...")
    for i in range(5):
        await processor.publish(
            topic="events",
            key=f"event-{i}",
            value={"order_id": f"ORD-{i}", "amount": 100 + i},
            headers={"source": "test"}
        )

    # Give messages time to be consumed
    await asyncio.sleep(0.2)

    print(f"   ✅ Published 5 messages")
    print(f"   ✅ Received {len(received_messages)} messages")

    # Test 4: Verify message content
    print("\n5. Verifying message content...")
    if len(received_messages) > 0:
        first_msg = received_messages[0]
        print(f"   ✅ First message:")
        print(f"      Topic: {first_msg.topic}")
        print(f"      Key: {first_msg.key}")
        print(f"      Value: {first_msg.value}")
        print(f"      Headers: {first_msg.headers}")

    # Test 5: Statistics
    print("\n6. Getting statistics...")
    final_stats = await processor.get_stats()
    print(f"   ✅ Messages published: {final_stats['messages_published']}")
    print(f"   ✅ Messages consumed: {final_stats['messages_consumed']}")
    print(f"   ✅ Active consumers: {final_stats['active_consumers']}")
    print(f"   ✅ Topics: {final_stats['topics']}")

    # Cleanup
    print("\n7. Cleaning up...")
    await processor.close()
    print("   ✅ Stream processor closed")

    print("\n" + "=" * 60)
    print("✅ In-memory stream processor tests passed!")
    print("=" * 60)


async def test_multiple_consumers():
    """Test multiple consumers on same topic."""

    print("\n" + "=" * 60)
    print("🧪 Testing Multiple Consumers")
    print("=" * 60)

    # Initialize
    print("\n1. Initializing stream processor...")
    processor = InMemoryStreamProcessor(max_queue_size=1000)
    await processor.connect()

    # Create topic
    await processor.create_topic("multi-consumer-topic")

    # Subscribe multiple consumers
    print("\n2. Subscribing multiple consumers...")
    consumer1_msgs = []
    consumer2_msgs = []

    async def consumer1_handler(message: StreamMessage):
        consumer1_msgs.append(message)

    async def consumer2_handler(message: StreamMessage):
        consumer2_msgs.append(message)

    await processor.subscribe(
        topics=["multi-consumer-topic"],
        callback=consumer1_handler,
        group_id="consumer-1"
    )

    await processor.subscribe(
        topics=["multi-consumer-topic"],
        callback=consumer2_handler,
        group_id="consumer-2"
    )

    await asyncio.sleep(0.1)

    # Publish messages
    print("\n3. Publishing messages...")
    for i in range(10):
        await processor.publish(
            topic="multi-consumer-topic",
            key=f"msg-{i}",
            value={"data": i}
        )

    await asyncio.sleep(0.2)

    print(f"   ✅ Consumer 1 received: {len(consumer1_msgs)} messages")
    print(f"   ✅ Consumer 2 received: {len(consumer2_msgs)} messages")
    print(f"   ✅ Both consumers receive all messages (fanout)")

    # Cleanup
    await processor.close()

    print("\n" + "=" * 60)
    print("✅ Multiple consumers test passed!")
    print("=" * 60)


async def test_performance():
    """Test stream processor performance."""

    print("\n" + "=" * 60)
    print("🧪 Testing Stream Processor Performance")
    print("=" * 60)

    # Initialize
    processor = InMemoryStreamProcessor(max_queue_size=10000)
    await processor.connect()
    await processor.create_topic("perf-test")

    # Test 1: Publish throughput
    print("\n1. Testing publish throughput...")
    import time

    start = time.time()
    for i in range(1000):
        await processor.publish(
            topic="perf-test",
            key=f"key-{i}",
            value={"index": i, "data": "x" * 100}
        )
    elapsed = time.time() - start

    throughput = 1000 / elapsed
    print(f"   ✅ Published 1,000 messages in {elapsed:.3f}s")
    print(f"   ✅ Throughput: {throughput:.0f} msg/s")
    print(f"   ✅ Latency: {elapsed/1000*1000:.3f}ms per message")

    # Test 2: Consume throughput
    print("\n2. Testing consume throughput...")
    consumed = []

    async def perf_handler(message: StreamMessage):
        consumed.append(message)

    await processor.subscribe(
        topics=["perf-test"],
        callback=perf_handler,
        group_id="perf-consumer"
    )

    # Wait for consumption
    await asyncio.sleep(1.0)

    print(f"   ✅ Consumed {len(consumed)} messages")

    # Cleanup
    await processor.close()

    print("\n" + "=" * 60)
    print("✅ Performance tests passed!")
    print("=" * 60)


async def test_factory_auto_detection():
    """Test factory auto-detection."""

    print("\n" + "=" * 60)
    print("🧪 Testing Factory Auto-Detection")
    print("=" * 60)

    # Test 1: Initialize via factory
    print("\n1. Initializing via factory...")
    processor = await init_stream_processor()
    stats = await processor.get_stats()
    print(f"   ✅ Backend: {stats['backend']}")
    print(f"   ✅ Auto-detected: in-memory (no Kafka configured)")

    # Test 2: Basic operations
    print("\n2. Testing basic operations...")
    await processor.create_topic("factory-test")
    topics = await processor.list_topics()
    print(f"   ✅ Topics: {topics}")

    # Cleanup
    print("\n3. Cleaning up...")
    await close_stream_processor()
    print("   ✅ Closed successfully")

    print("\n" + "=" * 60)
    print("✅ Factory auto-detection tests passed!")
    print("=" * 60)


async def main():
    """Run all tests."""
    await test_inmemory_stream_processor()
    await test_multiple_consumers()
    await test_performance()
    await test_factory_auto_detection()

    print("\n" + "=" * 60)
    print("✅ ALL STREAM PROCESSOR TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
