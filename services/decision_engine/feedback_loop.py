"""
Recovery Feedback Loop

Implements continuous learning from recovery action outcomes.
Updates success rates and action preferences based on historical performance.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

logger = structlog.get_logger()


@dataclass
class RecoveryOutcome:
    """
    Recovery action execution outcome.

    Attributes:
        action_id: Recovery action identifier
        event_id: Event that was recovered
        success: Whether recovery succeeded
        execution_time: Time taken (seconds)
        cost: Monetary cost incurred
        timestamp: When recovery was executed
        error_message: Error message if failed
        metadata: Optional metadata
    """
    action_id: str
    event_id: str
    success: bool
    execution_time: float
    cost: float
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class ActionStatistics:
    """
    Statistical data for recovery action.

    Attributes:
        action_id: Action identifier
        total_executions: Total times executed
        successes: Number of successes
        failures: Number of failures
        total_execution_time: Cumulative execution time
        total_cost: Cumulative cost
        avg_execution_time: Average execution time
        avg_cost: Average cost per execution
        success_rate: Success rate (0-1)
        last_updated: Last update timestamp
    """
    action_id: str
    total_executions: int = 0
    successes: int = 0
    failures: int = 0
    total_execution_time: float = 0.0
    total_cost: float = 0.0
    avg_execution_time: float = 0.0
    avg_cost: float = 0.0
    success_rate: float = 0.0
    last_updated: Optional[datetime] = None

    def update(self, outcome: RecoveryOutcome) -> None:
        """Update statistics with new outcome."""
        self.total_executions += 1

        if outcome.success:
            self.successes += 1
        else:
            self.failures += 1

        self.total_execution_time += outcome.execution_time
        self.total_cost += outcome.cost

        # Recalculate averages
        self.avg_execution_time = self.total_execution_time / self.total_executions
        self.avg_cost = self.total_cost / self.total_executions
        self.success_rate = self.successes / self.total_executions

        self.last_updated = datetime.utcnow()


class RecoveryFeedbackLoop:
    """
    Recovery feedback loop for continuous learning.

    Features:
    - Track recovery action outcomes
    - Calculate real-time success rates
    - Identify best-performing actions
    - Detect degrading actions
    - Provide recommendations
    """

    def __init__(
        self,
        window_size: int = 100,
        decay_factor: float = 0.95
    ):
        """
        Initialize feedback loop.

        Args:
            window_size: Number of recent outcomes to consider
            decay_factor: Exponential decay for weighted averages (0-1)
        """
        self.window_size = window_size
        self.decay_factor = decay_factor

        # Action statistics
        self.action_stats: Dict[str, ActionStatistics] = {}

        # Recent outcomes (circular buffer)
        self.recent_outcomes: List[RecoveryOutcome] = []

        # Failure patterns
        self.failure_patterns: Dict[str, List[str]] = defaultdict(list)

        logger.info(
            "feedback_loop_initialized",
            window_size=window_size,
            decay_factor=decay_factor
        )

    def record_outcome(self, outcome: RecoveryOutcome) -> None:
        """
        Record recovery action outcome.

        Args:
            outcome: Recovery outcome to record
        """
        # Initialize stats if needed
        if outcome.action_id not in self.action_stats:
            self.action_stats[outcome.action_id] = ActionStatistics(
                action_id=outcome.action_id
            )

        # Update statistics
        self.action_stats[outcome.action_id].update(outcome)

        # Add to recent outcomes (circular buffer)
        self.recent_outcomes.append(outcome)
        if len(self.recent_outcomes) > self.window_size:
            self.recent_outcomes.pop(0)

        # Track failure patterns
        if not outcome.success and outcome.error_message:
            self.failure_patterns[outcome.action_id].append(outcome.error_message)

            # Keep only recent failures
            if len(self.failure_patterns[outcome.action_id]) > 50:
                self.failure_patterns[outcome.action_id].pop(0)

        logger.info(
            "recovery_outcome_recorded",
            action_id=outcome.action_id,
            event_id=outcome.event_id,
            success=outcome.success,
            execution_time=round(outcome.execution_time, 3),
            cost=round(outcome.cost, 2)
        )

    def get_action_stats(self, action_id: str) -> Optional[ActionStatistics]:
        """
        Get statistics for specific action.

        Args:
            action_id: Action identifier

        Returns:
            Action statistics or None
        """
        return self.action_stats.get(action_id)

    def get_all_stats(self) -> Dict[str, ActionStatistics]:
        """Get statistics for all actions."""
        return self.action_stats.copy()

    def get_best_action(
        self,
        min_executions: int = 5
    ) -> Optional[str]:
        """
        Get best performing action based on success rate.

        Args:
            min_executions: Minimum executions required

        Returns:
            Action ID of best performer or None
        """
        eligible_actions = [
            (action_id, stats)
            for action_id, stats in self.action_stats.items()
            if stats.total_executions >= min_executions
        ]

        if not eligible_actions:
            return None

        # Sort by success rate (descending)
        best_action_id, best_stats = max(
            eligible_actions,
            key=lambda x: x[1].success_rate
        )

        return best_action_id

    def get_weighted_success_rate(
        self,
        action_id: str,
        recent_only: bool = True
    ) -> float:
        """
        Calculate exponentially weighted success rate.

        More recent outcomes have higher weight.

        Args:
            action_id: Action identifier
            recent_only: Use only recent outcomes from window

        Returns:
            Weighted success rate (0-1)
        """
        # Get relevant outcomes
        if recent_only:
            outcomes = [
                o for o in self.recent_outcomes
                if o.action_id == action_id
            ]
        else:
            outcomes = [
                o for o in self.recent_outcomes
                if o.action_id == action_id
            ]

        if not outcomes:
            return 0.0

        # Calculate exponentially weighted average
        weighted_sum = 0.0
        weight_sum = 0.0

        for i, outcome in enumerate(reversed(outcomes)):
            weight = self.decay_factor ** i
            weighted_sum += weight * (1.0 if outcome.success else 0.0)
            weight_sum += weight

        if weight_sum == 0:
            return 0.0

        return weighted_sum / weight_sum

    def detect_degradation(
        self,
        action_id: str,
        threshold: float = 0.2
    ) -> bool:
        """
        Detect if action performance is degrading.

        Compares recent success rate to historical average.

        Args:
            action_id: Action identifier
            threshold: Degradation threshold (0-1)

        Returns:
            True if degrading
        """
        stats = self.action_stats.get(action_id)
        if not stats or stats.total_executions < 10:
            return False

        # Get recent weighted success rate
        recent_rate = self.get_weighted_success_rate(action_id, recent_only=True)

        # Compare to historical average
        historical_rate = stats.success_rate

        # Degrading if recent rate significantly lower
        degradation = historical_rate - recent_rate

        is_degrading = degradation > threshold

        if is_degrading:
            logger.warning(
                "action_degradation_detected",
                action_id=action_id,
                historical_rate=round(historical_rate, 3),
                recent_rate=round(recent_rate, 3),
                degradation=round(degradation, 3)
            )

        return is_degrading

    def get_recommendations(self) -> List[Dict[str, any]]:
        """
        Get recommendations based on feedback data.

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Check for degrading actions
        for action_id in self.action_stats.keys():
            if self.detect_degradation(action_id):
                recommendations.append({
                    "type": "degradation",
                    "action_id": action_id,
                    "severity": "warning",
                    "message": f"Action '{action_id}' showing performance degradation"
                })

        # Identify underperforming actions
        for action_id, stats in self.action_stats.items():
            if stats.total_executions >= 10 and stats.success_rate < 0.5:
                recommendations.append({
                    "type": "low_success_rate",
                    "action_id": action_id,
                    "severity": "warning",
                    "message": f"Action '{action_id}' has low success rate: {stats.success_rate:.2%}",
                    "success_rate": stats.success_rate
                })

        # Identify best performer
        best_action = self.get_best_action(min_executions=5)
        if best_action:
            best_stats = self.action_stats[best_action]
            recommendations.append({
                "type": "best_performer",
                "action_id": best_action,
                "severity": "info",
                "message": f"Action '{best_action}' is top performer: {best_stats.success_rate:.2%}",
                "success_rate": best_stats.success_rate
            })

        return recommendations

    def get_failure_analysis(self, action_id: str) -> Dict[str, any]:
        """
        Analyze failure patterns for action.

        Args:
            action_id: Action identifier

        Returns:
            Failure analysis dictionary
        """
        stats = self.action_stats.get(action_id)
        if not stats:
            return {"error": "Action not found"}

        failures = self.failure_patterns.get(action_id, [])

        # Count error types
        error_counts = defaultdict(int)
        for error_msg in failures:
            # Extract error type (first word or first 50 chars)
            error_type = error_msg.split(":")[0][:50] if error_msg else "Unknown"
            error_counts[error_type] += 1

        # Sort by frequency
        common_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "action_id": action_id,
            "total_failures": stats.failures,
            "failure_rate": 1.0 - stats.success_rate,
            "common_errors": [
                {"error_type": error, "count": count}
                for error, count in common_errors[:5]
            ],
            "recent_failures": len(failures)
        }

    def export_statistics(self) -> Dict[str, any]:
        """
        Export all statistics for persistence/analysis.

        Returns:
            Statistics dictionary
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "window_size": self.window_size,
            "decay_factor": self.decay_factor,
            "total_outcomes": len(self.recent_outcomes),
            "actions": {
                action_id: {
                    "total_executions": stats.total_executions,
                    "successes": stats.successes,
                    "failures": stats.failures,
                    "success_rate": round(stats.success_rate, 4),
                    "avg_execution_time": round(stats.avg_execution_time, 3),
                    "avg_cost": round(stats.avg_cost, 2),
                    "last_updated": stats.last_updated.isoformat() if stats.last_updated else None
                }
                for action_id, stats in self.action_stats.items()
            },
            "recommendations": self.get_recommendations()
        }

    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics."""
        total_executions = sum(s.total_executions for s in self.action_stats.values())
        total_successes = sum(s.successes for s in self.action_stats.values())
        total_failures = sum(s.failures for s in self.action_stats.values())

        overall_success_rate = (
            total_successes / total_executions if total_executions > 0 else 0.0
        )

        return {
            "total_actions": len(self.action_stats),
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": round(overall_success_rate, 4),
            "recent_outcomes": len(self.recent_outcomes),
            "best_action": self.get_best_action(min_executions=5)
        }
