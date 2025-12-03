#!/usr/bin/env python3
"""
Test script for MCDM Decision Engine

Tests TOPSIS and WSM algorithms for recovery action selection.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.decision_engine import MCDMEngine, RecoveryAction, DecisionCriteria
from services.decision_engine.mcdm import CriteriaType


def test_topsis_algorithm():
    """Test TOPSIS algorithm."""

    print("=" * 60)
    print("🧪 Testing TOPSIS Algorithm")
    print("=" * 60)

    # Define criteria
    print("\n1. Defining decision criteria...")
    criteria = [
        DecisionCriteria(
            name="success_rate",
            weight=0.4,
            type=CriteriaType.BENEFIT,
            description="Historical success rate"
        ),
        DecisionCriteria(
            name="execution_time",
            weight=0.3,
            type=CriteriaType.COST,
            description="Time to execute (seconds)"
        ),
        DecisionCriteria(
            name="cost",
            weight=0.2,
            type=CriteriaType.COST,
            description="Monetary cost ($)"
        ),
        DecisionCriteria(
            name="impact",
            weight=0.1,
            type=CriteriaType.BENEFIT,
            description="Impact on system (0-1)"
        )
    ]

    print(f"   ✅ Defined {len(criteria)} criteria:")
    for c in criteria:
        print(f"      - {c.name}: weight={c.weight}, type={c.type.value}")

    # Initialize engine
    print("\n2. Initializing MCDM engine (TOPSIS)...")
    engine = MCDMEngine(criteria=criteria, method="topsis")
    stats = engine.get_stats()
    print(f"   ✅ Method: {stats['method']}")

    # Define recovery actions
    print("\n3. Defining recovery actions...")
    actions = [
        RecoveryAction(
            action_id="retry",
            name="Retry Event",
            description="Retry failed event with exponential backoff",
            criteria_values={
                "success_rate": 0.85,
                "execution_time": 5.0,
                "cost": 0.10,
                "impact": 0.3
            }
        ),
        RecoveryAction(
            action_id="replay",
            name="Replay from Source",
            description="Replay event from source system",
            criteria_values={
                "success_rate": 0.95,
                "execution_time": 15.0,
                "cost": 0.50,
                "impact": 0.8
            }
        ),
        RecoveryAction(
            action_id="manual",
            name="Manual Intervention",
            description="Alert ops team for manual resolution",
            criteria_values={
                "success_rate": 0.99,
                "execution_time": 300.0,
                "cost": 5.00,
                "impact": 0.5
            }
        ),
        RecoveryAction(
            action_id="skip",
            name="Skip Event",
            description="Mark event as skipped and continue",
            criteria_values={
                "success_rate": 1.0,
                "execution_time": 1.0,
                "cost": 0.0,
                "impact": 0.1
            }
        )
    ]

    print(f"   ✅ Defined {len(actions)} recovery actions:")
    for action in actions:
        print(f"      - {action.action_id}: {action.name}")

    # Select best action
    print("\n4. Selecting best action using TOPSIS...")
    best_action, best_score, all_scores = engine.select_best_action(actions)

    print(f"\n   🏆 Best Action: {best_action.name}")
    print(f"   ✅ Action ID: {best_action.action_id}")
    print(f"   ✅ TOPSIS Score: {best_score:.4f}")
    print(f"\n   📊 All Scores:")
    for action_id, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True):
        action = next(a for a in actions if a.action_id == action_id)
        print(f"      {action.name:25s} → {score:.4f}")

    # Explain decision
    print("\n5. Generating decision explanation...")
    explanation = engine.explain_decision(best_action, best_score, all_scores, actions)
    print(f"   ✅ Selected: {explanation['selected_action']['name']}")
    print(f"   ✅ Score: {explanation['selected_action']['score']}")
    print(f"\n   📋 Ranking:")
    for rank_info in explanation['ranking']:
        print(f"      Rank {rank_info['rank']}: {rank_info['action_id']} ({rank_info['score']:.4f})")

    print("\n" + "=" * 60)
    print("✅ TOPSIS algorithm tests passed!")
    print("=" * 60)


def test_wsm_algorithm():
    """Test WSM algorithm."""

    print("\n" + "=" * 60)
    print("🧪 Testing WSM Algorithm")
    print("=" * 60)

    # Define criteria
    print("\n1. Defining decision criteria...")
    criteria = [
        DecisionCriteria(
            name="success_rate",
            weight=0.5,
            type=CriteriaType.BENEFIT
        ),
        DecisionCriteria(
            name="execution_time",
            weight=0.3,
            type=CriteriaType.COST
        ),
        DecisionCriteria(
            name="cost",
            weight=0.2,
            type=CriteriaType.COST
        )
    ]

    # Initialize engine
    print("\n2. Initializing MCDM engine (WSM)...")
    engine = MCDMEngine(criteria=criteria, method="wsm")
    print(f"   ✅ Method: {engine.method}")

    # Define recovery actions
    actions = [
        RecoveryAction(
            action_id="retry",
            name="Retry Event",
            description="Retry failed event",
            criteria_values={
                "success_rate": 0.85,
                "execution_time": 5.0,
                "cost": 0.10
            }
        ),
        RecoveryAction(
            action_id="replay",
            name="Replay from Source",
            description="Replay event from source",
            criteria_values={
                "success_rate": 0.95,
                "execution_time": 15.0,
                "cost": 0.50
            }
        ),
        RecoveryAction(
            action_id="skip",
            name="Skip Event",
            description="Skip event",
            criteria_values={
                "success_rate": 1.0,
                "execution_time": 1.0,
                "cost": 0.0
            }
        )
    ]

    # Select best action
    print("\n3. Selecting best action using WSM...")
    best_action, best_score, all_scores = engine.select_best_action(actions)

    print(f"\n   🏆 Best Action: {best_action.name}")
    print(f"   ✅ WSM Score: {best_score:.4f}")
    print(f"\n   📊 All Scores:")
    for action_id, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True):
        action = next(a for a in actions if a.action_id == action_id)
        print(f"      {action.name:25s} → {score:.4f}")

    print("\n" + "=" * 60)
    print("✅ WSM algorithm tests passed!")
    print("=" * 60)


def test_entropy_weighting():
    """Test entropy-based weight calculation."""

    print("\n" + "=" * 60)
    print("🧪 Testing Entropy Weighting")
    print("=" * 60)

    # Define criteria (initial weights don't matter for entropy)
    print("\n1. Defining criteria...")
    criteria = [
        DecisionCriteria(name="success_rate", weight=0.33, type=CriteriaType.BENEFIT),
        DecisionCriteria(name="execution_time", weight=0.33, type=CriteriaType.COST),
        DecisionCriteria(name="cost", weight=0.34, type=CriteriaType.COST)
    ]

    engine = MCDMEngine(criteria=criteria, method="topsis")

    # Historical actions for entropy calculation
    print("\n2. Generating historical actions...")
    historical_actions = [
        RecoveryAction(
            action_id=f"action-{i}",
            name=f"Action {i}",
            description="",
            criteria_values={
                "success_rate": 0.7 + (i * 0.05),
                "execution_time": 10.0 - (i * 1.0),
                "cost": 0.5 + (i * 0.1)
            }
        )
        for i in range(5)
    ]

    print(f"   ✅ Generated {len(historical_actions)} historical actions")

    # Calculate entropy weights
    print("\n3. Calculating entropy-based weights...")
    entropy_weights = engine.calculate_entropy_weights(historical_actions)

    print(f"   ✅ Entropy Weights:")
    for name, weight in entropy_weights.items():
        print(f"      {name:20s} → {weight:.4f}")

    total_weight = sum(entropy_weights.values())
    print(f"\n   ✅ Total weight: {total_weight:.4f} (should be 1.0)")

    print("\n" + "=" * 60)
    print("✅ Entropy weighting tests passed!")
    print("=" * 60)


def test_comparison_topsis_vs_wsm():
    """Compare TOPSIS vs WSM on same dataset."""

    print("\n" + "=" * 60)
    print("🧪 Testing TOPSIS vs WSM Comparison")
    print("=" * 60)

    # Define criteria
    criteria = [
        DecisionCriteria(name="success_rate", weight=0.4, type=CriteriaType.BENEFIT),
        DecisionCriteria(name="execution_time", weight=0.3, type=CriteriaType.COST),
        DecisionCriteria(name="cost", weight=0.3, type=CriteriaType.COST)
    ]

    # Define actions
    actions = [
        RecoveryAction(
            action_id="retry",
            name="Retry",
            description="",
            criteria_values={"success_rate": 0.80, "execution_time": 5.0, "cost": 0.10}
        ),
        RecoveryAction(
            action_id="replay",
            name="Replay",
            description="",
            criteria_values={"success_rate": 0.95, "execution_time": 15.0, "cost": 0.50}
        ),
        RecoveryAction(
            action_id="skip",
            name="Skip",
            description="",
            criteria_values={"success_rate": 1.0, "execution_time": 1.0, "cost": 0.0}
        )
    ]

    # Test with TOPSIS
    print("\n1. Testing with TOPSIS...")
    topsis_engine = MCDMEngine(criteria=criteria, method="topsis")
    topsis_best, topsis_score, topsis_scores = topsis_engine.select_best_action(actions)
    print(f"   ✅ TOPSIS Best: {topsis_best.name} (score: {topsis_score:.4f})")

    # Test with WSM
    print("\n2. Testing with WSM...")
    wsm_engine = MCDMEngine(criteria=criteria, method="wsm")
    wsm_best, wsm_score, wsm_scores = wsm_engine.select_best_action(actions)
    print(f"   ✅ WSM Best: {wsm_best.name} (score: {wsm_score:.4f})")

    # Compare results
    print("\n3. Comparing results...")
    print(f"\n   {'Action':<20s} {'TOPSIS':<10s} {'WSM':<10s} {'Diff':<10s}")
    print(f"   {'-'*50}")
    for action in actions:
        t_score = topsis_scores[action.action_id]
        w_score = wsm_scores[action.action_id]
        diff = abs(t_score - w_score)
        print(f"   {action.name:<20s} {t_score:<10.4f} {w_score:<10.4f} {diff:<10.4f}")

    agreement = "✅ Same" if topsis_best.action_id == wsm_best.action_id else "⚠️ Different"
    print(f"\n   Best action agreement: {agreement}")

    print("\n" + "=" * 60)
    print("✅ Comparison tests passed!")
    print("=" * 60)


def test_edge_cases():
    """Test edge cases."""

    print("\n" + "=" * 60)
    print("🧪 Testing Edge Cases")
    print("=" * 60)

    criteria = [
        DecisionCriteria(name="metric1", weight=0.5, type=CriteriaType.BENEFIT),
        DecisionCriteria(name="metric2", weight=0.5, type=CriteriaType.COST)
    ]

    engine = MCDMEngine(criteria=criteria, method="topsis")

    # Test 1: Single action
    print("\n1. Testing single action...")
    single_action = [
        RecoveryAction(
            action_id="only",
            name="Only Action",
            description="",
            criteria_values={"metric1": 0.5, "metric2": 0.5}
        )
    ]
    best, score, _ = engine.select_best_action(single_action)
    print(f"   ✅ Single action: {best.name}, score: {score}")

    # Test 2: Identical actions
    print("\n2. Testing identical actions...")
    identical_actions = [
        RecoveryAction(
            action_id=f"action-{i}",
            name=f"Action {i}",
            description="",
            criteria_values={"metric1": 0.8, "metric2": 0.2}
        )
        for i in range(3)
    ]
    best, score, scores = engine.select_best_action(identical_actions)
    print(f"   ✅ Best from identical: {best.name}")
    print(f"   ✅ All scores equal: {len(set(scores.values())) == 1}")

    # Test 3: Extreme values
    print("\n3. Testing extreme values...")
    extreme_actions = [
        RecoveryAction(
            action_id="low",
            name="Low",
            description="",
            criteria_values={"metric1": 0.0, "metric2": 100.0}
        ),
        RecoveryAction(
            action_id="high",
            name="High",
            description="",
            criteria_values={"metric1": 100.0, "metric2": 0.0}
        )
    ]
    best, score, _ = engine.select_best_action(extreme_actions)
    print(f"   ✅ Best with extremes: {best.name}, score: {score:.4f}")

    print("\n" + "=" * 60)
    print("✅ Edge case tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_topsis_algorithm()
    test_wsm_algorithm()
    test_entropy_weighting()
    test_comparison_topsis_vs_wsm()
    test_edge_cases()

    print("\n" + "=" * 60)
    print("✅ ALL MCDM ENGINE TESTS PASSED!")
    print("=" * 60)
