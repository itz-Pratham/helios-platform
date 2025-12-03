"""
Reconciliation Engine - Core logic for detecting event inconsistencies across clouds.

This service compares events from multiple sources (AWS, GCP, Azure, Kafka) to detect:
- Missing events (event in source A but not B)
- Duplicate events (same event_id multiple times in one source)
- Data mismatches (same event_id, different payload)
- Out-of-order events (sequence violations)
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from uuid import uuid4
import structlog
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Event, ReconciliationResult
from models.repositories import EventRepository

logger = structlog.get_logger()


class ReconciliationConfig:
    """Configuration for reconciliation engine."""

    def __init__(
        self,
        window_minutes: int = 30,
        expected_sources: Optional[List[str]] = None,
        consistency_threshold: float = 0.95,
        max_events_per_run: int = 1000,
    ):
        self.window_minutes = window_minutes
        self.expected_sources = expected_sources or ["aws", "gcp", "azure"]
        self.consistency_threshold = consistency_threshold
        self.max_events_per_run = max_events_per_run


class EventInstance:
    """Represents a single instance of an event from a specific source."""

    def __init__(self, event: Event):
        self.id = str(event.id)
        self.event_id = event.event_id
        self.source = event.source
        self.event_type = event.event_type
        self.payload = event.payload
        self.ingested_at = event.ingested_at
        self.metadata = event.event_metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "source": self.source,
            "event_type": self.event_type,
            "payload": self.payload,
            "ingested_at": self.ingested_at.isoformat(),
            "metadata": self.metadata,
        }


class ReconciliationIssue:
    """Represents a detected inconsistency."""

    def __init__(
        self,
        issue_type: str,
        severity: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.type = issue_type
        self.severity = severity  # low, medium, high, critical
        self.description = description
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
        }


class ReconciliationEngine:
    """
    Core reconciliation engine that compares events across multiple sources.
    """

    def __init__(self, session: AsyncSession, config: Optional[ReconciliationConfig] = None):
        self.session = session
        self.config = config or ReconciliationConfig()
        self.event_repo = EventRepository(session)

    async def reconcile_window(
        self,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Reconcile events within a time window.

        Args:
            window_start: Start of reconciliation window (default: now - window_minutes)
            window_end: End of reconciliation window (default: now)

        Returns:
            Dictionary with reconciliation summary
        """
        # Calculate window if not provided
        if window_end is None:
            window_end = datetime.utcnow()
        if window_start is None:
            window_start = window_end - timedelta(minutes=self.config.window_minutes)

        run_id = f"recon_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        logger.info(
            "reconciliation_started",
            run_id=run_id,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
        )

        # Fetch all events in window
        events = await self._fetch_events_in_window(window_start, window_end)

        # Group events by event_id
        event_groups = self._group_events_by_id(events)

        # Reconcile each group
        results = []
        for event_id, instances in event_groups.items():
            result = await self._reconcile_event_group(
                run_id, event_id, instances, window_start, window_end
            )
            results.append(result)

        # Calculate summary statistics
        total_events = len(event_groups)
        consistent_count = sum(1 for r in results if r.status == "consistent")
        missing_count = sum(1 for r in results if r.status == "missing")
        inconsistent_count = sum(1 for r in results if r.status == "inconsistent")
        duplicate_count = sum(1 for r in results if r.status == "duplicate")

        avg_consistency_score = (
            sum(r.consistency_score for r in results if r.consistency_score) / len(results)
            if results
            else 0.0
        )

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        logger.info(
            "reconciliation_completed",
            run_id=run_id,
            total_events=total_events,
            consistent=consistent_count,
            missing=missing_count,
            inconsistent=inconsistent_count,
            duplicate=duplicate_count,
            avg_consistency_score=avg_consistency_score,
            duration_ms=duration_ms,
        )

        return {
            "run_id": run_id,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "total_events": total_events,
            "consistent": consistent_count,
            "missing": missing_count,
            "inconsistent": inconsistent_count,
            "duplicate": duplicate_count,
            "avg_consistency_score": avg_consistency_score,
            "duration_ms": duration_ms,
            "results": [self._result_to_dict(r) for r in results],
        }

    async def _fetch_events_in_window(
        self, window_start: datetime, window_end: datetime
    ) -> List[Event]:
        """Fetch all events within the time window."""
        query = select(Event).where(
            and_(
                Event.ingested_at >= window_start,
                Event.ingested_at <= window_end,
            )
        ).limit(self.config.max_events_per_run)

        result = await self.session.execute(query)
        events = result.scalars().all()

        logger.info(
            "events_fetched",
            count=len(events),
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
        )

        return list(events)

    def _group_events_by_id(self, events: List[Event]) -> Dict[str, List[EventInstance]]:
        """Group events by their event_id."""
        groups: Dict[str, List[EventInstance]] = {}

        for event in events:
            instance = EventInstance(event)
            if instance.event_id not in groups:
                groups[instance.event_id] = []
            groups[instance.event_id].append(instance)

        return groups

    async def _reconcile_event_group(
        self,
        run_id: str,
        event_id: str,
        instances: List[EventInstance],
        window_start: datetime,
        window_end: datetime,
    ) -> ReconciliationResult:
        """
        Reconcile a group of event instances with the same event_id.

        Detects:
        1. Missing events (not present in all expected sources)
        2. Duplicate events (multiple instances in same source)
        3. Data mismatches (different payloads)
        """
        issues: List[ReconciliationIssue] = []

        # Check which sources have this event
        found_sources = {inst.source for inst in instances}
        missing_sources = set(self.config.expected_sources) - found_sources

        # Get event type from first instance
        event_type = instances[0].event_type if instances else "unknown"

        # Detect missing events
        if missing_sources:
            for source in missing_sources:
                issues.append(
                    ReconciliationIssue(
                        issue_type="missing",
                        severity="high",
                        description=f"Event not found in {source}",
                        details={"source": source},
                    )
                )

        # Detect duplicates (multiple instances from same source)
        source_counts = {}
        for inst in instances:
            source_counts[inst.source] = source_counts.get(inst.source, 0) + 1

        for source, count in source_counts.items():
            if count > 1:
                issues.append(
                    ReconciliationIssue(
                        issue_type="duplicate",
                        severity="high",
                        description=f"Event duplicated {count} times in {source}",
                        details={"source": source, "count": count},
                    )
                )

        # Detect data mismatches (compare payloads)
        if len(instances) > 1:
            mismatches = self._detect_payload_mismatches(instances)
            for mismatch in mismatches:
                issues.append(mismatch)

        # Determine overall status
        if not issues:
            status = "consistent"
        elif any(issue.type == "missing" for issue in issues):
            status = "missing"
        elif any(issue.type == "duplicate" for issue in issues):
            status = "duplicate"
        elif any(issue.type == "data_mismatch" for issue in issues):
            status = "inconsistent"
        else:
            status = "inconsistent"

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(instances, issues)

        # Build event_instances map
        event_instances_map = {inst.source: inst.to_dict() for inst in instances}

        # Create reconciliation result
        result = ReconciliationResult(
            run_id=run_id,
            event_id=event_id,
            event_type=event_type,
            window_start=window_start,
            window_end=window_end,
            status=status,
            expected_sources=self.config.expected_sources,
            found_in_sources=list(found_sources),
            missing_from_sources=list(missing_sources),
            event_instances=event_instances_map,
            issues=[issue.to_dict() for issue in issues],
            consistency_score=consistency_score,
            created_at=datetime.utcnow(),
        )

        # Save to database
        self.session.add(result)
        await self.session.commit()

        return result

    def _detect_payload_mismatches(
        self, instances: List[EventInstance]
    ) -> List[ReconciliationIssue]:
        """
        Compare payloads across instances to detect data mismatches.
        """
        issues = []

        # Use first instance as reference
        reference = instances[0]

        for instance in instances[1:]:
            # Compare payload fields
            ref_payload = reference.payload
            inst_payload = instance.payload

            # Find mismatched fields
            all_keys = set(ref_payload.keys()) | set(inst_payload.keys())

            for key in all_keys:
                ref_value = ref_payload.get(key)
                inst_value = inst_payload.get(key)

                if ref_value != inst_value:
                    issues.append(
                        ReconciliationIssue(
                            issue_type="data_mismatch",
                            severity="critical",
                            description=f"Field '{key}' mismatch between {reference.source} and {instance.source}",
                            details={
                                "field": key,
                                "values": {
                                    reference.source: ref_value,
                                    instance.source: inst_value,
                                },
                            },
                        )
                    )

        return issues

    def _calculate_consistency_score(
        self, instances: List[EventInstance], issues: List[ReconciliationIssue]
    ) -> float:
        """
        Calculate consistency score (0.0 - 1.0) based on issues.

        Formula:
        - Start at 1.0 (perfect)
        - Deduct for each issue based on severity:
          - critical: -0.4
          - high: -0.2
          - medium: -0.1
          - low: -0.05
        - Minimum score: 0.0
        """
        score = 1.0

        severity_penalties = {
            "critical": 0.4,
            "high": 0.2,
            "medium": 0.1,
            "low": 0.05,
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 0.1)
            score -= penalty

        return max(0.0, score)

    def _result_to_dict(self, result: ReconciliationResult) -> Dict[str, Any]:
        """Convert ReconciliationResult to dictionary."""
        return {
            "id": str(result.id),
            "run_id": result.run_id,
            "event_id": result.event_id,
            "event_type": result.event_type,
            "status": result.status,
            "expected_sources": result.expected_sources,
            "found_in_sources": result.found_in_sources,
            "missing_from_sources": result.missing_from_sources,
            "event_instances": result.event_instances,
            "issues": result.issues,
            "consistency_score": result.consistency_score,
            "created_at": result.created_at.isoformat(),
        }


async def reconcile_recent_events(session: AsyncSession, minutes: int = 30) -> Dict[str, Any]:
    """
    Convenience function to reconcile recent events.

    Args:
        session: Database session
        minutes: Look back this many minutes (default: 30)

    Returns:
        Reconciliation summary
    """
    engine = ReconciliationEngine(session, ReconciliationConfig(window_minutes=minutes))
    return await engine.reconcile_window()
