"""
Statistical Anomaly Detection

Uses EWMA (Exponentially Weighted Moving Average) and Z-score for anomaly detection.
Baseline fallback when LSTM model is unavailable.

Algorithm:
1. Track metric using EWMA: EWMA_t = α * value_t + (1-α) * EWMA_{t-1}
2. Calculate variance using EWMA: Var_t = α * (value_t - EWMA_t)^2 + (1-α) * Var_{t-1}
3. Compute Z-score: z = (value - EWMA) / sqrt(Var)
4. Flag as anomaly if |z| > threshold
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import structlog

logger = structlog.get_logger()


@dataclass
class AnomalyResult:
    """
    Anomaly detection result.

    Attributes:
        metric_name: Name of metric
        value: Current metric value
        expected_value: Expected value (EWMA)
        z_score: Z-score (number of std devs from mean)
        is_anomaly: Whether value is anomalous
        severity: Anomaly severity (0-1)
        timestamp: Detection timestamp
    """
    metric_name: str
    value: float
    expected_value: float
    z_score: float
    is_anomaly: bool
    severity: float
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "expected_value": round(self.expected_value, 4),
            "z_score": round(self.z_score, 4),
            "is_anomaly": self.is_anomaly,
            "severity": round(self.severity, 4),
            "timestamp": self.timestamp.isoformat()
        }


class EWMAAnomalyDetector:
    """
    EWMA-based anomaly detector.

    Uses exponentially weighted moving average to establish baseline
    and detect anomalies using Z-score thresholding.

    Features:
    - Adaptive baseline using EWMA
    - Variance tracking for Z-score calculation
    - Configurable sensitivity (threshold)
    - Multi-metric support
    - Historical anomaly tracking
    """

    def __init__(
        self,
        alpha: float = 0.3,
        threshold: float = 3.0,
        min_samples: int = 10
    ):
        """
        Initialize EWMA anomaly detector.

        Args:
            alpha: Smoothing factor (0-1). Higher = more weight to recent values
            threshold: Z-score threshold for anomaly detection (typically 2-3)
            min_samples: Minimum samples before detecting anomalies
        """
        if not 0 < alpha < 1:
            raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")

        if threshold <= 0:
            raise ValueError(f"Threshold must be positive, got {threshold}")

        self.alpha = alpha
        self.threshold = threshold
        self.min_samples = min_samples

        # EWMA state per metric
        self.ewma: Dict[str, float] = {}
        self.variance: Dict[str, float] = {}
        self.sample_count: Dict[str, int] = defaultdict(int)

        # Anomaly history
        self.anomaly_history: List[AnomalyResult] = []
        self.total_anomalies = 0

        logger.info(
            "ewma_detector_initialized",
            alpha=alpha,
            threshold=threshold,
            min_samples=min_samples
        )

    def update(
        self,
        metric_name: str,
        value: float
    ) -> AnomalyResult:
        """
        Update EWMA and detect anomaly.

        Args:
            metric_name: Metric identifier
            value: Current metric value

        Returns:
            Anomaly detection result
        """
        # Initialize if first sample
        if metric_name not in self.ewma:
            self.ewma[metric_name] = value
            self.variance[metric_name] = 0.0
            self.sample_count[metric_name] = 1

            return AnomalyResult(
                metric_name=metric_name,
                value=value,
                expected_value=value,
                z_score=0.0,
                is_anomaly=False,
                severity=0.0,
                timestamp=datetime.utcnow()
            )

        # Get current state
        prev_ewma = self.ewma[metric_name]
        prev_variance = self.variance[metric_name]

        # Update EWMA
        new_ewma = self.alpha * value + (1 - self.alpha) * prev_ewma

        # Update variance (EWMA of squared deviations)
        deviation = value - prev_ewma
        new_variance = self.alpha * (deviation ** 2) + (1 - self.alpha) * prev_variance

        # Store updated values
        self.ewma[metric_name] = new_ewma
        self.variance[metric_name] = new_variance
        self.sample_count[metric_name] += 1

        # Calculate Z-score
        std_dev = math.sqrt(new_variance) if new_variance > 0 else 1e-10
        z_score = (value - new_ewma) / std_dev

        # Detect anomaly
        is_anomaly = False
        severity = 0.0

        if self.sample_count[metric_name] >= self.min_samples:
            abs_z = abs(z_score)
            is_anomaly = abs_z > self.threshold

            # Calculate severity (0-1 scale)
            # severity = 0 at threshold, approaches 1 as z-score increases
            if is_anomaly:
                # Map z-score to 0-1 range (saturates at 2*threshold)
                severity = min((abs_z - self.threshold) / self.threshold, 1.0)

        # Create result
        result = AnomalyResult(
            metric_name=metric_name,
            value=value,
            expected_value=new_ewma,
            z_score=z_score,
            is_anomaly=is_anomaly,
            severity=severity,
            timestamp=datetime.utcnow()
        )

        # Track anomaly
        if is_anomaly:
            self.anomaly_history.append(result)
            self.total_anomalies += 1

            # Keep only recent anomalies
            if len(self.anomaly_history) > 1000:
                self.anomaly_history = self.anomaly_history[-1000:]

            logger.warning(
                "anomaly_detected",
                metric=metric_name,
                value=round(value, 4),
                expected=round(new_ewma, 4),
                z_score=round(z_score, 4),
                severity=round(severity, 4)
            )
        else:
            logger.debug(
                "metric_updated",
                metric=metric_name,
                value=round(value, 4),
                expected=round(new_ewma, 4),
                z_score=round(z_score, 4)
            )

        return result

    def batch_update(
        self,
        metrics: Dict[str, float]
    ) -> List[AnomalyResult]:
        """
        Update multiple metrics at once.

        Args:
            metrics: Dictionary mapping metric_name -> value

        Returns:
            List of anomaly results
        """
        results = []
        for metric_name, value in metrics.items():
            result = self.update(metric_name, value)
            results.append(result)
        return results

    def get_expected_value(self, metric_name: str) -> Optional[float]:
        """
        Get expected value (EWMA) for metric.

        Args:
            metric_name: Metric identifier

        Returns:
            Expected value or None if not initialized
        """
        return self.ewma.get(metric_name)

    def get_anomalies(
        self,
        metric_name: Optional[str] = None,
        limit: int = 100
    ) -> List[AnomalyResult]:
        """
        Get recent anomalies.

        Args:
            metric_name: Filter by metric (optional)
            limit: Maximum anomalies to return

        Returns:
            List of recent anomalies
        """
        if metric_name:
            filtered = [
                a for a in self.anomaly_history
                if a.metric_name == metric_name
            ]
            return filtered[-limit:]
        else:
            return self.anomaly_history[-limit:]

    def reset_metric(self, metric_name: str) -> None:
        """
        Reset EWMA state for specific metric.

        Args:
            metric_name: Metric to reset
        """
        if metric_name in self.ewma:
            del self.ewma[metric_name]
            del self.variance[metric_name]
            del self.sample_count[metric_name]
            logger.info("metric_reset", metric=metric_name)

    def reset_all(self) -> None:
        """Reset all metrics."""
        self.ewma.clear()
        self.variance.clear()
        self.sample_count.clear()
        self.anomaly_history.clear()
        self.total_anomalies = 0
        logger.info("detector_reset")

    def get_statistics(self) -> Dict:
        """Get detector statistics."""
        metrics_tracked = len(self.ewma)

        # Calculate anomaly rate
        total_samples = sum(self.sample_count.values())
        anomaly_rate = (
            self.total_anomalies / total_samples
            if total_samples > 0
            else 0.0
        )

        return {
            "algorithm": "EWMA",
            "alpha": self.alpha,
            "threshold": self.threshold,
            "min_samples": self.min_samples,
            "metrics_tracked": metrics_tracked,
            "total_samples": total_samples,
            "total_anomalies": self.total_anomalies,
            "anomaly_rate": round(anomaly_rate, 4),
            "recent_anomalies": len(self.anomaly_history)
        }

    def get_metric_summary(self, metric_name: str) -> Optional[Dict]:
        """
        Get summary for specific metric.

        Args:
            metric_name: Metric identifier

        Returns:
            Metric summary or None
        """
        if metric_name not in self.ewma:
            return None

        # Count anomalies for this metric
        metric_anomalies = sum(
            1 for a in self.anomaly_history
            if a.metric_name == metric_name
        )

        # Calculate anomaly rate for this metric
        samples = self.sample_count[metric_name]
        metric_anomaly_rate = metric_anomalies / samples if samples > 0 else 0.0

        return {
            "metric_name": metric_name,
            "ewma": round(self.ewma[metric_name], 4),
            "variance": round(self.variance[metric_name], 4),
            "std_dev": round(math.sqrt(self.variance[metric_name]), 4),
            "sample_count": samples,
            "anomaly_count": metric_anomalies,
            "anomaly_rate": round(metric_anomaly_rate, 4)
        }

    def export_state(self) -> Dict:
        """
        Export detector state for persistence.

        Returns:
            State dictionary
        """
        return {
            "config": {
                "alpha": self.alpha,
                "threshold": self.threshold,
                "min_samples": self.min_samples
            },
            "state": {
                "ewma": self.ewma.copy(),
                "variance": self.variance.copy(),
                "sample_count": dict(self.sample_count)
            },
            "statistics": self.get_statistics(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def import_state(self, state: Dict) -> None:
        """
        Import detector state from persistence.

        Args:
            state: State dictionary from export_state()
        """
        if "state" in state:
            self.ewma = state["state"].get("ewma", {})
            self.variance = state["state"].get("variance", {})
            self.sample_count = defaultdict(
                int,
                state["state"].get("sample_count", {})
            )
            logger.info(
                "state_imported",
                metrics_restored=len(self.ewma)
            )
