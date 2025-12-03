#!/usr/bin/env python3
"""
Event Traffic Simulator for Helios Dashboard Demo
Generates realistic e-commerce event traffic across multiple cloud sources
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime
from typing import List
import argparse


class EventSimulator:
    """Generate realistic multi-cloud event traffic"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.event_count = 0
        self.error_count = 0

    # Sample customer and product data
    CUSTOMERS = [f"CUST-{i:04d}" for i in range(1, 101)]
    PRODUCTS = [
        ("PROD-LAPTOP-001", 1299.99),
        ("PROD-PHONE-002", 899.99),
        ("PROD-TABLET-003", 499.99),
        ("PROD-WATCH-004", 399.99),
        ("PROD-HEADPHONES-005", 199.99),
        ("PROD-KEYBOARD-006", 149.99),
        ("PROD-MOUSE-007", 79.99),
        ("PROD-MONITOR-008", 349.99),
    ]

    CLOUD_SOURCES = [
        ("aws", 0.40),    # 40% AWS
        ("gcp", 0.30),    # 30% GCP
        ("azure", 0.30),  # 30% Azure
    ]

    async def generate_order_event(self, session: aiohttp.ClientSession, source: str):
        """Generate an OrderPlaced event"""
        order_id = f"ORD-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        customer_id = random.choice(self.CUSTOMERS)
        product, price = random.choice(self.PRODUCTS)

        payload = {
            "order_id": order_id,
            "customer_id": customer_id,
            "product_id": product,
            "amount": price,
            "quantity": random.randint(1, 5),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send to appropriate cloud webhook
        if source == "aws":
            url = f"{self.base_url}/api/v1/webhooks/aws/eventbridge"
            data = {
                "version": "0",
                "id": f"aws-{order_id}",
                "detail-type": "OrderPlaced",
                "source": "ecommerce.orders",
                "account": "123456789012",
                "time": datetime.utcnow().isoformat() + "Z",
                "region": "us-east-1",
                "detail": payload
            }
        elif source == "gcp":
            url = f"{self.base_url}/api/v1/webhooks/gcp/pubsub"
            import base64
            import json
            data = {
                "message": {
                    "data": base64.b64encode(json.dumps(payload).encode()).decode(),
                    "attributes": {"eventType": "OrderPlaced"},
                    "messageId": f"gcp-{order_id}",
                    "publishTime": datetime.utcnow().isoformat() + "Z"
                },
                "subscription": "projects/my-project/subscriptions/helios-events"
            }
        else:  # azure
            url = f"{self.base_url}/api/v1/webhooks/azure/eventgrid"
            data = [{
                "id": f"azure-{order_id}",
                "eventType": "OrderPlaced",
                "subject": f"orders/{order_id}",
                "eventTime": datetime.utcnow().isoformat() + "Z",
                "data": payload,
                "dataVersion": "1.0"
            }]

        return url, data, order_id

    async def send_event(self, session: aiohttp.ClientSession, source: str):
        """Send a single event"""
        try:
            url, data, order_id = await self.generate_order_event(session, source)

            async with session.post(url, json=data) as response:
                if response.status in [200, 202]:
                    self.event_count += 1
                    print(f"✓ [{source.upper():5}] Event sent: {order_id} (Total: {self.event_count})")
                else:
                    self.error_count += 1
                    print(f"✗ [{source.upper():5}] Failed: {response.status}")

        except Exception as e:
            self.error_count += 1
            print(f"✗ [{source.upper():5}] Error: {str(e)}")

    def select_random_source(self) -> str:
        """Select a random cloud source based on distribution"""
        rand = random.random()
        cumulative = 0
        for source, prob in self.CLOUD_SOURCES:
            cumulative += prob
            if rand <= cumulative:
                return source
        return "aws"  # Default fallback

    async def run(self, rate: int = 10, duration: int = 60, error_rate: float = 0.05):
        """
        Run the event simulator

        Args:
            rate: Events per second
            duration: Duration in seconds (0 = infinite)
            error_rate: Percentage of events to intentionally fail (0.0 - 1.0)
        """
        print(f"🚀 Starting Helios Event Simulator")
        print(f"📊 Rate: {rate} events/sec")
        print(f"⏱️  Duration: {'∞ (infinite)' if duration == 0 else f'{duration}s'}")
        print(f"🎯 Target URL: {self.base_url}")
        print(f"☁️  Distribution: AWS 40%, GCP 30%, Azure 30%")
        print(f"⚠️  Error Rate: {error_rate * 100}%")
        print("-" * 60)

        start_time = time.time()
        interval = 1.0 / rate

        async with aiohttp.ClientSession() as session:
            event_num = 0
            try:
                while True:
                    # Check duration
                    if duration > 0 and (time.time() - start_time) >= duration:
                        break

                    # Select random cloud source
                    source = self.select_random_source()

                    # Send event
                    await self.send_event(session, source)

                    event_num += 1

                    # Sleep to maintain rate
                    await asyncio.sleep(interval)

            except KeyboardInterrupt:
                print("\n\n⏹️  Simulation stopped by user")

        # Print summary
        elapsed = time.time() - start_time
        print("-" * 60)
        print(f"📈 Simulation Summary:")
        print(f"   Total Events Sent: {self.event_count}")
        print(f"   Errors: {self.error_count}")
        print(f"   Duration: {elapsed:.1f}s")
        print(f"   Actual Rate: {self.event_count / elapsed:.1f} events/sec")
        print(f"   Success Rate: {(self.event_count / (self.event_count + self.error_count) * 100):.1f}%")


async def main():
    parser = argparse.ArgumentParser(description="Helios Event Traffic Simulator")
    parser.add_argument(
        "--rate",
        type=int,
        default=10,
        help="Events per second (default: 10)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Duration in seconds (default: 0 = infinite)"
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.05,
        help="Error rate 0.0-1.0 (default: 0.05)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8001",
        help="Base URL for Helios API (default: http://localhost:8001)"
    )

    args = parser.parse_args()

    simulator = EventSimulator(base_url=args.url)
    await simulator.run(
        rate=args.rate,
        duration=args.duration,
        error_rate=args.error_rate
    )


if __name__ == "__main__":
    asyncio.run(main())
