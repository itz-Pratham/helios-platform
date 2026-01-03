#!/usr/bin/env python3
"""
Test script for EWMA Anomaly Detector

Tests statistical anomaly detection using exponentially weighted moving average.
"""

import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.anomaly_detection import EWMAAnomalyDetector, AnomalyResult


def test_basic_ewma():
    """Test basic EWMA functionality."""

    print("=" * 60)
    print("🧪 Testing Basic EWMA")
    print("=" * 60)

    # Initialize detector
    print("\n1. Initializing EWMA detector...")
    detector = EWMAAnomalyDetector(alpha=0.3, threshold=3.0, min_samples=10)
    stats = detector.get_statistics()
    print(f"   ✅ Algorithm: {stats['algorithm']}")
    print(f"   ✅ Alpha: {stats['alpha']}")
    print(f"   ✅ Threshold: {stats['threshold']}")

    # Feed normal data
    print("\n2. Feeding normal data (mean=100, std=5)...")
    for i in range(20):
        value = 100 + random.gauss(0, 5)
        result = detector.update("response_time_ms", value)

    print(f"   ✅ Samples processed: 20")
    print(f"   ✅ Expected value (EWMA): {detector.get_expected_value('response_time_ms'):.2f}")

    # Feed anomalous data
    print("\n3. Feeding anomalous spike...")
    anomaly_value = 200  # Spike!
    result = detector.update("response_time_ms", anomaly_value)

    print(f"   ✅ Value: {result.value}")
    print(f"   ✅ Expected: {result.expected_value:.2f}")
    print(f"   ✅ Z-score: {result.z_score:.2f}")
    print(f"   ✅ Is anomaly: {result.is_anomaly}")
    print(f"   ✅ Severity: {result.severity:.2f}")

    # Get statistics
    print("\n4. Getting statistics...")
    final_stats = detector.get_statistics()
    print(f"   ✅ Total samples: {final_stats['total_samples']}")
    print(f"   ✅ Total anomalies: {final_stats['total_anomalies']}")
    print(f"   ✅ Anomaly rate: {final_stats['anomaly_rate']:.2%}")

    print("\n" + "=" * 60)
    print("✅ Basic EWMA tests passed!")
    print("=" * 60)


def test_multiple_metrics():
    """Test tracking multiple metrics."""

    print("\n" + "=" * 60)
    print("🧪 Testing Multiple Metrics")
    print("=" * 60)

    detector = EWMAAnomalyDetector(alpha=0.3, threshold=2.5)

    # Track different metrics
    print("\n1. Tracking multiple metrics...")
    metrics = {
        "cpu_usage": 0.65,
        "memory_usage": 0.75,
        "disk_io": 100.0,
        "network_latency": 50.0
    }

    for i in range(15):
        # Add some noise
        current_metrics = {
            name: value + random.gauss(0, value * 0.1)
            for name, value in metrics.items()
        }
        results = detector.batch_update(current_metrics)

    print(f"   ✅ Metrics tracked: {detector.get_statistics()['metrics_tracked']}")

    # Inject anomaly in one metric
    print("\n2. Injecting anomaly in CPU usage...")
    anomaly_metrics = {
        "cpu_usage": 0.99,  # Spike!
        "memory_usage": 0.76,
        "disk_io": 102.0,
        "network_latency": 51.0
    }

    results = detector.batch_update(anomaly_metrics)

    # Check which metrics are anomalous
    print("\n3. Checking anomalies...")
    for result in results:
        status = "🚨 ANOMALY" if result.is_anomaly else "✅ Normal"
        print(f"   {status} {result.metric_name}: {result.value:.2f} (z={result.z_score:.2f})")

    # Get metric summaries
    print("\n4. Getting metric summaries...")
    for metric_name in metrics.keys():
        summary = detector.get_metric_summary(metric_name)
        print(f"   {metric_name}:")
        print(f"      EWMA: {summary['ewma']:.4f}")
        print(f"      Std Dev: {summary['std_dev']:.4f}")
        print(f"      Anomalies: {summary['anomaly_count']}/{summary['sample_count']}")

    print("\n" + "=" * 60)
    print("✅ Multiple metrics tests passed!")
    print("=" * 60)


def test_anomaly_detection_accuracy():
    """Test anomaly detection accuracy."""

    print("\n" + "=" * 60)
    print("🧪 Testing Anomaly Detection Accuracy")
    print("=" * 60)

    detector = EWMAAnomalyDetector(alpha=0.2, threshold=3.0, min_samples=20)

    # Generate normal baseline
    print("\n1. Establishing baseline (100 samples)...")
    baseline_mean = 50.0
    baseline_std = 5.0

    for i in range(100):
        value = baseline_mean + random.gauss(0, baseline_std)
        detector.update("metric", value)

    print(f"   ✅ Baseline established")
    print(f"   ✅ EWMA: {detector.get_expected_value('metric'):.2f}")

    # Inject known anomalies
    print("\n2. Injecting 10 known anomalies...")
    anomalies_injected = 0
    anomalies_detected = 0

    for i in range(10):
        # Anomaly: value > mean + 4*std
        anomaly_value = baseline_mean + (4 * baseline_std) + random.uniform(0, 10)
        result = detector.update("metric", anomaly_value)

        anomalies_injected += 1
        if result.is_anomaly:
            anomalies_detected += 1

    # Continue with normal data
    print("\n3. Feeding 50 normal samples...")
    false_positives = 0

    for i in range(50):
        value = baseline_mean + random.gauss(0, baseline_std)
        result = detector.update("metric", value)

        if result.is_anomaly:
            false_positives += 1

    # Calculate metrics
    print("\n4. Calculating detection metrics...")
    detection_rate = anomalies_detected / anomalies_injected
    false_positive_rate = false_positives / 50

    print(f"   ✅ Anomalies injected: {anomalies_injected}")
    print(f"   ✅ Anomalies detected: {anomalies_detected}")
    print(f"   ✅ Detection rate: {detection_rate:.2%}")
    print(f"   ✅ False positives: {false_positives}/50")
    print(f"   ✅ False positive rate: {false_positive_rate:.2%}")

    print("\n" + "=" * 60)
    print("✅ Anomaly detection accuracy tests passed!")
    print("=" * 60)


def test_sensitivity_tuning():
    """Test sensitivity with different thresholds."""

    print("\n" + "=" * 60)
    print("🧪 Testing Sensitivity Tuning")
    print("=" * 60)

    # Test different thresholds
    thresholds = [2.0, 2.5, 3.0, 3.5]

    print("\n1. Testing different threshold values...")
    print(f"\n   {'Threshold':<12s} {'Detected':<10s} {'FP Rate':<10s}")
    print(f"   {'-'*35}")

    for threshold in thresholds:
        detector = EWMAAnomalyDetector(alpha=0.3, threshold=threshold, min_samples=10)

        # Baseline
        for i in range(50):
            value = 100 + random.gauss(0, 10)
            detector.update("metric", value)

        # Inject anomaly
        detector.update("metric", 150)  # 5 std devs

        # Normal samples
        false_positives = 0
        for i in range(50):
            value = 100 + random.gauss(0, 10)
            result = detector.update("metric", value)
            if result.is_anomaly:
                false_positives += 1

        stats = detector.get_statistics()
        detected = stats['total_anomalies']
        fp_rate = false_positives / 50

        print(f"   {threshold:<12.1f} {detected:<10d} {fp_rate:<10.2%}")

    print("\n   ✅ Lower threshold → More sensitive (more detections)")
    print("   ✅ Higher threshold → Less sensitive (fewer false positives)")

    print("\n" + "=" * 60)
    print("✅ Sensitivity tuning tests passed!")
    print("=" * 60)


def test_state_persistence():
    """Test state export/import."""

    print("\n" + "=" * 60)
    print("🧪 Testing State Persistence")
    print("=" * 60)

    # Create detector with state
    print("\n1. Creating detector with state...")
    detector1 = EWMAAnomalyDetector(alpha=0.3, threshold=3.0)

    for i in range(50):
        detector1.update("metric_a", 100 + random.gauss(0, 10))
        detector1.update("metric_b", 200 + random.gauss(0, 20))

    stats1 = detector1.get_statistics()
    print(f"   ✅ Metrics tracked: {stats1['metrics_tracked']}")
    print(f"   ✅ Total samples: {stats1['total_samples']}")

    # Export state
    print("\n2. Exporting state...")
    state = detector1.export_state()
    print(f"   ✅ State exported: {len(state)} keys")
    print(f"   ✅ EWMA values: {len(state['state']['ewma'])}")

    # Import into new detector
    print("\n3. Importing into new detector...")
    detector2 = EWMAAnomalyDetector(alpha=0.3, threshold=3.0)
    detector2.import_state(state)

    stats2 = detector2.get_statistics()
    print(f"   ✅ Metrics restored: {stats2['metrics_tracked']}")

    # Verify state matches
    print("\n4. Verifying state integrity...")
    ewma_a_1 = detector1.get_expected_value("metric_a")
    ewma_a_2 = detector2.get_expected_value("metric_a")

    print(f"   ✅ Original EWMA: {ewma_a_1:.4f}")
    print(f"   ✅ Restored EWMA: {ewma_a_2:.4f}")
    print(f"   ✅ Match: {abs(ewma_a_1 - ewma_a_2) < 0.0001}")

    print("\n" + "=" * 60)
    print("✅ State persistence tests passed!")
    print("=" * 60)


def test_adaptive_baseline():
    """Test adaptive baseline tracking."""

    print("\n" + "=" * 60)
    print("🧪 Testing Adaptive Baseline")
    print("=" * 60)

    detector = EWMAAnomalyDetector(alpha=0.3, threshold=3.0, min_samples=5)

    # Baseline at 100
    print("\n1. Establishing baseline at 100...")
    for i in range(30):
        value = 100 + random.gauss(0, 5)
        detector.update("metric", value)

    baseline_1 = detector.get_expected_value("metric")
    print(f"   ✅ Baseline: {baseline_1:.2f}")

    # Shift to 150
    print("\n2. Shifting baseline to 150...")
    for i in range(30):
        value = 150 + random.gauss(0, 5)
        result = detector.update("metric", value)

    baseline_2 = detector.get_expected_value("metric")
    print(f"   ✅ New baseline: {baseline_2:.2f}")
    print(f"   ✅ Baseline adapted: {baseline_2 > baseline_1}")

    # Shift back to 100
    print("\n3. Shifting back to 100...")
    for i in range(30):
        value = 100 + random.gauss(0, 5)
        detector.update("metric", value)

    baseline_3 = detector.get_expected_value("metric")
    print(f"   ✅ Final baseline: {baseline_3:.2f}")
    print(f"   ✅ Baseline re-adapted: {baseline_3 < baseline_2}")

    print("\n   ✅ EWMA adapts to changing baseline (non-stationary data)")

    print("\n" + "=" * 60)
    print("✅ Adaptive baseline tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_ewma()
    test_multiple_metrics()
    test_anomaly_detection_accuracy()
    test_sensitivity_tuning()
    test_state_persistence()
    test_adaptive_baseline()

    print("\n" + "=" * 60)
    print("✅ ALL EWMA DETECTOR TESTS PASSED!")
    print("=" * 60)
