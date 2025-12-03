"""Data models module."""
from models.events import (
    Event as EventModel,
    EventSource,
    EventType,
    EventMetadata,
    OrderPlacedPayload,
    PaymentProcessedPayload,
    InventoryReservedPayload,
    ShipmentCreatedPayload,
    IngestEventRequest,
    IngestEventResponse,
    ReconciliationStatus,
    ReconciliationResult as ReconciliationResultModel,
    HealthCheckResponse,
)

from models.database import (
    Base,
    Event as DBEvent,
    ReconciliationResult as DBReconciliationResult,
    SelfHealingAction,
    ReplayHistory,
)

from models.db_session import (
    get_db,
    init_db,
    close_db,
    engine,
    AsyncSessionLocal,
)

from models.repositories import (
    EventRepository,
    ReconciliationRepository,
    SelfHealingRepository,
    ReplayRepository,
)

__all__ = [
    # Pydantic models
    "EventModel",
    "EventSource",
    "EventType",
    "EventMetadata",
    "OrderPlacedPayload",
    "PaymentProcessedPayload",
    "InventoryReservedPayload",
    "ShipmentCreatedPayload",
    "IngestEventRequest",
    "IngestEventResponse",
    "ReconciliationStatus",
    "ReconciliationResultModel",
    "HealthCheckResponse",
    # Database models
    "Base",
    "DBEvent",
    "DBReconciliationResult",
    "SelfHealingAction",
    "ReplayHistory",
    # Session
    "get_db",
    "init_db",
    "close_db",
    "engine",
    "AsyncSessionLocal",
    # Repositories
    "EventRepository",
    "ReconciliationRepository",
    "SelfHealingRepository",
    "ReplayRepository",
]
