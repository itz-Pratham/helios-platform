"""Base cloud client interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CloudClient(ABC):
    """Abstract base class for cloud clients."""

    @abstractmethod
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish an event to the cloud service.

        Args:
            event_type: Type of event (e.g., "OrderPlaced")
            payload: Event payload data
            metadata: Optional metadata

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to cloud service."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection to cloud service."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if client has valid configuration/credentials."""
        pass


class MockCloudClient(CloudClient):
    """Mock cloud client for demo mode."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._connected = False

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mock publish - just log the event."""
        import structlog
        logger = structlog.get_logger()
        logger.info(
            "mock_cloud_event_publish",
            service=self.service_name,
            event_type=event_type,
            payload=payload
        )
        return True

    async def connect(self) -> None:
        """Mock connect."""
        self._connected = True

    async def close(self) -> None:
        """Mock close."""
        self._connected = False

    def is_configured(self) -> bool:
        """Mock is always 'configured'."""
        return False  # Return False to indicate it's mock
