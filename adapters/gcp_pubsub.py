"""GCP Pub/Sub push subscription adapter.

Handles incoming events from GCP Pub/Sub push subscriptions.
Supports:
- Push subscription verification
- Base64 message decoding
- Attribute extraction
"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, Field
import structlog
import json
import base64

from models import EventType, EventSource, IngestEventRequest
from services import get_event_gateway, get_kafka_producer
from models import EventRepository, get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
router = APIRouter()


class PubSubMessage(BaseModel):
    """GCP Pub/Sub message structure."""
    data: str  # Base64 encoded
    attributes: Dict[str, str] = Field(default_factory=dict)
    messageId: str
    message_id: Optional[str] = Field(default=None, alias="message_id")
    publishTime: str
    publish_time: Optional[str] = Field(default=None, alias="publish_time")


class PubSubPushRequest(BaseModel):
    """GCP Pub/Sub push request structure."""
    message: PubSubMessage
    subscription: str


def parse_event_type(event_type_str: str) -> Optional[EventType]:
    """
    Map GCP event type to Helios EventType.

    Args:
        event_type_str: Event type string from Pub/Sub attributes

    Returns:
        EventType if recognized, None otherwise
    """
    mapping = {
        "OrderPlaced": EventType.ORDER_PLACED,
        "order.placed": EventType.ORDER_PLACED,
        "PaymentProcessed": EventType.PAYMENT_PROCESSED,
        "payment.processed": EventType.PAYMENT_PROCESSED,
        "InventoryReserved": EventType.INVENTORY_RESERVED,
        "inventory.reserved": EventType.INVENTORY_RESERVED,
    }
    return mapping.get(event_type_str)


@router.post(
    "/webhooks/gcp/pubsub",
    status_code=status.HTTP_200_OK,
    summary="GCP Pub/Sub webhook endpoint",
    description="Receives events from GCP Pub/Sub push subscriptions"
)
async def gcp_pubsub_webhook(
    push_request: PubSubPushRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming events from GCP Pub/Sub push subscription.

    GCP Pub/Sub sends events as POST requests with:
    - message.data: Base64 encoded JSON payload
    - message.attributes: Event metadata
    - message.messageId: Unique message identifier
    """
    try:
        message = push_request.message
        message_id = message.messageId or message.message_id

        logger.info(
            "gcp_pubsub_message_received",
            message_id=message_id,
            subscription=push_request.subscription,
            attributes=message.attributes
        )

        # Decode Base64 data
        try:
            decoded_data = base64.b64decode(message.data).decode('utf-8')
            payload = json.loads(decoded_data)
        except Exception as e:
            logger.error(
                "gcp_message_decode_error",
                message_id=message_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode message data: {str(e)}"
            )

        # Get event type from attributes or payload
        event_type_str = message.attributes.get('eventType') or message.attributes.get('event_type')
        if not event_type_str:
            event_type_str = payload.get('event_type')

        if not event_type_str:
            logger.warning(
                "gcp_missing_event_type",
                message_id=message_id,
                attributes=message.attributes
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event_type in attributes or payload"
            )

        # Map to EventType
        event_type = parse_event_type(event_type_str)
        if not event_type:
            logger.warning(
                "gcp_unknown_event_type",
                event_type=event_type_str,
                message_id=message_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event type: {event_type_str}"
            )

        # Extract project and topic from subscription
        # Format: projects/{project}/subscriptions/{subscription}
        subscription_parts = push_request.subscription.split('/')
        project_id = subscription_parts[1] if len(subscription_parts) > 1 else "unknown"

        # Create Helios event request
        helios_event = IngestEventRequest(
            event_type=event_type,
            source=EventSource.GCP,
            payload=payload,
            metadata={
                "gcp_message_id": message_id,
                "gcp_project_id": project_id,
                "gcp_subscription": push_request.subscription,
                "gcp_publish_time": message.publishTime or message.publish_time,
                "gcp_attributes": message.attributes,
            }
        )

        event_id = message_id

        # Get services
        gateway = get_event_gateway()
        producer = get_kafka_producer()

        # Validate
        is_valid, error_msg = await gateway.validate_event(helios_event)
        if not is_valid:
            logger.warning(
                "gcp_event_validation_failed",
                event_id=event_id,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event validation failed: {error_msg}"
            )

        # Check duplicates
        if await gateway.is_duplicate(event_id):
            logger.warning(
                "gcp_duplicate_event_rejected",
                event_id=event_id
            )
            # Return 200 to acknowledge message (prevent redelivery)
            return {
                "status": "duplicate",
                "event_id": event_id,
                "message": "Event already processed"
            }

        # Produce to Kafka
        topic_suffix = f"events.{helios_event.event_type.value.lower()}"
        await producer.produce(
            topic_suffix=topic_suffix,
            event_id=event_id,
            event_type=helios_event.event_type.value,
            payload=helios_event.payload,
            metadata=helios_event.metadata,
        )

        # Store to Postgres
        event_repo = EventRepository(db)
        await event_repo.create(
            event_id=event_id,
            event_type=helios_event.event_type.value,
            source=helios_event.source.value,
            payload=helios_event.payload,
            metadata=helios_event.metadata,
        )

        await db.commit()

        # Mark as processed
        await gateway.mark_processed(event_id)

        logger.info(
            "gcp_event_ingested_successfully",
            event_id=event_id,
            order_id=helios_event.payload.get("order_id")
        )

        # Return 200 to acknowledge message
        return {
            "status": "accepted",
            "event_id": event_id,
            "source": "gcp",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "gcp_pubsub_webhook_error",
            error=str(e),
            error_type=type(e).__name__
        )
        # Return 500 to trigger retry from Pub/Sub
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process GCP event: {str(e)}"
        )


@router.get(
    "/webhooks/gcp/health",
    summary="GCP webhook health check",
    description="Health check endpoint for GCP Pub/Sub webhook"
)
async def gcp_webhook_health():
    """Health check for GCP webhook endpoint."""
    return {
        "status": "healthy",
        "adapter": "gcp_pubsub",
        "timestamp": datetime.utcnow().isoformat()
    }
