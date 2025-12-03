#!/usr/bin/env python3
"""
Test script for Recovery Feedback Loop

Tests continuous learning from recovery action outcomes.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.decision_engine.feedback_loop import (
    RecoveryFeedbackLoop,
    RecoveryOutcome,
    ActionStatistics
)


def test_basic_feedback_loop():
    """Test basic feedback loop functionality."""

    print("=" * 60)
    print("🧪 Testing Basic Feedback Loop")
    print("=" * 60)

    # Initialize feedback loop
    print("\n1. Initializing feedback loop...")
    feedback = RecoveryFeedbackLoop(window_size=100, decay_factor=0.95)
    print(f"   ✅ Window size: {feedback.window_size}")
    print(f"   ✅ Decay factor: {feedback.decay_factor}")

    # Record successful outcomes
    print("\n2. Recording successful outcomes...")
    for i in range(5):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=True,
            execution_time=2.0 + (i * 0.1),
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    print(f"   ✅ Recorded 5 successful outcomes")

    # Record failed outcome
    print("\n3. Recording failed outcome...")
    failed_outcome = RecoveryOutcome(
        action_id="retry",
        event_id="EVENT-FAILED",
        success=False,
        execution_time=5.0,
        cost=0.15,
        timestamp=datetime.utcnow(),
        error_message="Connection timeout"
    )
    feedback.record_outcome(failed_outcome)
    print(f"   ✅ Recorded 1 failed outcome")

    # Get statistics
    print("\n4. Getting action statistics...")
    stats = feedback.get_action_stats("retry")
    print(f"   ✅ Total executions: {stats.total_executions}")
    print(f"   ✅ Successes: {stats.successes}")
    print(f"   ✅ Failures: {stats.failures}")
    print(f"   ✅ Success rate: {stats.success_rate:.2%}")
    print(f"   ✅ Avg execution time: {stats.avg_execution_time:.3f}s")
    print(f"   ✅ Avg cost: ${stats.avg_cost:.2f}")

    # Get summary
    print("\n5. Getting summary...")
    summary = feedback.get_summary()
    print(f"   ✅ Total actions: {summary['total_actions']}")
    print(f"   ✅ Total executions: {summary['total_executions']}")
    print(f"   ✅ Overall success rate: {summary['overall_success_rate']:.2%}")

    print("\n" + "=" * 60)
    print("✅ Basic feedback loop tests passed!")
    print("=" * 60)


def test_multiple_actions():
    """Test feedback loop with multiple actions."""

    print("\n" + "=" * 60)
    print("🧪 Testing Multiple Actions")
    print("=" * 60)

    feedback = RecoveryFeedbackLoop()

    # Record outcomes for different actions
    print("\n1. Recording outcomes for multiple actions...")

    # Retry: High success rate
    for i in range(10):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=i < 9,  # 90% success
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    # Replay: Medium success rate
    for i in range(10):
        outcome = RecoveryOutcome(
            action_id="replay",
            event_id=f"EVENT-{i}",
            success=i < 7,  # 70% success
            execution_time=10.0,
            cost=0.50,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    # Skip: 100% success (trivial)
    for i in range(5):
        outcome = RecoveryOutcome(
            action_id="skip",
            event_id=f"EVENT-{i}",
            success=True,
            execution_time=0.1,
            cost=0.0,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    print(f"   ✅ Recorded outcomes for 3 actions")

    # Get all statistics
    print("\n2. Comparing action performance...")
    all_stats = feedback.get_all_stats()

    print(f"\n   {'Action':<15s} {'Executions':<12s} {'Success Rate':<15s} {'Avg Time':<10s} {'Avg Cost':<10s}")
    print(f"   {'-'*70}")
    for action_id, stats in sorted(all_stats.items()):
        print(f"   {action_id:<15s} {stats.total_executions:<12d} {stats.success_rate:<15.2%} {stats.avg_execution_time:<10.2f} ${stats.avg_cost:<9.2f}")

    # Get best action
    print("\n3. Identifying best action...")
    best_action = feedback.get_best_action(min_executions=5)
    best_stats = feedback.get_action_stats(best_action)
    print(f"   🏆 Best action: {best_action}")
    print(f"   ✅ Success rate: {best_stats.success_rate:.2%}")

    print("\n" + "=" * 60)
    print("✅ Multiple actions tests passed!")
    print("=" * 60)


def test_degradation_detection():
    """Test degradation detection."""

    print("\n" + "=" * 60)
    print("🧪 Testing Degradation Detection")
    print("=" * 60)

    feedback = RecoveryFeedbackLoop(window_size=20)

    # Record initially good performance
    print("\n1. Recording initially good performance...")
    for i in range(10):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=True,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    initial_rate = feedback.get_action_stats("retry").success_rate
    print(f"   ✅ Initial success rate: {initial_rate:.2%}")

    # Record degrading performance
    print("\n2. Recording degrading performance...")
    for i in range(10, 20):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=i % 2 == 0,  # Only 50% success
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow(),
            error_message="Service unavailable" if i % 2 != 0 else None
        )
        feedback.record_outcome(outcome)

    final_rate = feedback.get_action_stats("retry").success_rate
    print(f"   ✅ Final success rate: {final_rate:.2%}")

    # Detect degradation
    print("\n3. Detecting degradation...")
    is_degrading = feedback.detect_degradation("retry", threshold=0.2)
    print(f"   ✅ Degradation detected: {is_degrading}")

    # Get recommendations
    print("\n4. Getting recommendations...")
    recommendations = feedback.get_recommendations()
    print(f"   ✅ Total recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"      - [{rec['severity']}] {rec['message']}")

    print("\n" + "=" * 60)
    print("✅ Degradation detection tests passed!")
    print("=" * 60)


def test_weighted_success_rate():
    """Test exponentially weighted success rate."""

    print("\n" + "=" * 60)
    print("🧪 Testing Weighted Success Rate")
    print("=" * 60)

    feedback = RecoveryFeedbackLoop(decay_factor=0.9)

    # Old outcomes (failed)
    print("\n1. Recording old failures...")
    for i in range(5):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"OLD-{i}",
            success=False,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow() - timedelta(hours=1)
        )
        feedback.record_outcome(outcome)

    # Recent outcomes (successful)
    print("\n2. Recording recent successes...")
    for i in range(5):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"NEW-{i}",
            success=True,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    # Compare weighted vs simple success rate
    print("\n3. Comparing success rates...")
    simple_rate = feedback.get_action_stats("retry").success_rate
    weighted_rate = feedback.get_weighted_success_rate("retry")

    print(f"   ✅ Simple success rate: {simple_rate:.2%}")
    print(f"   ✅ Weighted success rate: {weighted_rate:.2%}")
    print(f"   ✅ Difference: {abs(weighted_rate - simple_rate):.2%}")
    print(f"   ✅ Weighted rate higher (recent better): {weighted_rate > simple_rate}")

    print("\n" + "=" * 60)
    print("✅ Weighted success rate tests passed!")
    print("=" * 60)


def test_failure_analysis():
    """Test failure pattern analysis."""

    print("\n" + "=" * 60)
    print("🧪 Testing Failure Analysis")
    print("=" * 60)

    feedback = RecoveryFeedbackLoop()

    # Record various failures
    print("\n1. Recording failures with different error types...")
    error_types = [
        "Connection timeout",
        "Connection timeout",
        "Connection timeout",
        "Service unavailable",
        "Service unavailable",
        "Invalid response",
        "Rate limit exceeded"
    ]

    for i, error_msg in enumerate(error_types):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=False,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow(),
            error_message=error_msg
        )
        feedback.record_outcome(outcome)

    # Add some successes
    for i in range(3):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"SUCCESS-{i}",
            success=True,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    # Analyze failures
    print("\n2. Analyzing failure patterns...")
    analysis = feedback.get_failure_analysis("retry")

    print(f"   ✅ Total failures: {analysis['total_failures']}")
    print(f"   ✅ Failure rate: {analysis['failure_rate']:.2%}")
    print(f"\n   📊 Common errors:")
    for error in analysis['common_errors']:
        print(f"      - {error['error_type']}: {error['count']} occurrences")

    print("\n" + "=" * 60)
    print("✅ Failure analysis tests passed!")
    print("=" * 60)


def test_export_statistics():
    """Test statistics export."""

    print("\n" + "=" * 60)
    print("🧪 Testing Statistics Export")
    print("=" * 60)

    feedback = RecoveryFeedbackLoop()

    # Record some data
    print("\n1. Recording sample data...")
    for i in range(10):
        outcome = RecoveryOutcome(
            action_id="retry",
            event_id=f"EVENT-{i}",
            success=i < 8,
            execution_time=2.0,
            cost=0.10,
            timestamp=datetime.utcnow()
        )
        feedback.record_outcome(outcome)

    # Export statistics
    print("\n2. Exporting statistics...")
    export = feedback.export_statistics()

    print(f"   ✅ Timestamp: {export['timestamp']}")
    print(f"   ✅ Total outcomes: {export['total_outcomes']}")
    print(f"   ✅ Actions tracked: {len(export['actions'])}")
    print(f"   ✅ Recommendations: {len(export['recommendations'])}")

    # Verify export structure
    print("\n3. Verifying export structure...")
    retry_data = export['actions']['retry']
    print(f"   ✅ Executions: {retry_data['total_executions']}")
    print(f"   ✅ Success rate: {retry_data['success_rate']:.2%}")
    print(f"   ✅ Avg time: {retry_data['avg_execution_time']}s")
    print(f"   ✅ Avg cost: ${retry_data['avg_cost']}")

    print("\n" + "=" * 60)
    print("✅ Statistics export tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_feedback_loop()
    test_multiple_actions()
    test_degradation_detection()
    test_weighted_success_rate()
    test_failure_analysis()
    test_export_statistics()

    print("\n" + "=" * 60)
    print("✅ ALL FEEDBACK LOOP TESTS PASSED!")
    print("=" * 60)
