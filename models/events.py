"""Pydantic models for events."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


class EventSource(str, Enum):
    """Event source cloud provider."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class EventType(str, Enum):
    """Event types."""
    ORDER_PLACED = "OrderPlaced"
    PAYMENT_PROCESSED = "PaymentProcessed"
    INVENTORY_RESERVED = "InventoryReserved"
    SHIPMENT_CREATED = "ShipmentCreated"
    ORDER_CANCELLED = "OrderCancelled"
    REFUND_PROCESSED = "RefundProcessed"


class OrderItem(BaseModel):
    """Order item details."""
    product_id: str = Field(..., description="Product SKU or ID")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    price: float = Field(..., gt=0, description="Unit price")

    @property
    def total(self) -> float:
        """Calculate total price for this item."""
        return self.quantity * self.price


class EventMetadata(BaseModel):
    """Event metadata."""
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    order_id: Optional[str] = Field(None, description="Order ID for correlation")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source: EventSource = Field(..., description="Cloud source")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID")


class OrderPlacedPayload(BaseModel):
    """Payload for OrderPlaced event."""
    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer identifier")
    items: List[OrderItem] = Field(..., min_length=1, description="Order items")
    total_amount: float = Field(..., gt=0, description="Total order amount")
    currency: str = Field(default="USD", description="Currency code")
    discount_code: Optional[str] = Field(None, description="Applied discount code")

    @property
    def calculated_total(self) -> float:
        """Calculate total from items."""
        return sum(item.total for item in self.items)


class PaymentProcessedPayload(BaseModel):
    """Payload for PaymentProcessed event."""
    order_id: str = Field(..., description="Order identifier")
    payment_id: str = Field(..., description="Payment transaction ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", description="Currency code")
    payment_method: str = Field(..., description="Payment method (card, paypal, etc)")
    status: str = Field(..., description="Payment status (authorized, captured, failed)")


class InventoryReservedPayload(BaseModel):
    """Payload for InventoryReserved event."""
    order_id: str = Field(..., description="Order identifier")
    warehouse_id: str = Field(..., description="Warehouse location")
    items: List[OrderItem] = Field(..., min_length=1, description="Reserved items")
    reservation_id: str = Field(..., description="Inventory reservation ID")
    expires_at: datetime = Field(..., description="Reservation expiry time")


class ShipmentCreatedPayload(BaseModel):
    """Payload for ShipmentCreated event."""
    order_id: str = Field(..., description="Order identifier")
    shipment_id: str = Field(..., description="Shipment tracking ID")
    carrier: str = Field(..., description="Shipping carrier")
    tracking_number: str = Field(..., description="Tracking number")
    estimated_delivery: datetime = Field(..., description="Estimated delivery date")


class Event(BaseModel):
    """Generic event wrapper."""
    metadata: EventMetadata = Field(..., description="Event metadata")
    event_type: EventType = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(..., description="Event payload")

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class IngestEventRequest(BaseModel):
    """API request to ingest an event."""
    source: EventSource = Field(..., description="Cloud source")
    event_type: EventType = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class IngestEventResponse(BaseModel):
    """API response for event ingestion."""
    event_id: str = Field(..., description="Generated event ID")
    status: str = Field(..., description="Ingestion status")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReconciliationStatus(str, Enum):
    """Reconciliation status."""
    PENDING = "pending"
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    PARTIAL = "partial"


class ReconciliationResult(BaseModel):
    """Reconciliation result for an order."""
    order_id: str = Field(..., description="Order ID")
    status: ReconciliationStatus = Field(..., description="Reconciliation status")
    window_start: datetime = Field(..., description="Reconciliation window start")
    window_end: datetime = Field(..., description="Reconciliation window end")
    events: Dict[str, Optional[Event]] = Field(..., description="Events by type")
    missing_events: List[str] = Field(default_factory=list, description="Missing event types")
    validation_errors: Dict[str, Any] = Field(default_factory=dict, description="Validation errors")
    reconciled_at: Optional[datetime] = Field(None, description="Reconciliation timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(..., description="Service health status")
