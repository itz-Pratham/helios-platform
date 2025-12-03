"""Azure Event Grid client for production use."""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from azure.eventgrid import EventGridPublisherClient
from azure.core.credentials import AzureKeyCredential
from azure.core.messaging import CloudEvent
from azure.core.exceptions import AzureError

from .base import CloudClient

logger = structlog.get_logger()


class AzureEventGridClient(CloudClient):
    """Real Azure Event Grid client."""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_EVENT_GRID_ENDPOINT")
        self.access_key = os.getenv("AZURE_EVENT_GRID_ACCESS_KEY")
        self.topic_hostname = os.getenv("AZURE_EVENT_GRID_TOPIC_HOSTNAME")
        self.subject_prefix = os.getenv("AZURE_EVENT_SUBJECT_PREFIX", "helios")
        self.client = None

    async def connect(self) -> None:
        """Initialize Azure Event Grid client."""
        try:
            if self.access_key:
                credential = AzureKeyCredential(self.access_key)
                self.client = EventGridPublisherClient(
                    self.endpoint,
                    credential
                )
            logger.info(
                "azure_eventgrid_client_initialized",
                endpoint=self.endpoint
            )
        except Exception as e:
            logger.error("azure_eventgrid_connection_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close Azure Event Grid client."""
        if self.client:
            self.client.close()
        self.client = None
        logger.info("azure_eventgrid_client_closed")

    def is_configured(self) -> bool:
        """Check if Azure credentials are configured."""
        return all([
            self.endpoint,
            self.access_key
        ])

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish event to Azure Event Grid.

        Args:
            event_type: Event type (e.g., "OrderPlaced")
            payload: Event payload
            metadata: Optional metadata

        Returns:
            bool: True if successful
        """
        if not self.client:
            await self.connect()

        try:
            # Create CloudEvent
            event = CloudEvent(
                type=f"Helios.{event_type}",
                source=f"{self.subject_prefix}/events",
                data=payload,
                subject=metadata.get("subject", f"{self.subject_prefix}/{event_type}") if metadata else f"{self.subject_prefix}/{event_type}"
            )

            # Publish event
            self.client.send([event])

            logger.info(
                "azure_eventgrid_event_published",
                event_type=event_type,
                endpoint=self.endpoint
            )
            return True

        except AzureError as e:
            logger.error(
                "azure_eventgrid_error",
                error=str(e)
            )
            return False
        except Exception as e:
            logger.error("azure_eventgrid_unexpected_error", error=str(e))
            return False
