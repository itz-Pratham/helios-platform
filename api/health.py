"""Health check endpoints."""
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import structlog

from config import settings
from models import HealthCheckResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns the health status of the application and its dependencies"
)
async def health_check():
    """
    Comprehensive health check of all services.

    Returns:
        HealthCheckResponse: Health status of all components
    """
    services_status = {}

    # Check Postgres
    try:
        # TODO: Add actual database health check
        services_status["postgres"] = "healthy"
    except Exception as e:
        logger.error("postgres_health_check_failed", error=str(e))
        services_status["postgres"] = "unhealthy"

    # Check Redis
    try:
        # TODO: Add actual Redis health check
        services_status["redis"] = "healthy"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        services_status["redis"] = "unhealthy"

    # Check Kafka
    try:
        # TODO: Add actual Kafka health check
        services_status["kafka"] = "healthy"
    except Exception as e:
        logger.error("kafka_health_check_failed", error=str(e))
        services_status["kafka"] = "unhealthy"

    # Determine overall status
    overall_status = "healthy" if all(
        s == "healthy" for s in services_status.values()
    ) else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services=services_status
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint"
)
async def readiness_check():
    """
    Readiness probe for Kubernetes.

    Returns:
        dict: Simple readiness status
    """
    # TODO: Add actual readiness checks (DB connection, etc.)
    return {"ready": True}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint"
)
async def liveness_check():
    """
    Liveness probe for Kubernetes.

    Returns:
        dict: Simple liveness status
    """
    return {"alive": True}
