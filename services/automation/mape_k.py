"""
MAPE-K Closed-Loop Automation

Implements the MAPE-K (Monitor-Analyze-Plan-Execute-Knowledge) cycle
for autonomous self-healing cloud event reconciliation.

Based on IBM's autonomic computing architecture.

Phases:
1. Monitor: Collect metrics and detect anomalies
2. Analyze: Determine root cause and impact
3. Plan: Select optimal recovery action using MCDM
4. Execute: Execute recovery action
5. Knowledge: Learn from outcome and update models
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger()


class MAPEKPhase(Enum):
    """MAPE-K cycle phases."""
    MONITOR = "monitor"
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    KNOWLEDGE = "knowledge"


@dataclass
class MonitoringData:
    """
    Data collected during Monitor phase.

    Attributes:
        event_id: Event identifier
        sources_found: Sources where event was found
        sources_missing: Sources where event is missing
        metrics: System metrics
        timestamp: When monitoring occurred
    """
    event_id: str
    sources_found: List[str]
    sources_missing: List[str]
    metrics: Dict[str, float]
    timestamp: datetime


@dataclass
class AnalysisResult:
    """
    Result from Analyze phase.

    Attributes:
        event_id: Event identifier
        root_cause: Identified root cause
        impact_severity: Impact severity (0-1)
        recommended_actions: Recommended recovery actions
        analysis_timestamp: When analysis occurred
    """
    event_id: str
    root_cause: str
    impact_severity: float
    recommended_actions: List[str]
    analysis_timestamp: datetime


@dataclass
class RecoveryPlan:
    """
    Plan from Plan phase.

    Attributes:
        event_id: Event identifier
        selected_action: Selected recovery action
        action_score: MCDM score for selected action
        alternative_actions: Alternative actions considered
        plan_timestamp: When plan was created
    """
    event_id: str
    selected_action: str
    action_score: float
    alternative_actions: List[Dict[str, float]]
    plan_timestamp: datetime


@dataclass
class ExecutionResult:
    """
    Result from Execute phase.

    Attributes:
        event_id: Event identifier
        action_id: Executed action
        success: Whether execution succeeded
        execution_time: Time taken (seconds)
        cost: Cost incurred
        error_message: Error if failed
        execution_timestamp: When execution occurred
    """
    event_id: str
    action_id: str
    success: bool
    execution_time: float
    cost: float
    error_message: Optional[str]
    execution_timestamp: datetime


class MAPEKLoop:
    """
    MAPE-K closed-loop automation engine.

    Orchestrates the full autonomic computing cycle:
    Monitor → Analyze → Plan → Execute → Knowledge → Monitor → ...
    """

    def __init__(
        self,
        monitor_callback: Optional[Callable] = None,
        analyze_callback: Optional[Callable] = None,
        plan_callback: Optional[Callable] = None,
        execute_callback: Optional[Callable] = None,
        knowledge_callback: Optional[Callable] = None
    ):
        """
        Initialize MAPE-K loop.

        Args:
            monitor_callback: Custom monitor phase handler
            analyze_callback: Custom analyze phase handler
            plan_callback: Custom plan phase handler
            execute_callback: Custom execute phase handler
            knowledge_callback: Custom knowledge phase handler
        """
        self.monitor_callback = monitor_callback
        self.analyze_callback = analyze_callback
        self.plan_callback = plan_callback
        self.execute_callback = execute_callback
        self.knowledge_callback = knowledge_callback

        # Phase execution history
        self.execution_history: List[Dict[str, Any]] = []

        # Current phase
        self.current_phase: Optional[MAPEKPhase] = None

        # Statistics
        self.cycles_completed = 0
        self.cycles_succeeded = 0
        self.cycles_failed = 0

        logger.info("mape_k_loop_initialized")

    async def run_cycle(
        self,
        event_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run complete MAPE-K cycle for event.

        Args:
            event_id: Event to process
            context: Additional context

        Returns:
            Cycle result dictionary
        """
        cycle_start = datetime.utcnow()
        context = context or {}

        logger.info(
            "mape_k_cycle_started",
            event_id=event_id,
            cycle_number=self.cycles_completed + 1
        )

        cycle_result = {
            "event_id": event_id,
            "cycle_number": self.cycles_completed + 1,
            "phases": {},
            "success": False,
            "start_time": cycle_start.isoformat()
        }

        try:
            # Phase 1: Monitor
            monitoring_data = await self._monitor_phase(event_id, context)
            cycle_result["phases"]["monitor"] = monitoring_data
            logger.info("mape_k_phase_completed", phase="monitor", event_id=event_id)

            # Phase 2: Analyze
            analysis_result = await self._analyze_phase(monitoring_data, context)
            cycle_result["phases"]["analyze"] = analysis_result
            logger.info("mape_k_phase_completed", phase="analyze", event_id=event_id)

            # Phase 3: Plan
            recovery_plan = await self._plan_phase(analysis_result, context)
            cycle_result["phases"]["plan"] = recovery_plan
            logger.info("mape_k_phase_completed", phase="plan", event_id=event_id)

            # Phase 4: Execute
            execution_result = await self._execute_phase(recovery_plan, context)
            cycle_result["phases"]["execute"] = execution_result
            logger.info("mape_k_phase_completed", phase="execute", event_id=event_id)

            # Phase 5: Knowledge
            knowledge_update = await self._knowledge_phase(
                monitoring_data,
                analysis_result,
                recovery_plan,
                execution_result,
                context
            )
            cycle_result["phases"]["knowledge"] = knowledge_update
            logger.info("mape_k_phase_completed", phase="knowledge", event_id=event_id)

            # Mark cycle as successful
            cycle_result["success"] = execution_result.get("success", False)
            if cycle_result["success"]:
                self.cycles_succeeded += 1
            else:
                self.cycles_failed += 1

        except Exception as e:
            logger.error(
                "mape_k_cycle_failed",
                event_id=event_id,
                error=str(e),
                phase=self.current_phase.value if self.current_phase else "unknown"
            )
            cycle_result["error"] = str(e)
            cycle_result["failed_phase"] = self.current_phase.value if self.current_phase else "unknown"
            self.cycles_failed += 1

        finally:
            cycle_end = datetime.utcnow()
            cycle_duration = (cycle_end - cycle_start).total_seconds()
            cycle_result["end_time"] = cycle_end.isoformat()
            cycle_result["duration_seconds"] = cycle_duration

            self.cycles_completed += 1
            self.execution_history.append(cycle_result)

            # Keep only recent history
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]

            logger.info(
                "mape_k_cycle_completed",
                event_id=event_id,
                success=cycle_result["success"],
                duration=round(cycle_duration, 3),
                cycles_completed=self.cycles_completed
            )

        return cycle_result

    async def _monitor_phase(
        self,
        event_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Monitor phase: Collect metrics and detect anomalies.

        Args:
            event_id: Event to monitor
            context: Context data

        Returns:
            Monitoring data
        """
        self.current_phase = MAPEKPhase.MONITOR

        if self.monitor_callback:
            result = await self.monitor_callback(event_id, context)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Default monitoring (placeholder)
        return {
            "event_id": event_id,
            "sources_found": context.get("sources_found", []),
            "sources_missing": context.get("sources_missing", ["azure"]),
            "metrics": {
                "event_age_hours": 2.5,
                "reconciliation_attempts": 0,
                "system_load": 0.65
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _analyze_phase(
        self,
        monitoring_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze phase: Determine root cause and impact.

        Args:
            monitoring_data: Data from monitor phase
            context: Context data

        Returns:
            Analysis result
        """
        self.current_phase = MAPEKPhase.ANALYZE

        if self.analyze_callback:
            result = await self.analyze_callback(monitoring_data, context)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Default analysis (placeholder)
        sources_missing = monitoring_data.get("sources_missing", [])
        impact = len(sources_missing) / 3.0  # Assume 3 total sources

        return {
            "event_id": monitoring_data["event_id"],
            "root_cause": f"Event missing from {len(sources_missing)} source(s)",
            "impact_severity": min(impact, 1.0),
            "recommended_actions": ["retry", "replay", "skip"],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def _plan_phase(
        self,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Plan phase: Select optimal recovery action.

        Args:
            analysis_result: Result from analyze phase
            context: Context data

        Returns:
            Recovery plan
        """
        self.current_phase = MAPEKPhase.PLAN

        if self.plan_callback:
            result = await self.plan_callback(analysis_result, context)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Default planning (placeholder - would use MCDM in real implementation)
        recommended = analysis_result.get("recommended_actions", [])
        selected = recommended[0] if recommended else "skip"

        return {
            "event_id": analysis_result["event_id"],
            "selected_action": selected,
            "action_score": 0.85,
            "alternative_actions": [
                {"action_id": action, "score": 0.7 - (i * 0.1)}
                for i, action in enumerate(recommended[1:])
            ],
            "plan_timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_phase(
        self,
        recovery_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute phase: Execute recovery action.

        Args:
            recovery_plan: Plan from plan phase
            context: Context data

        Returns:
            Execution result
        """
        self.current_phase = MAPEKPhase.EXECUTE

        if self.execute_callback:
            result = await self.execute_callback(recovery_plan, context)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Default execution (placeholder)
        import random
        success = random.random() > 0.1  # 90% success rate

        return {
            "event_id": recovery_plan["event_id"],
            "action_id": recovery_plan["selected_action"],
            "success": success,
            "execution_time": 2.5,
            "cost": 0.10,
            "error_message": None if success else "Simulated failure",
            "execution_timestamp": datetime.utcnow().isoformat()
        }

    async def _knowledge_phase(
        self,
        monitoring_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        recovery_plan: Dict[str, Any],
        execution_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Knowledge phase: Learn from outcome and update models.

        Args:
            monitoring_data: Monitor phase data
            analysis_result: Analyze phase data
            recovery_plan: Plan phase data
            execution_result: Execute phase data
            context: Context data

        Returns:
            Knowledge update result
        """
        self.current_phase = MAPEKPhase.KNOWLEDGE

        if self.knowledge_callback:
            result = await self.knowledge_callback(
                monitoring_data,
                analysis_result,
                recovery_plan,
                execution_result,
                context
            )
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Default knowledge update (placeholder)
        return {
            "event_id": execution_result["event_id"],
            "feedback_recorded": True,
            "model_updated": True,
            "success_rate_delta": 0.01 if execution_result["success"] else -0.01,
            "knowledge_timestamp": datetime.utcnow().isoformat()
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get MAPE-K loop statistics."""
        success_rate = (
            self.cycles_succeeded / self.cycles_completed
            if self.cycles_completed > 0
            else 0.0
        )

        return {
            "cycles_completed": self.cycles_completed,
            "cycles_succeeded": self.cycles_succeeded,
            "cycles_failed": self.cycles_failed,
            "success_rate": round(success_rate, 4),
            "current_phase": self.current_phase.value if self.current_phase else None
        }

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent execution history.

        Args:
            limit: Number of recent cycles to return

        Returns:
            Recent cycle results
        """
        return self.execution_history[-limit:]

    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history = []
        logger.info("mape_k_history_cleared")
