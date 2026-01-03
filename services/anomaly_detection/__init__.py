"""
Anomaly Detection Package

Statistical and ML-based anomaly detection for event reconciliation.
Dual-mode: LSTM (production) + EWMA (fallback).
"""

from .statistical import EWMAAnomalyDetector, AnomalyResult
from .ml_detector import LSTMAnomalyDetector, get_ml_detector

__all__ = [
    "EWMAAnomalyDetector",
    "AnomalyResult",
    "LSTMAnomalyDetector",
    "get_ml_detector"
]
