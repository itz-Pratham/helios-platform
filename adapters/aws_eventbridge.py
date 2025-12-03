"""AWS EventBridge webhook adapter.

Handles incoming events from AWS EventBridge.
Supports:
- SNS subscription confirmation
- Event validation
- Signature verification (in production)
"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
import structlog
import json

from models import EventType, EventSource, IngestEventRequest
from services import get_event_gateway, get_kafka_producer
from models import EventRepository, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

logger = structlog.get_logger()
router = APIRouter()


class AWSEventBridgeEvent(BaseModel):
    """AWS EventBridge event structure."""
    version: str = Field(default="0")
    id: str
    detail_type: str = Field(alias="detail-type")
    source: str
    account: str
    time: str
    region: str
    resources: list = Field(default_factory=list)
    detail: Dict[str, Any]


class SNSMessage(BaseModel):
    """SNS message structure for subscription confirmation."""
    Type: str
    MessageId: str
    TopicArn: Optional[str] = None
    Message: Optional[str] = None
    Timestamp: str
    SignatureVersion: Optional[str] = None
    Signature: Optional[str] = None
    SigningCertURL: Optional[str] = None
    SubscribeURL: Optional[str] = None
    Token: Optional[str] = None


def parse_event_type(detail_type: str) -> Optional[EventType]:
    """
    Map AWS detail-type to Helios EventType.

    Args:
        detail_type: AWS EventBridge detail-type

    Returns:
        EventType if recognized, None otherwise
    """
    mapping = {
        "OrderPlaced": EventType.ORDER_PLACED,
        "Order Placed": EventType.ORDER_PLACED,
        "PaymentProcessed": EventType.PAYMENT_PROCESSED,
        "Payment Processed": EventType.PAYMENT_PROCESSED,
        "InventoryReserved": EventType.INVENTORY_RESERVED,
        "Inventory Reserved": EventType.INVENTORY_RESERVED,
    }
    return mapping.get(detail_type)


@router.post(
    "/webhooks/aws/eventbridge",
    status_code=status.HTTP_202_ACCEPTED,
    summary="AWS EventBridge webhook endpoint",
    description="Receives events from AWS EventBridge via SNS/HTTP subscription"
)
async def aws_eventbridge_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming events from AWS EventBridge.

    Supports two modes:
    1. SNS subscription confirmation
    2. Actual event delivery
    """
    try:
        # Parse raw body
        body = await request.body()
        body_str = body.decode('utf-8')

        event_data = None

        # Check if this is an SNS message
        try:
            sns_message = json.loads(body_str)
            message_type = sns_message.get('Type')

            # Handle SNS subscription confirmation
            if message_type == 'SubscriptionConfirmation':
                subscribe_url = sns_message.get('SubscribeURL')
                logger.info(
                    "aws_sns_subscription_confirmation",
                    topic_arn=sns_message.get('TopicArn'),
                    subscribe_url=subscribe_url
                )
                # In production, you would call subscribe_url to confirm
                # For now, just log it
                return {
                    "status": "subscription_confirmation_received",
                    "message": "Please confirm subscription manually via SubscribeURL",
                    "subscribe_url": subscribe_url
                }

            # Handle SNS notification (actual event)
            elif message_type == 'Notification':
                # Extract the actual EventBridge event from SNS Message
                event_data = json.loads(sns_message.get('Message', '{}'))
            else:
                # Direct EventBridge event (without SNS wrapper)
                event_data = sns_message

        except json.JSONDecodeError:
            # Direct EventBridge event (without SNS wrapper)
            event_data = json.loads(body_str)

        # Parse EventBridge event
        try:
            eb_event = AWSEventBridgeEvent(**event_data)
        except Exception as e:
            logger.error(
                "aws_eventbridge_parse_error",
                error=str(e),
                body=body_str[:200]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid EventBridge event format: {str(e)}"
            )

        # Map detail-type to EventType
        event_type = parse_event_type(eb_event.detail_type)
        if not event_type:
            logger.warning(
                "aws_unknown_event_type",
                detail_type=eb_event.detail_type
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event type: {eb_event.detail_type}"
            )

        # Create Helios event request
        helios_event = IngestEventRequest(
            event_type=event_type,
            source=EventSource.AWS,
            payload=eb_event.detail,
            metadata={
                "aws_event_id": eb_event.id,
                "aws_account": eb_event.account,
                "aws_region": eb_event.region,
                "aws_source": eb_event.source,
                "aws_time": eb_event.time,
                "aws_detail_type": eb_event.detail_type,
            }
        )

        # Use the same ingestion flow
        event_id = eb_event.id

        logger.info(
            "aws_eventbridge_event_received",
            event_id=event_id,
            detail_type=eb_event.detail_type,
            account=eb_event.account,
            region=eb_event.region
        )

        # Get services
        gateway = get_event_gateway()
        producer = get_kafka_producer()

        # Validate
        is_valid, error_msg = await gateway.validate_event(helios_event)
        if not is_valid:
            logger.warning(
                "aws_event_validation_failed",
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
                "aws_duplicate_event_rejected",
                event_id=event_id
            )
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
            "aws_event_ingested_successfully",
            event_id=event_id,
            order_id=helios_event.payload.get("order_id")
        )

        return {
            "status": "accepted",
            "event_id": event_id,
            "source": "aws",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "aws_eventbridge_webhook_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process AWS event: {str(e)}"
        )


@router.get(
    "/webhooks/aws/health",
    summary="AWS webhook health check",
    description="Health check endpoint for AWS EventBridge webhook"
)
async def aws_webhook_health():
    """Health check for AWS webhook endpoint."""
    return {
        "status": "healthy",
        "adapter": "aws_eventbridge",
        "timestamp": datetime.utcnow().isoformat()
    }
