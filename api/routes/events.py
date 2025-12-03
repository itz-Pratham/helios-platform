"""Event ingestion and query endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from uuid import uuid4

from models import (
    IngestEventRequest,
    IngestEventResponse,
    get_db,
    EventRepository,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/events/ingest",
    response_model=IngestEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest event from cloud source",
    description="Accept and process events from AWS, GCP, or Azure"
)
async def ingest_event(
    request: IngestEventRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest an event from a cloud source.

    Args:
        request: Event ingestion request
        db: Database session

    Returns:
        IngestEventResponse: Ingestion confirmation
    """
    event_id = str(uuid4())

    logger.info(
        "event_received",
        event_id=event_id,
        source=request.source,
        event_type=request.event_type,
        order_id=request.payload.get("order_id")
    )

    try:
        # Import Event Gateway and Kafka Producer
        from services import get_event_gateway, get_kafka_producer
        gateway = get_event_gateway()
        producer = get_kafka_producer()

        # Validate event schema and business rules
        is_valid, error_msg = await gateway.validate_event(request)
        if not is_valid:
            logger.warning(
                "event_validation_failed",
                event_id=event_id,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event validation failed: {error_msg}"
            )

        # Check for duplicates using Redis
        if await gateway.is_duplicate(event_id):
            logger.warning(
                "duplicate_event_rejected",
                event_id=event_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate event: {event_id} already processed"
            )

        # Produce to Kafka (mock for now)
        topic_suffix = f"events.{request.event_type.value.lower()}"
        await producer.produce(
            topic_suffix=topic_suffix,
            event_id=event_id,
            event_type=request.event_type.value,
            payload=request.payload,
            metadata=request.metadata,
        )

        # Store to Postgres (order_id/customer_id auto-extracted by DB)
        event_repo = EventRepository(db)
        await event_repo.create(
            event_id=event_id,
            event_type=request.event_type.value,
            source=request.source.value,
            payload=request.payload,
            metadata=request.metadata,
        )

        await db.commit()

        # Mark event as processed in Redis (for deduplication)
        await gateway.mark_processed(event_id)

        logger.info(
            "event_persisted",
            event_id=event_id,
            order_id=request.payload.get("order_id")
        )

        # Broadcast to WebSocket clients
        try:
            from api.routes.websocket import broadcast_event
            await broadcast_event({
                "event_id": event_id,
                "event_type": request.event_type.value,
                "source": request.source.value,
                "payload": request.payload,
                "ingested_at": datetime.utcnow().isoformat(),
            })
        except Exception as ws_error:
            # Don't fail the request if WebSocket broadcast fails
            logger.warning("websocket_broadcast_failed", error=str(ws_error))

        return IngestEventResponse(
            event_id=event_id,
            status="accepted",
            message=f"Event {event_id} accepted and persisted",
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation, duplicate)
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "event_ingestion_failed",
            event_id=event_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}"
        )


# NOTE: Old reconciliation endpoints removed - now using /api/v1/reconciliation/* endpoints


@router.post(
    "/reconciliation/replay",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger manual replay for an order",
    description="Manually trigger event replay for a specific order"
)
async def trigger_manual_replay(order_id: str):
    """
    Manually trigger replay for an order.

    Args:
        order_id: Order identifier

    Returns:
        dict: Replay status
    """
    logger.info("manual_replay_triggered", order_id=order_id)

    try:
        # TODO: Trigger replay logic
        return {
            "order_id": order_id,
            "status": "replay_initiated",
            "message": f"Replay initiated for order {order_id}"
        }

    except Exception as e:
        logger.error(
            "manual_replay_failed",
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger replay: {str(e)}"
        )
