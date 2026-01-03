"""FastAPI application entrypoint."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from config import settings
from api.health import router as health_router
from api.routes import events as events_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(
        "starting_helios",
        version=settings.app_version,
        env=settings.env
    )

    # Initialize database
    from models import init_db
    await init_db()
    logger.info("database_initialized")

    # Initialize Redis/Event Gateway
    from services import get_event_gateway, get_kafka_producer
    gateway = get_event_gateway()
    await gateway.connect()
    logger.info("event_gateway_initialized")

    # Initialize Kafka producer (mock)
    producer = get_kafka_producer()
    await producer.connect()
    logger.info("kafka_producer_initialized")

    yield

    # Shutdown
    logger.info("shutting_down_helios")

    # Close Kafka producer
    await producer.close()
    logger.info("kafka_producer_closed")

    # Close Event Gateway
    await gateway.close()
    logger.info("event_gateway_closed")

    # Close database connections
    from models import close_db
    await close_db()
    logger.info("database_closed")

    # TODO: Close Kafka producer


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Cloud Event Reconciliation & Self-Healing Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(events_router.router, prefix="/api/v1", tags=["Events"])

# Include cloud adapter webhooks
from adapters import aws_eventbridge, gcp_pubsub, azure_eventgrid
app.include_router(aws_eventbridge.router, prefix="/api/v1", tags=["AWS Webhooks"])
app.include_router(gcp_pubsub.router, prefix="/api/v1", tags=["GCP Webhooks"])
app.include_router(azure_eventgrid.router, prefix="/api/v1", tags=["Azure Webhooks"])

# Include WebSocket and stats endpoints
from api.routes import websocket as websocket_router
app.include_router(websocket_router.router, prefix="/api/v1", tags=["WebSocket & Stats"])

# Include reconciliation endpoints
from api.routes import reconciliation
app.include_router(reconciliation.router, tags=["Reconciliation"])

# Include Phase 2 metrics endpoints
from api.routes import phase2_metrics
app.include_router(phase2_metrics.router, tags=["Phase 2 Metrics"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
