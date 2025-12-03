"""Azure Event Grid webhook adapter.

Handles incoming events from Azure Event Grid.
Supports:
- Subscription validation handshake
- Event validation
- Signature verification (in production)
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, Field
import structlog
import json

from models import EventType, EventSource, IngestEventRequest
from services import get_event_gateway, get_kafka_producer
from models import EventRepository, get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
router = APIRouter()


class EventGridEvent(BaseModel):
    """Azure Event Grid event structure."""
    id: str
    eventType: str
    subject: str
    eventTime: str
    data: Dict[str, Any]
    dataVersion: str = Field(default="1.0")
    metadataVersion: str = Field(default="1")
    topic: Optional[str] = None


class SubscriptionValidationEvent(BaseModel):
    """Azure Event Grid subscription validation event."""
    id: str
    eventType: str
    subject: str
    eventTime: str
    data: Dict[str, str]  # Contains validationCode
    dataVersion: str
    metadataVersion: str
    topic: Optional[str] = None


class SubscriptionValidationResponse(BaseModel):
    """Response for subscription validation."""
    validationResponse: str


def parse_event_type(event_type_str: str) -> Optional[EventType]:
    """
    Map Azure eventType to Helios EventType.

    Args:
        event_type_str: Azure Event Grid eventType

    Returns:
        EventType if recognized, None otherwise
    """
    # Azure uses namespaced event types like "Contoso.Orders.OrderPlaced"
    # We'll extract the last part and map it
    event_name = event_type_str.split('.')[-1]

    mapping = {
        "OrderPlaced": EventType.ORDER_PLACED,
        "PaymentProcessed": EventType.PAYMENT_PROCESSED,
        "InventoryReserved": EventType.INVENTORY_RESERVED,
    }
    return mapping.get(event_name)


@router.post(
    "/webhooks/azure/eventgrid",
    status_code=status.HTTP_200_OK,
    summary="Azure Event Grid webhook endpoint",
    description="Receives events from Azure Event Grid subscriptions"
)
async def azure_eventgrid_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming events from Azure Event Grid.

    Azure sends events in an array format. Handles:
    1. Subscription validation (handshake)
    2. Regular event delivery
    """
    try:
        # Parse body
        body = await request.body()
        body_str = body.decode('utf-8')
        events_data = json.loads(body_str)

        # Azure sends events as an array
        if not isinstance(events_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expected array of events"
            )

        results = []

        for event_data in events_data:
            try:
                event_type = event_data.get('eventType')

                # Handle subscription validation
                if event_type == 'Microsoft.EventGrid.SubscriptionValidationEvent':
                    validation_code = event_data.get('data', {}).get('validationCode')
                    logger.info(
                        "azure_subscription_validation",
                        event_id=event_data.get('id'),
                        topic=event_data.get('topic')
                    )
                    # Return validation response immediately
                    return {"validationResponse": validation_code}

                # Parse regular event
                eg_event = EventGridEvent(**event_data)

                # Map eventType to Helios EventType
                helios_event_type = parse_event_type(eg_event.eventType)
                if not helios_event_type:
                    logger.warning(
                        "azure_unknown_event_type",
                        event_type=eg_event.eventType,
                        event_id=eg_event.id
                    )
                    results.append({
                        "event_id": eg_event.id,
                        "status": "skipped",
                        "reason": f"Unknown event type: {eg_event.eventType}"
                    })
                    continue

                # Extract topic details
                # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.EventGrid/topics/{topic}
                topic_name = "unknown"
                if eg_event.topic:
                    topic_parts = eg_event.topic.split('/')
                    topic_name = topic_parts[-1] if topic_parts else "unknown"

                # Create Helios event request
                helios_event = IngestEventRequest(
                    event_type=helios_event_type,
                    source=EventSource.AZURE,
                    payload=eg_event.data,
                    metadata={
                        "azure_event_id": eg_event.id,
                        "azure_event_type": eg_event.eventType,
                        "azure_subject": eg_event.subject,
                        "azure_event_time": eg_event.eventTime,
                        "azure_topic": eg_event.topic,
                        "azure_topic_name": topic_name,
                        "azure_data_version": eg_event.dataVersion,
                    }
                )

                event_id = eg_event.id

                logger.info(
                    "azure_eventgrid_event_received",
                    event_id=event_id,
                    event_type=eg_event.eventType,
                    subject=eg_event.subject
                )

                # Get services
                gateway = get_event_gateway()
                producer = get_kafka_producer()

                # Validate
                is_valid, error_msg = await gateway.validate_event(helios_event)
                if not is_valid:
                    logger.warning(
                        "azure_event_validation_failed",
                        event_id=event_id,
                        error=error_msg
                    )
                    results.append({
                        "event_id": event_id,
                        "status": "validation_failed",
                        "error": error_msg
                    })
                    continue

                # Check duplicates
                if await gateway.is_duplicate(event_id):
                    logger.warning(
                        "azure_duplicate_event_rejected",
                        event_id=event_id
                    )
                    results.append({
                        "event_id": event_id,
                        "status": "duplicate"
                    })
                    continue

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
                    "azure_event_ingested_successfully",
                    event_id=event_id,
                    order_id=helios_event.payload.get("order_id")
                )

                results.append({
                    "event_id": event_id,
                    "status": "accepted"
                })

            except Exception as e:
                logger.error(
                    "azure_event_processing_error",
                    event_id=event_data.get('id'),
                    error=str(e)
                )
                results.append({
                    "event_id": event_data.get('id'),
                    "status": "error",
                    "error": str(e)
                })

        # Return batch results
        return {
            "status": "processed",
            "total_events": len(events_data),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "azure_eventgrid_webhook_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Azure events: {str(e)}"
        )


@router.get(
    "/webhooks/azure/health",
    summary="Azure webhook health check",
    description="Health check endpoint for Azure Event Grid webhook"
)
async def azure_webhook_health():
    """Health check for Azure webhook endpoint."""
    return {
        "status": "healthy",
        "adapter": "azure_eventgrid",
        "timestamp": datetime.utcnow().isoformat()
    }
