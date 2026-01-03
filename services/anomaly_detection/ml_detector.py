#!/usr/bin/env python3
"""
LSTM-based Anomaly Detection (Production)

Uses trained Keras LSTM model for real-time anomaly detection.
Falls back to statistical EWMA detector if model unavailable.
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class MLAnomalyResult:
    """Result from ML anomaly detection."""
    metric_name: str
    is_anomaly: bool
    confidence: float  # 0-1 (anomaly probability)
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    model_type: str  # "lstm" or "ewma_fallback"
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None


class LSTMAnomalyDetector:
    """
    LSTM-based anomaly detector for production use.

    Features:
    - Real-time inference (<100ms)
    - Rolling 60-minute window
    - Auto-fallback to statistical detector
    - Confidence scoring
    - Severity classification
    """

    def __init__(
        self,
        model_path: str = "ml_models/anomaly_detector.keras",  # Prefer .keras (modern format)
        scaler_path: str = "ml_models/scaler.pkl",
        config_path: str = "ml_models/model_config.json",
        threshold: float = 0.5,
        window_size: int = 60
    ):
        """
        Initialize LSTM anomaly detector.

        Args:
            model_path: Path to Keras model file
            scaler_path: Path to feature scaler pickle
            config_path: Path to model config JSON
            threshold: Anomaly probability threshold (0-1)
            window_size: Rolling window size (minutes)
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.config_path = Path(config_path)
        self.threshold = threshold
        self.window_size = window_size

        # Model components
        self.model = None
        self.scaler = None
        self.config = None
        self.feature_names = None

        # Rolling window buffer
        self.metric_history = deque(maxlen=window_size)

        # Fallback detector
        self.fallback_detector = None

        # Load model
        self._load_model()

    def _load_model(self) -> None:
        """Load Keras model and scaler."""
        try:
            # Check files exist
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model not found: {self.model_path}")
            if not self.scaler_path.exists():
                raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config not found: {self.config_path}")

            # Load config
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            self.feature_names = self.config['feature_names']
            logger.info(f"Loaded config: {len(self.feature_names)} features")

            # Load scaler
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Loaded scaler: mean={self.scaler.mean_[:3]}")

            # Load Keras model (with compatibility for different TF versions)
            import tensorflow as tf

            # Custom objects for backwards compatibility
            custom_objects = {}

            try:
                self.model = tf.keras.models.load_model(
                    self.model_path,
                    custom_objects=custom_objects,
                    compile=False  # Don't need training config
                )
                logger.info(f"Loaded LSTM model: {self.model.count_params()} params")
            except Exception as e:
                # Try loading without compile (more permissive)
                logger.warning(f"First load attempt failed: {e}")
                logger.info("Trying alternative loading method...")

                # Load model architecture only and rebuild
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                # Rebuild model from scratch
                from tensorflow.keras import Sequential
                from tensorflow.keras.layers import LSTM, Dense, Dropout

                self.model = Sequential([
                    LSTM(config['model_architecture']['lstm_1'],
                         return_sequences=True,
                         input_shape=(60, 8),
                         recurrent_dropout=0.1),
                    Dropout(0.3),
                    LSTM(config['model_architecture']['lstm_2'],
                         recurrent_dropout=0.1),
                    Dropout(0.3),
                    Dense(config['model_architecture']['dense'], activation='relu'),
                    Dropout(0.2),
                    Dense(1, activation='sigmoid')
                ])

                # Load weights from saved model
                self.model.load_weights(self.model_path)
                logger.info(f"Loaded LSTM weights: {self.model.count_params()} params")

            # Warm up model (first inference is slow)
            dummy_input = np.random.randn(1, self.window_size, len(self.feature_names)).astype(np.float32)
            _ = self.model.predict(dummy_input, verbose=0)
            logger.info("Model warmed up")

        except Exception as e:
            logger.warning(f"Failed to load LSTM model: {e}")
            logger.warning("Will use EWMA fallback detector")
            self._init_fallback()

    def _init_fallback(self) -> None:
        """Initialize EWMA fallback detector."""
        from .statistical import EWMAAnomalyDetector

        self.fallback_detector = EWMAAnomalyDetector(
            alpha=0.3,
            threshold=3.0,
            min_samples=10
        )
        logger.info("EWMA fallback detector initialized")

    def update(self, metrics: Dict[str, float]) -> MLAnomalyResult:
        """
        Update detector with new metrics and check for anomalies.

        Args:
            metrics: Dictionary with metric names and values
                    Must contain all required features:
                    - missing_event_rate
                    - duplicate_rate
                    - inconsistent_rate
                    - aws_gcp_latency_ms
                    - aws_azure_latency_ms
                    - gcp_azure_latency_ms
                    - event_rate_per_minute
                    - payload_size_variance

        Returns:
            MLAnomalyResult with detection results
        """
        timestamp = datetime.utcnow()

        # Use fallback if model not loaded
        if self.model is None:
            return self._fallback_detect(metrics, timestamp)

        try:
            # Extract features in correct order
            features = [metrics[name] for name in self.feature_names]

            # Add to rolling window
            self.metric_history.append(features)

            # Need full window for prediction
            if len(self.metric_history) < self.window_size:
                return MLAnomalyResult(
                    metric_name="system",
                    is_anomaly=False,
                    confidence=0.0,
                    severity="low",
                    timestamp=timestamp,
                    model_type="lstm",
                    expected_value=None,
                    actual_value=None
                )

            # Prepare input (normalize + reshape)
            window_data = np.array(list(self.metric_history))
            normalized = self.scaler.transform(window_data.reshape(-1, len(self.feature_names)))
            input_tensor = normalized.reshape(1, self.window_size, len(self.feature_names)).astype(np.float32)

            # Predict
            anomaly_prob = float(self.model.predict(input_tensor, verbose=0)[0][0])

            # Classify
            is_anomaly = anomaly_prob > self.threshold
            severity = self._classify_severity(anomaly_prob)

            return MLAnomalyResult(
                metric_name="system",
                is_anomaly=is_anomaly,
                confidence=anomaly_prob,
                severity=severity,
                timestamp=timestamp,
                model_type="lstm",
                expected_value=None,  # LSTM doesn't predict specific values
                actual_value=anomaly_prob
            )

        except Exception as e:
            logger.error(f"LSTM inference failed: {e}")
            return self._fallback_detect(metrics, timestamp)

    def _fallback_detect(self, metrics: Dict[str, float], timestamp: datetime) -> MLAnomalyResult:
        """Use EWMA fallback detector."""
        if self.fallback_detector is None:
            self._init_fallback()

        # Use missing_event_rate as primary metric for fallback
        result = self.fallback_detector.update("missing_event_rate", metrics.get("missing_event_rate", 0.0))

        return MLAnomalyResult(
            metric_name=result.metric_name,
            is_anomaly=result.is_anomaly,
            confidence=result.severity,  # Use severity as confidence
            severity="medium" if result.is_anomaly else "low",
            timestamp=timestamp,
            model_type="ewma_fallback",
            expected_value=result.expected_value,
            actual_value=result.value
        )

    def _classify_severity(self, confidence: float) -> str:
        """
        Classify anomaly severity based on confidence.

        Args:
            confidence: Anomaly probability (0-1)

        Returns:
            Severity level: "low", "medium", "high", "critical"
        """
        if confidence < self.threshold:
            return "low"
        elif confidence < 0.7:
            return "medium"
        elif confidence < 0.9:
            return "high"
        else:
            return "critical"

    def get_stats(self) -> Dict:
        """Get detector statistics."""
        return {
            "model_loaded": self.model is not None,
            "model_type": "lstm" if self.model is not None else "ewma_fallback",
            "window_size": self.window_size,
            "current_window_length": len(self.metric_history),
            "threshold": self.threshold,
            "feature_count": len(self.feature_names) if self.feature_names else 0,
            "model_params": self.model.count_params() if self.model else 0
        }

    def reset(self) -> None:
        """Reset detector state (clear history)."""
        self.metric_history.clear()
        logger.info("Detector reset")


# Singleton instance
_detector_instance: Optional[LSTMAnomalyDetector] = None


def get_ml_detector() -> LSTMAnomalyDetector:
    """Get singleton ML detector instance."""
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = LSTMAnomalyDetector()

    return _detector_instance
