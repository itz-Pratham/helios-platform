"""GCP Pub/Sub client for production use."""
import os
import json
from typing import Dict, Any, Optional
import structlog
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError

from .base import CloudClient

logger = structlog.get_logger()


class GCPPubSubClient(CloudClient):
    """Real GCP Pub/Sub client."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.topic_id = os.getenv("GCP_PUBSUB_TOPIC", "helios-events")
        self.publisher = None

    async def connect(self) -> None:
        """Initialize GCP Pub/Sub publisher."""
        try:
            self.publisher = pubsub_v1.PublisherClient()
            logger.info(
                "gcp_pubsub_client_initialized",
                project=self.project_id,
                topic=self.topic_id
            )
        except Exception as e:
            logger.error("gcp_pubsub_connection_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close GCP Pub/Sub client."""
        if self.publisher:
            # Flush any pending messages
            self.publisher.stop()
        self.publisher = None
        logger.info("gcp_pubsub_client_closed")

    def is_configured(self) -> bool:
        """Check if GCP credentials are configured."""
        # Check for service account key file or default credentials
        return bool(
            self.project_id and (
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or
                os.getenv("GCLOUD_PROJECT")
            )
        )

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish event to GCP Pub/Sub.

        Args:
            event_type: Event type (e.g., "OrderPlaced")
            payload: Event payload
            metadata: Optional metadata

        Returns:
            bool: True if successful
        """
        if not self.publisher:
            await self.connect()

        try:
            # Build topic path
            topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

            # Serialize payload
            message_data = json.dumps(payload).encode("utf-8")

            # Prepare attributes
            attributes = {
                "eventType": event_type,
                "source": "helios.platform"
            }

            # Add metadata to attributes if provided
            if metadata:
                for key, value in metadata.items():
                    attributes[f"meta_{key}"] = str(value)

            # Publish message
            future = self.publisher.publish(
                topic_path,
                data=message_data,
                **attributes
            )

            # Wait for result
            message_id = future.result(timeout=30)

            logger.info(
                "gcp_pubsub_event_published",
                event_type=event_type,
                topic=self.topic_id,
                message_id=message_id
            )
            return True

        except GoogleAPIError as e:
            logger.error(
                "gcp_pubsub_api_error",
                error_code=e.code,
                error_message=e.message
            )
            return False
        except Exception as e:
            logger.error("gcp_pubsub_unexpected_error", error=str(e))
            return False
