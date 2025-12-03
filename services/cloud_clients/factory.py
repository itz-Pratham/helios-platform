"""Cloud client factory with automatic mode detection."""
import os
import structlog
from typing import Optional

from .base import CloudClient, MockCloudClient
from .aws_client import AWSEventBridgeClient
from .gcp_client import GCPPubSubClient
from .azure_client import AzureEventGridClient

logger = structlog.get_logger()

# Singleton instances
_aws_client: Optional[CloudClient] = None
_gcp_client: Optional[CloudClient] = None
_azure_client: Optional[CloudClient] = None


def get_deployment_mode() -> str:
    """
    Get deployment mode from environment.

    Returns:
        str: "production" or "demo"
    """
    return os.getenv("DEPLOYMENT_MODE", "demo").lower()


def get_aws_client() -> CloudClient:
    """
    Get AWS EventBridge client.

    Auto-detects mode:
    - If AWS credentials are configured → Real AWS client
    - Otherwise → Mock client

    Returns:
        CloudClient: AWS client instance
    """
    global _aws_client

    if _aws_client is None:
        # Try to create real client
        real_client = AWSEventBridgeClient()

        # Check if credentials are configured
        if real_client.is_configured() and get_deployment_mode() == "production":
            _aws_client = real_client
            logger.info(
                "aws_client_mode",
                mode="production",
                event_bus=real_client.event_bus_name
            )
        else:
            _aws_client = MockCloudClient("AWS EventBridge")
            logger.info(
                "aws_client_mode",
                mode="demo",
                reason="No credentials configured" if not real_client.is_configured() else "Demo mode enabled"
            )

    return _aws_client


def get_gcp_client() -> CloudClient:
    """
    Get GCP Pub/Sub client.

    Auto-detects mode:
    - If GCP credentials are configured → Real GCP client
    - Otherwise → Mock client

    Returns:
        CloudClient: GCP client instance
    """
    global _gcp_client

    if _gcp_client is None:
        # Try to create real client
        real_client = GCPPubSubClient()

        # Check if credentials are configured
        if real_client.is_configured() and get_deployment_mode() == "production":
            _gcp_client = real_client
            logger.info(
                "gcp_client_mode",
                mode="production",
                project=real_client.project_id,
                topic=real_client.topic_id
            )
        else:
            _gcp_client = MockCloudClient("GCP Pub/Sub")
            logger.info(
                "gcp_client_mode",
                mode="demo",
                reason="No credentials configured" if not real_client.is_configured() else "Demo mode enabled"
            )

    return _gcp_client


def get_azure_client() -> CloudClient:
    """
    Get Azure Event Grid client.

    Auto-detects mode:
    - If Azure credentials are configured → Real Azure client
    - Otherwise → Mock client

    Returns:
        CloudClient: Azure client instance
    """
    global _azure_client

    if _azure_client is None:
        # Try to create real client
        real_client = AzureEventGridClient()

        # Check if credentials are configured
        if real_client.is_configured() and get_deployment_mode() == "production":
            _azure_client = real_client
            logger.info(
                "azure_client_mode",
                mode="production",
                endpoint=real_client.endpoint
            )
        else:
            _azure_client = MockCloudClient("Azure Event Grid")
            logger.info(
                "azure_client_mode",
                mode="demo",
                reason="No credentials configured" if not real_client.is_configured() else "Demo mode enabled"
            )

    return _azure_client


def reset_clients():
    """Reset all client singletons (useful for testing)."""
    global _aws_client, _gcp_client, _azure_client
    _aws_client = None
    _gcp_client = None
    _azure_client = None
