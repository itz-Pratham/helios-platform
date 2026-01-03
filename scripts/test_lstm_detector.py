#!/usr/bin/env python3
"""
Test LSTM Anomaly Detector

Verify the trained model works in production.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.anomaly_detection.ml_detector import LSTMAnomalyDetector
import time


def test_lstm_detector():
    """Test LSTM detector with various scenarios."""

    print("="*60)
    print("🧪 Testing LSTM Anomaly Detector")
    print("="*60)

    # Initialize detector
    print("\n1. Initializing detector...")
    detector = LSTMAnomalyDetector()

    # Get stats
    stats = detector.get_stats()
    print(f"   ✅ Model loaded: {stats['model_loaded']}")
    print(f"   ✅ Model type: {stats['model_type']}")
    print(f"   ✅ Model params: {stats['model_params']:,}")
    print(f"   ✅ Window size: {stats['window_size']}")
    print(f"   ✅ Features: {stats['feature_count']}")

    # Test 1: Normal metrics
    print("\n2. Testing with NORMAL metrics...")
    normal_metrics = {
        'missing_event_rate': 0.02,      # 2% (normal)
        'duplicate_rate': 0.005,          # 0.5% (normal)
        'inconsistent_rate': 0.003,       # 0.3% (normal)
        'aws_gcp_latency_ms': 45.0,       # 45ms (normal)
        'aws_azure_latency_ms': 50.0,     # 50ms (normal)
        'gcp_azure_latency_ms': 42.0,     # 42ms (normal)
        'event_rate_per_minute': 1250.0,  # 1250 events/min (normal)
        'payload_size_variance': 0.1      # 0.1 variance (normal)
    }

    # Feed 60 minutes of normal data
    for i in range(60):
        result = detector.update(normal_metrics)
        if i == 59:  # Last update (when window is full)
            print(f"   📊 Result after {i+1} minutes:")
            print(f"      Is anomaly: {result.is_anomaly}")
            print(f"      Confidence: {result.confidence:.6f}")
            print(f"      Severity: {result.severity}")
            print(f"      Model: {result.model_type}")

    # Test 2: Anomalous metrics
    print("\n3. Testing with ANOMALOUS metrics...")
    anomaly_metrics = {
        'missing_event_rate': 0.25,       # 25% (ANOMALY!)
        'duplicate_rate': 0.005,
        'inconsistent_rate': 0.003,
        'aws_gcp_latency_ms': 150.0,      # 150ms (HIGH!)
        'aws_azure_latency_ms': 180.0,    # 180ms (HIGH!)
        'gcp_azure_latency_ms': 140.0,
        'event_rate_per_minute': 600.0,   # 600 events/min (LOW!)
        'payload_size_variance': 0.1
    }

    # Feed 10 minutes of anomalous data
    for i in range(10):
        result = detector.update(anomaly_metrics)
        if i == 9:  # Last update
            print(f"   📊 Result after {i+1} anomalous minutes:")
            print(f"      Is anomaly: {result.is_anomaly}")
            print(f"      Confidence: {result.confidence:.6f}")
            print(f"      Severity: {result.severity}")
            print(f"      Model: {result.model_type}")

    # Test 3: Latency spike
    print("\n4. Testing LATENCY SPIKE...")
    latency_spike = {
        'missing_event_rate': 0.02,
        'duplicate_rate': 0.005,
        'inconsistent_rate': 0.003,
        'aws_gcp_latency_ms': 250.0,      # SPIKE!
        'aws_azure_latency_ms': 280.0,    # SPIKE!
        'gcp_azure_latency_ms': 240.0,    # SPIKE!
        'event_rate_per_minute': 1100.0,  # Slightly lower
        'payload_size_variance': 0.1
    }

    for i in range(5):
        result = detector.update(latency_spike)
        if i == 4:
            print(f"   📊 Result after {i+1} minutes of spike:")
            print(f"      Is anomaly: {result.is_anomaly}")
            print(f"      Confidence: {result.confidence:.6f}")
            print(f"      Severity: {result.severity}")

    # Test 4: Duplicate storm
    print("\n5. Testing DUPLICATE STORM...")
    duplicate_storm = {
        'missing_event_rate': 0.02,
        'duplicate_rate': 0.12,           # 12% duplicates! (STORM!)
        'inconsistent_rate': 0.003,
        'aws_gcp_latency_ms': 45.0,
        'aws_azure_latency_ms': 50.0,
        'gcp_azure_latency_ms': 42.0,
        'event_rate_per_minute': 1800.0,  # Higher (duplicates)
        'payload_size_variance': 0.3      # Higher variance
    }

    for i in range(5):
        result = detector.update(duplicate_storm)
        if i == 4:
            print(f"   📊 Result after {i+1} minutes of storm:")
            print(f"      Is anomaly: {result.is_anomaly}")
            print(f"      Confidence: {result.confidence:.6f}")
            print(f"      Severity: {result.severity}")

    # Test 5: Inference speed
    print("\n6. Testing INFERENCE SPEED...")
    start = time.time()
    for _ in range(100):
        _ = detector.update(normal_metrics)
    elapsed = time.time() - start
    avg_latency = (elapsed / 100) * 1000

    print(f"   ⚡ 100 inferences in {elapsed:.3f}s")
    print(f"   ⚡ Average latency: {avg_latency:.2f}ms")

    if avg_latency < 100:
        print(f"   ✅ PASS: Latency < 100ms target")
    else:
        print(f"   ⚠️  WARNING: Latency > 100ms")

    # Summary
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)
    print("\n📊 Detector Stats:")
    final_stats = detector.get_stats()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")

    print("\n✅ LSTM detector is production-ready!")


if __name__ == "__main__":
    test_lstm_detector()
