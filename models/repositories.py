"""Repository layer for database operations."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.database import Event, ReconciliationResult, SelfHealingAction, ReplayHistory

logger = structlog.get_logger()


class EventRepository:
    """Repository for Event operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        event_id: str,
        event_type: str,
        source: str,
        payload: dict,
        metadata: Optional[dict] = None,
    ) -> Event:
        """Create a new event."""
        event = Event(
            event_id=event_id,
            event_type=event_type,
            source=source,
            payload=payload,
            event_metadata=metadata or {},
        )
        self.db.add(event)
        await self.db.flush()
        logger.info(
            "event_created",
            event_id=event_id,
            event_type=event_type,
            source=source,
        )
        return event

    async def get_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by event_id."""
        result = await self.db.execute(
            select(Event).where(Event.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_id(
        self, order_id: str, event_type: Optional[str] = None
    ) -> List[Event]:
        """Get all events for an order_id."""
        query = select(Event).where(Event.order_id == order_id)
        if event_type:
            query = query.where(Event.event_type == event_type)
        query = query.order_by(Event.ingested_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def exists(self, event_id: str) -> bool:
        """Check if event exists."""
        result = await self.db.execute(
            select(Event.id).where(Event.event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def mark_processed(self, event_id: str) -> None:
        """Mark event as processed."""
        result = await self.db.execute(
            select(Event).where(Event.event_id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.processed_at = datetime.utcnow()
            await self.db.flush()


class ReconciliationRepository:
    """Repository for ReconciliationResult operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_filters(
        self,
        filters: dict,
        limit: int = 100,
    ) -> List[ReconciliationResult]:
        """Find reconciliation results by filters."""
        query = select(ReconciliationResult)

        # Apply filters
        if "run_id" in filters:
            query = query.where(ReconciliationResult.run_id == filters["run_id"])
        if "status" in filters:
            query = query.where(ReconciliationResult.status == filters["status"])
        if "event_id" in filters:
            query = query.where(ReconciliationResult.event_id == filters["event_id"])

        query = query.order_by(desc(ReconciliationResult.created_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_summary_stats(self, since: datetime) -> dict:
        """Get summary statistics for reconciliation results."""
        from sqlalchemy import func

        # Get counts by status
        result = await self.db.execute(
            select(
                ReconciliationResult.status,
                func.count(ReconciliationResult.id).label("count"),
                func.avg(ReconciliationResult.consistency_score).label("avg_score"),
            )
            .where(ReconciliationResult.created_at >= since)
            .group_by(ReconciliationResult.status)
        )

        rows = result.fetchall()

        stats = {
            "total": 0,
            "consistent": 0,
            "missing": 0,
            "inconsistent": 0,
            "duplicate": 0,
            "avg_score": 0.0,
        }

        total_score = 0.0
        total_with_score = 0

        for row in rows:
            status, count, avg_score = row
            stats["total"] += count
            stats[status] = count

            if avg_score is not None:
                total_score += avg_score * count
                total_with_score += count

        # Calculate overall average score
        if total_with_score > 0:
            stats["avg_score"] = total_score / total_with_score

        # Calculate consistency percentage
        if stats["total"] > 0:
            stats["consistency_percentage"] = (stats["consistent"] / stats["total"]) * 100

        return stats

    async def get_recent_runs(self, limit: int = 10) -> List[dict]:
        """Get list of recent reconciliation runs with summary."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                ReconciliationResult.run_id,
                func.min(ReconciliationResult.window_start).label("window_start"),
                func.max(ReconciliationResult.window_end).label("window_end"),
                func.count(ReconciliationResult.id).label("total_events"),
                func.sum(
                    func.case((ReconciliationResult.status == "consistent", 1), else_=0)
                ).label("consistent"),
                func.sum(
                    func.case((ReconciliationResult.status == "missing", 1), else_=0)
                ).label("missing"),
                func.sum(
                    func.case((ReconciliationResult.status == "inconsistent", 1), else_=0)
                ).label("inconsistent"),
                func.sum(
                    func.case((ReconciliationResult.status == "duplicate", 1), else_=0)
                ).label("duplicate"),
                func.avg(ReconciliationResult.consistency_score).label("avg_score"),
                func.min(ReconciliationResult.created_at).label("created_at"),
            )
            .group_by(ReconciliationResult.run_id)
            .order_by(desc("created_at"))
            .limit(limit)
        )

        rows = result.fetchall()

        return [
            {
                "run_id": row.run_id,
                "window_start": row.window_start.isoformat(),
                "window_end": row.window_end.isoformat(),
                "total_events": row.total_events,
                "consistent": row.consistent or 0,
                "missing": row.missing or 0,
                "inconsistent": row.inconsistent or 0,
                "duplicate": row.duplicate or 0,
                "avg_consistency_score": float(row.avg_score) if row.avg_score else 0.0,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


class SelfHealingRepository:
    """Repository for SelfHealingAction operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        action_type: str,
        trigger_reason: str,
        target: dict,
        triggered_by: str = "auto",
    ) -> SelfHealingAction:
        """Create self-healing action."""
        action = SelfHealingAction(
            action_type=action_type,
            trigger_reason=trigger_reason,
            target=target,
            triggered_by=triggered_by,
            status="pending",
        )
        self.db.add(action)
        await self.db.flush()
        logger.info(
            "self_healing_action_created",
            action_type=action_type,
            trigger_reason=trigger_reason,
        )
        return action

    async def mark_completed(
        self,
        action_id: UUID,
        success: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
    ) -> None:
        """Mark action as completed."""
        result = await self.db.execute(
            select(SelfHealingAction).where(SelfHealingAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if action:
            action.status = "completed" if success else "failed"
            action.completed_at = datetime.utcnow()
            action.duration_ms = duration_ms
            action.success = success
            action.error_message = error_message
            await self.db.flush()


class ReplayRepository:
    """Repository for ReplayHistory operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        replay_id: str,
        start_time: datetime,
        end_time: datetime,
        target_env: str,
        filters: Optional[dict] = None,
        initiated_by: str = "system",
    ) -> ReplayHistory:
        """Create replay history entry."""
        replay = ReplayHistory(
            replay_id=replay_id,
            start_time=start_time,
            end_time=end_time,
            filters=filters or {},
            target_env=target_env,
            initiated_by=initiated_by,
            status="pending",
        )
        self.db.add(replay)
        await self.db.flush()
        logger.info(
            "replay_created",
            replay_id=replay_id,
            target_env=target_env,
        )
        return replay

    async def get_by_replay_id(self, replay_id: str) -> Optional[ReplayHistory]:
        """Get replay by replay_id."""
        result = await self.db.execute(
            select(ReplayHistory).where(ReplayHistory.replay_id == replay_id)
        )
        return result.scalar_one_or_none()

    async def mark_completed(
        self, replay_id: str, events_count: int, success: bool
    ) -> None:
        """Mark replay as completed."""
        result = await self.db.execute(
            select(ReplayHistory).where(ReplayHistory.replay_id == replay_id)
        )
        replay = result.scalar_one_or_none()
        if replay:
            replay.status = "completed" if success else "failed"
            replay.completed_at = datetime.utcnow()
            replay.events_count = events_count
            await self.db.flush()
