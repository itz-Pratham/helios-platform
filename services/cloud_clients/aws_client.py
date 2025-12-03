"""AWS EventBridge client for production use."""
import os
from typing import Dict, Any, Optional
import structlog
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError

from .base import CloudClient

logger = structlog.get_logger()


class AWSEventBridgeClient(CloudClient):
    """Real AWS EventBridge client."""

    def __init__(self):
        self.event_bus_name = os.getenv("AWS_EVENTBRIDGE_BUS_NAME", "default")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.source = os.getenv("AWS_EVENT_SOURCE", "helios.platform")
        self.session = None
        self.client = None

    async def connect(self) -> None:
        """Initialize AWS EventBridge client."""
        try:
            self.session = aioboto3.Session()
            logger.info(
                "aws_eventbridge_client_initialized",
                event_bus=self.event_bus_name,
                region=self.region
            )
        except Exception as e:
            logger.error("aws_eventbridge_connection_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close AWS client."""
        self.client = None
        self.session = None
        logger.info("aws_eventbridge_client_closed")

    def is_configured(self) -> bool:
        """Check if AWS credentials are configured."""
        return all([
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("AWS_SECRET_ACCESS_KEY"),
        ])

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish event to AWS EventBridge.

        Args:
            event_type: Event type (e.g., "OrderPlaced")
            payload: Event payload
            metadata: Optional metadata

        Returns:
            bool: True if successful
        """
        if not self.session:
            await self.connect()

        try:
            async with self.session.client(
                "events",
                region_name=self.region
            ) as client:
                # Prepare EventBridge entry
                entry = {
                    "Source": self.source,
                    "DetailType": event_type,
                    "Detail": self._serialize_detail(payload),
                    "EventBusName": self.event_bus_name,
                }

                # Add metadata if provided
                if metadata:
                    entry["Resources"] = metadata.get("resources", [])

                # Publish event
                response = await client.put_events(Entries=[entry])

                # Check if successful
                if response.get("FailedEntryCount", 0) > 0:
                    failed = response.get("Entries", [{}])[0]
                    logger.error(
                        "aws_eventbridge_publish_failed",
                        error_code=failed.get("ErrorCode"),
                        error_message=failed.get("ErrorMessage")
                    )
                    return False

                logger.info(
                    "aws_eventbridge_event_published",
                    event_type=event_type,
                    event_bus=self.event_bus_name,
                    event_id=response.get("Entries", [{}])[0].get("EventId")
                )
                return True

        except NoCredentialsError:
            logger.error("aws_credentials_not_found")
            return False
        except ClientError as e:
            logger.error(
                "aws_eventbridge_client_error",
                error_code=e.response["Error"]["Code"],
                error_message=e.response["Error"]["Message"]
            )
            return False
        except Exception as e:
            logger.error("aws_eventbridge_unexpected_error", error=str(e))
            return False

    def _serialize_detail(self, payload: Dict[str, Any]) -> str:
        """Serialize payload to JSON string for EventBridge."""
        import json
        return json.dumps(payload, default=str)
