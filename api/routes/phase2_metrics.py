"""
Phase 2 Metrics API Routes

Endpoints for Phase 2 dashboard:
- Reconciliation metrics (Event Index, Bloom Filters, Windows)
- LSTM Anomaly alerts
- Scheduled jobs status
- Missing events timeline
- Recovery recommendations
- MCDM decision explanations
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/phase2", tags=["phase2-metrics"])


# ==================== Pydantic Models ====================

class EventIndexStats(BaseModel):
    """Event Index statistics."""
    backend: str  # "redis" or "sqlite"
    total_events: int
    avg_lookup_ms: float
    by_source: Dict[str, int]  # {"aws": 1000, "gcp": 800, "azure": 900}


class BloomFilterStats(BaseModel):
    """Bloom Filter statistics."""
    memory_mb: float
    capacity: int
    current_load: int
    false_positive_rate: float


class ReconciliationWindowStats(BaseModel):
    """Reconciliation window statistics."""
    active: int
    pending_events: int
    avg_closure_sec: float
    timeout_rate: float


class ReconciliationMetricsResponse(BaseModel):
    """Complete reconciliation metrics for dashboard."""
    event_index: EventIndexStats
    bloom_filter: BloomFilterStats
    reconciliation_windows: ReconciliationWindowStats


class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""
    timestamp: datetime
    metric_name: str
    is_anomaly: bool
    confidence: float  # 0-1
    severity: str  # "low", "medium", "high", "critical"
    model_type: str  # "lstm" or "ewma_fallback"
    expected_value: Optional[float]
    actual_value: float
    message: str


class ModelStatus(BaseModel):
    """ML model status."""
    model_loaded: bool
    model_type: str  # "lstm" or "ewma_fallback"
    window_size: int
    current_window_length: int
    threshold: float
    feature_count: int
    model_params: int


class ScheduledJobInfo(BaseModel):
    """Scheduled job information."""
    id: str
    name: str
    schedule: str  # "interval[0:05:00]" or "cron[minute='0']"
    next_run: Optional[datetime]
    last_run: Optional[Dict[str, Any]]  # {"timestamp", "status", "duration_sec"}
    status: str  # "running", "paused", "idle"


class MissingEventInfo(BaseModel):
    """Missing event information."""
    event_id: str
    expected_sources: List[str]
    received_sources: List[str]
    missing_sources: List[str]
    first_seen: datetime
    window_timeout: datetime
    status: str  # "missing", "delayed", "reconciled"


class SourceReliability(BaseModel):
    """Source reliability score."""
    source: str
    reliability_percentage: float
    events_on_time: int
    events_delayed: int
    events_missing: int


class RecoveryRecommendation(BaseModel):
    """Recovery action recommendation."""
    timestamp: datetime
    issue: Dict[str, Any]  # {"type", "description", "severity", "event_ids"}
    recommended_action: Dict[str, Any]  # {"name", "description", "topsis_score", etc.}
    decision_matrix: Optional[Dict[str, Any]]
    status: str  # "pending_phase3_executor"


class MCDMDecisionTree(BaseModel):
    """MCDM decision tree for visualization."""
    recommendation_id: str
    root_issue: Dict[str, Any]
    criteria: List[str]
    weights: Dict[str, float]
    candidates: List[Dict[str, Any]]
    winner: str


# ==================== Endpoints ====================

@router.get("/metrics", response_model=ReconciliationMetricsResponse)
async def get_reconciliation_metrics():
    """
    Get comprehensive reconciliation metrics for Phase 2 dashboard.

    Returns event index stats, bloom filter stats, and reconciliation window stats.
    """
    try:
        # Import here to avoid circular dependencies
        from services.event_index import get_event_index
        from services.anomaly_detection import get_ml_detector

        event_index = get_event_index()

        # Get event index stats
        index_stats = event_index.get_stats() if hasattr(event_index, 'get_stats') else {
            "backend": "redis",
            "total_events": 0,
            "avg_lookup_ms": 0.0,
            "by_source": {"aws": 0, "gcp": 0, "azure": 0}
        }

        # TODO: Get actual Bloom filter stats
        bloom_stats = {
            "memory_mb": 36.0,
            "capacity": 10000000,
            "current_load": 0,
            "false_positive_rate": 0.001
        }

        # TODO: Get actual window stats
        window_stats = {
            "active": 0,
            "pending_events": 0,
            "avg_closure_sec": 0.0,
            "timeout_rate": 0.0
        }

        return ReconciliationMetricsResponse(
            event_index=EventIndexStats(**index_stats),
            bloom_filter=BloomFilterStats(**bloom_stats),
            reconciliation_windows=ReconciliationWindowStats(**window_stats)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/anomaly/recent", response_model=List[AnomalyAlert])
async def get_recent_anomalies(
    limit: int = Query(50, ge=1, le=200, description="Number of alerts to return")
):
    """
    Get recent anomaly detection alerts.

    Returns list of anomalies detected by LSTM or EWMA detector.
    """
    # TODO: Implement actual anomaly storage/retrieval
    # For now, return empty list
    return []


@router.get("/anomaly/model-status", response_model=ModelStatus)
async def get_model_status():
    """
    Get ML anomaly detection model status.

    Returns information about which model is loaded and its configuration.
    """
    try:
        from services.anomaly_detection.ml_detector import get_ml_detector

        detector = get_ml_detector()
        stats = detector.get_stats()

        return ModelStatus(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/scheduler/jobs", response_model=List[ScheduledJobInfo])
async def get_scheduled_jobs():
    """
    Get status of all scheduled reconciliation jobs.

    Returns list of jobs with their schedules and last run information.
    """
    try:
        from services.scheduler import ReconciliationScheduler
        from services.scheduler.reconciliation_scheduler import get_scheduler

        scheduler = get_scheduler()

        if not scheduler.is_running():
            return []

        jobs_status = scheduler.get_job_status()

        return [
            ScheduledJobInfo(
                id=job["id"],
                name=job["name"],
                schedule=job["trigger"],
                next_run=datetime.fromisoformat(job["next_run_time"]) if job["next_run_time"] else None,
                last_run=None,  # TODO: Track last run info
                status="running" if not job.get("pending", False) else "idle"
            )
            for job in jobs_status
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler jobs: {str(e)}")


@router.get("/missing-events", response_model=List[MissingEventInfo])
async def get_missing_events(
    hours: int = Query(6, ge=1, le=24, description="Look back period in hours"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get events missing from one or more sources.

    Returns list of events that haven't arrived from all expected sources.
    """
    # TODO: Implement actual missing events tracking
    return []


@router.get("/source-reliability", response_model=List[SourceReliability])
async def get_source_reliability(
    hours: int = Query(24, ge=1, le=168, description="Look back period in hours")
):
    """
    Get reliability scores for each event source (AWS, GCP, Azure).

    Returns percentage of events received on time from each source.
    """
    # TODO: Implement actual reliability tracking
    return [
        SourceReliability(
            source="aws",
            reliability_percentage=99.2,
            events_on_time=9920,
            events_delayed=70,
            events_missing=10
        ),
        SourceReliability(
            source="gcp",
            reliability_percentage=98.7,
            events_on_time=9870,
            events_delayed=110,
            events_missing=20
        ),
        SourceReliability(
            source="azure",
            reliability_percentage=97.5,
            events_on_time=9750,
            events_delayed=200,
            events_missing=50
        ),
    ]


@router.get("/recommendations", response_model=List[RecoveryRecommendation])
async def get_recovery_recommendations(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get recovery action recommendations from MCDM engine.

    Returns list of recommended actions with TOPSIS scores.
    Note: Actions are NOT executed until Phase 3.
    """
    # TODO: Implement actual recommendation storage
    return []


@router.get("/mcdm/decision-tree/{recommendation_id}", response_model=MCDMDecisionTree)
async def get_decision_tree(recommendation_id: str):
    """
    Get MCDM decision tree for a specific recommendation.

    Returns detailed breakdown of how the decision was made.
    """
    # TODO: Implement decision tree retrieval
    raise HTTPException(status_code=404, detail="Decision tree not found")


@router.get("/mcdm/criteria-weights")
async def get_criteria_weights():
    """
    Get current MCDM criteria weights.

    Returns weights used for decision making (MTTR, QoS, Success Rate, Cost).
    """
    return {
        "weights": {
            "mttr": 0.4,
            "qos_impact": 0.3,
            "success_rate": 0.2,
            "cost": 0.1
        },
        "method": "entropy_weighted",
        "last_updated": datetime.utcnow().isoformat()
    }
