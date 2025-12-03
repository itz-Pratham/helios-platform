#!/usr/bin/env python3
"""
Publish test events to real cloud services (AWS/GCP/Azure)

This script allows you to send real events to your cloud event services
for testing the production integration.
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cloud_clients import get_aws_client, get_gcp_client, get_azure_client
import structlog

logger = structlog.get_logger()


async def publish_aws_event(event_type: str, payload: dict):
    """Publish event to AWS EventBridge."""
    print(f"\n📤 Publishing to AWS EventBridge...")
    client = get_aws_client()

    if not client.is_configured():
        print("❌ AWS credentials not configured!")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env.production")
        return False

    await client.connect()
    success = await client.publish_event(event_type, payload)

    if success:
        print(f"✅ Event published to AWS EventBridge")
    else:
        print(f"❌ Failed to publish to AWS EventBridge")

    await client.close()
    return success


async def publish_gcp_event(event_type: str, payload: dict):
    """Publish event to GCP Pub/Sub."""
    print(f"\n📤 Publishing to GCP Pub/Sub...")
    client = get_gcp_client()

    if not client.is_configured():
        print("❌ GCP credentials not configured!")
        print("   Set GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS")
        return False

    await client.connect()
    success = await client.publish_event(event_type, payload)

    if success:
        print(f"✅ Event published to GCP Pub/Sub")
    else:
        print(f"❌ Failed to publish to GCP Pub/Sub")

    await client.close()
    return success


async def publish_azure_event(event_type: str, payload: dict):
    """Publish event to Azure Event Grid."""
    print(f"\n📤 Publishing to Azure Event Grid...")
    client = get_azure_client()

    if not client.is_configured():
        print("❌ Azure credentials not configured!")
        print("   Set AZURE_EVENT_GRID_ENDPOINT and AZURE_EVENT_GRID_ACCESS_KEY")
        return False

    await client.connect()
    success = await client.publish_event(event_type, payload)

    if success:
        print(f"✅ Event published to Azure Event Grid")
    else:
        print(f"❌ Failed to publish to Azure Event Grid")

    await client.close()
    return success


async def main():
    parser = argparse.ArgumentParser(
        description="Publish test events to cloud services"
    )
    parser.add_argument(
        "--cloud",
        choices=["aws", "gcp", "azure", "all"],
        default="all",
        help="Cloud service to publish to"
    )
    parser.add_argument(
        "--event-type",
        default="OrderPlaced",
        help="Event type (default: OrderPlaced)"
    )
    parser.add_argument(
        "--order-id",
        default="TEST-ORDER-001",
        help="Order ID for test event"
    )
    parser.add_argument(
        "--customer-id",
        default="TEST-CUSTOMER-001",
        help="Customer ID for test event"
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=99.99,
        help="Order amount"
    )

    args = parser.parse_args()

    # Prepare test payload
    payload = {
        "order_id": args.order_id,
        "customer_id": args.customer_id,
        "amount": args.amount,
        "status": "pending",
        "items": [
            {"product_id": "PROD-001", "quantity": 2, "price": 49.99}
        ]
    }

    print("=" * 60)
    print("🚀 HELIOS - Cloud Event Publisher")
    print("=" * 60)
    print(f"Event Type: {args.event_type}")
    print(f"Payload: {payload}")
    print("=" * 60)

    results = []

    # Publish to selected cloud(s)
    if args.cloud in ["aws", "all"]:
        success = await publish_aws_event(args.event_type, payload)
        results.append(("AWS", success))

    if args.cloud in ["gcp", "all"]:
        success = await publish_gcp_event(args.event_type, payload)
        results.append(("GCP", success))

    if args.cloud in ["azure", "all"]:
        success = await publish_azure_event(args.event_type, payload)
        results.append(("Azure", success))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    for cloud, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {cloud}: {status}")
    print("=" * 60)

    # Return exit code
    all_success = all(success for _, success in results)
    return 0 if all_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
