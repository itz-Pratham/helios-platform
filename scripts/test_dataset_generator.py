#!/usr/bin/env python3
"""
Quick test: Verify dataset generation works

Run this locally to test dataset generation before Kaggle.
Generates small dataset (100 hours instead of 10,000).
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dataset generator
from ml.generate_synthetic_dataset import generate_dataset, preview_dataset


def test_quick_generation():
    """Test dataset generation with small dataset."""

    print("="*60)
    print("🧪 Testing Dataset Generation")
    print("="*60)

    print("\n1. Generating small dataset (100 hours)...")

    # Generate small dataset for testing
    df = generate_dataset(
        num_hours=100,  # Small for quick test
        anomaly_probability=0.05,  # 5% (more anomalies for testing)
        output_file="test_reconciliation_metrics.csv"
    )

    print("\n2. Verifying dataset structure...")

    # Check shape
    expected_samples = 100 * 60  # 100 hours * 60 minutes
    assert len(df) == expected_samples, f"Expected {expected_samples} samples, got {len(df)}"
    print(f"   ✅ Correct number of samples: {len(df)}")

    # Check columns
    required_cols = [
        'missing_event_rate', 'duplicate_rate', 'inconsistent_rate',
        'aws_gcp_latency_ms', 'aws_azure_latency_ms', 'gcp_azure_latency_ms',
        'event_rate_per_minute', 'payload_size_variance',
        'timestamp', 'is_anomaly', 'anomaly_type', 'hour_of_day', 'day_of_week'
    ]

    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    print(f"   ✅ All required columns present: {len(required_cols)}")

    # Check data types
    assert df['is_anomaly'].dtype == 'int64', "is_anomaly should be int"
    assert df['missing_event_rate'].dtype == 'float64', "metrics should be float"
    print(f"   ✅ Correct data types")

    # Check anomalies exist
    anomaly_count = df['is_anomaly'].sum()
    assert anomaly_count > 0, "No anomalies found!"
    print(f"   ✅ Anomalies detected: {anomaly_count} minutes")

    # Check value ranges
    assert df['missing_event_rate'].min() >= 0, "Negative missing rate!"
    assert df['missing_event_rate'].max() <= 1, "Missing rate > 100%!"
    print(f"   ✅ Valid value ranges")

    print("\n3. Previewing dataset...")
    preview_dataset("test_reconciliation_metrics.csv")

    print("\n4. Checking anomaly types...")
    anomaly_types = df[df['is_anomaly'] == 1]['anomaly_type'].unique()
    print(f"   Anomaly types found: {list(anomaly_types)}")
    assert len(anomaly_types) > 0, "No anomaly types!"
    print(f"   ✅ {len(anomaly_types)} different anomaly types")

    print("\n" + "="*60)
    print("✅ ALL DATASET TESTS PASSED!")
    print("="*60)

    print("\n📊 Sample Statistics:")
    print(f"   Normal missing rate: {df[df['is_anomaly']==0]['missing_event_rate'].mean():.4f}")
    print(f"   Anomaly missing rate: {df[df['is_anomaly']==1]['missing_event_rate'].mean():.4f}")
    print(f"   Normal latency: {df[df['is_anomaly']==0]['aws_gcp_latency_ms'].mean():.2f}ms")
    print(f"   Anomaly latency: {df[df['is_anomaly']==1]['aws_gcp_latency_ms'].mean():.2f}ms")

    print("\n✅ Dataset generation works! Ready for Kaggle.")
    print(f"\n🗑️  You can delete: test_reconciliation_metrics.csv")


if __name__ == "__main__":
    test_quick_generation()
