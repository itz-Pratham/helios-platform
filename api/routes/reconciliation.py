"""
Reconciliation API routes.

Endpoints for triggering and viewing event reconciliation results.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db, ReconciliationRepository
from services.reconciliation_engine import reconcile_recent_events, ReconciliationConfig

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


# Pydantic models for API
class ReconciliationTriggerRequest(BaseModel):
    """Request to trigger a reconciliation run."""

    window_minutes: Optional[int] = Field(30, ge=1, le=1440, description="Look back window in minutes (max 24 hours)")
    expected_sources: Optional[List[str]] = Field(None, description="List of expected sources (default: aws, gcp, azure)")


class ReconciliationSummary(BaseModel):
    """Summary of a reconciliation run."""

    run_id: str
    window_start: str
    window_end: str
    total_events: int
    consistent: int
    missing: int
    inconsistent: int
    duplicate: int
    avg_consistency_score: float
    duration_ms: int


class ReconciliationDetailResponse(BaseModel):
    """Detailed reconciliation result for a specific event."""

    id: str
    run_id: str
    event_id: str
    event_type: str
    status: str
    expected_sources: List[str]
    found_in_sources: List[str]
    missing_from_sources: List[str]
    event_instances: dict
    issues: List[dict]
    consistency_score: Optional[float]
    created_at: str


@router.post("/trigger", response_model=ReconciliationSummary)
async def trigger_reconciliation(
    request: ReconciliationTriggerRequest = ReconciliationTriggerRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a manual reconciliation run.

    This will compare events across all cloud sources within the specified time window
    and detect inconsistencies.

    **Response includes:**
    - Summary statistics (total events, issues found)
    - run_id for querying detailed results
    """
    try:
        result = await reconcile_recent_events(db, minutes=request.window_minutes)
        return ReconciliationSummary(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")


@router.get("/results", response_model=List[ReconciliationDetailResponse])
async def get_reconciliation_results(
    run_id: Optional[str] = Query(None, description="Filter by specific reconciliation run"),
    status: Optional[str] = Query(None, description="Filter by status (consistent, missing, inconsistent, duplicate)"),
    event_id: Optional[str] = Query(None, description="Filter by specific event_id"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get reconciliation results with optional filtering.

    **Filters:**
    - run_id: Get results from a specific reconciliation run
    - status: Filter by reconciliation status
    - event_id: Get results for a specific event

    **Status values:**
    - consistent: Event found in all sources with matching data
    - missing: Event missing from one or more sources
    - inconsistent: Event found but data mismatches
    - duplicate: Multiple copies of event in one source
    """
    repo = ReconciliationRepository(db)

    try:
        # Build filters
        filters = {}
        if run_id:
            filters["run_id"] = run_id
        if status:
            filters["status"] = status
        if event_id:
            filters["event_id"] = event_id

        results = await repo.find_by_filters(filters, limit=limit)

        return [
            ReconciliationDetailResponse(
                id=str(r.id),
                run_id=r.run_id,
                event_id=r.event_id,
                event_type=r.event_type,
                status=r.status,
                expected_sources=r.expected_sources,
                found_in_sources=r.found_in_sources or [],
                missing_from_sources=r.missing_from_sources or [],
                event_instances=r.event_instances or {},
                issues=r.issues or [],
                consistency_score=r.consistency_score,
                created_at=r.created_at.isoformat(),
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch results: {str(e)}")


@router.get("/summary")
async def get_reconciliation_summary(
    hours: int = Query(24, ge=1, le=168, description="Look back period in hours (max 7 days)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for reconciliation results over a time period.

    Returns aggregated statistics about event consistency.
    """
    repo = ReconciliationRepository(db)

    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        stats = await repo.get_summary_stats(since)

        return {
            "period_hours": hours,
            "since": since.isoformat(),
            "total_events_checked": stats.get("total", 0),
            "consistent": stats.get("consistent", 0),
            "missing": stats.get("missing", 0),
            "inconsistent": stats.get("inconsistent", 0),
            "duplicate": stats.get("duplicate", 0),
            "avg_consistency_score": stats.get("avg_score", 0.0),
            "consistency_percentage": stats.get("consistency_percentage", 0.0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/runs")
async def get_reconciliation_runs(
    limit: int = Query(10, ge=1, le=100, description="Number of runs to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of recent reconciliation runs with their summary statistics.
    """
    repo = ReconciliationRepository(db)

    try:
        runs = await repo.get_recent_runs(limit=limit)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch runs: {str(e)}")
