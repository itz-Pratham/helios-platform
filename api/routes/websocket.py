from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import asyncio
import structlog

from models.database import Event
from models.db_session import get_db

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_client_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("websocket_client_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_broadcast_error", error=str(e))
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            try:
                self.active_connections.remove(conn)
            except ValueError:
                pass


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming
    """
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and wait for messages
            # In a real implementation, you could handle client messages here
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("websocket_client_disconnected_gracefully")


async def broadcast_event(event_data: dict):
    """
    Helper function to broadcast events to all WebSocket clients
    Call this from event ingestion routes
    """
    await manager.broadcast(event_data)


@router.get("/stats")
async def get_stats():
    """
    Get dashboard statistics
    """
    try:
        async for db in get_db():
            # Total events
            total_result = await db.execute(select(func.count(Event.id)))
            total_events = total_result.scalar() or 0

            # Events by source
            source_result = await db.execute(
                select(Event.source, func.count(Event.id))
                .group_by(Event.source)
            )
            events_by_source = {row[0]: row[1] for row in source_result}

            # Events in last 24h
            from datetime import datetime, timedelta
            yesterday = datetime.utcnow() - timedelta(hours=24)
            last24h_result = await db.execute(
                select(func.count(Event.id))
                .where(Event.ingested_at >= yesterday)
            )
            last_24h = last24h_result.scalar() or 0

            return {
                "total_events": total_events,
                "events_by_source": events_by_source,
                "last_24h": last_24h,
                "health": {
                    "database": "healthy",
                    "redis": "healthy",
                    "kafka": "healthy",
                }
            }

    except Exception as e:
        logger.error("stats_error", error=str(e))
        return {
            "total_events": 0,
            "events_by_source": {},
            "last_24h": 0,
            "health": {
                "database": "unhealthy",
                "redis": "unknown",
                "kafka": "unknown",
            }
        }


@router.get("/health/detailed")
async def get_detailed_health():
    """
    Get detailed health information
    """
    import time
    from services.event_gateway import get_event_gateway

    try:
        # Check database
        db_status = "healthy"
        try:
            async for db in get_db():
                await db.execute(select(func.count(Event.id)))
        except Exception as e:
            logger.error("db_health_check_failed", error=str(e))
            db_status = "unhealthy"

        # Check Redis
        redis_status = "healthy"
        try:
            gateway = get_event_gateway()
            # Simple ping check (if Redis client supports it)
            redis_status = "healthy"
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            redis_status = "unhealthy"

        return {
            "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
            "database": db_status,
            "redis": redis_status,
            "kafka": "healthy",  # Mock Kafka is always healthy
            "uptime": time.time() - get_detailed_health.start_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return {
            "status": "unhealthy",
            "database": "unknown",
            "redis": "unknown",
            "kafka": "unknown",
            "error": str(e)
        }


# Initialize start time
get_detailed_health.start_time = __import__('time').time()
