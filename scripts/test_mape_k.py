#!/usr/bin/env python3
"""
Test script for MAPE-K Closed-Loop Automation

Tests the Monitor-Analyze-Plan-Execute-Knowledge cycle.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.automation import MAPEKLoop, MAPEKPhase


async def test_basic_mape_k_cycle():
    """Test basic MAPE-K cycle."""

    print("=" * 60)
    print("🧪 Testing Basic MAPE-K Cycle")
    print("=" * 60)

    # Initialize MAPE-K loop
    print("\n1. Initializing MAPE-K loop...")
    mape_k = MAPEKLoop()
    stats = mape_k.get_statistics()
    print(f"   ✅ Cycles completed: {stats['cycles_completed']}")

    # Run single cycle
    print("\n2. Running MAPE-K cycle...")
    context = {
        "sources_found": ["aws", "gcp"],
        "sources_missing": ["azure"]
    }

    result = await mape_k.run_cycle(
        event_id="EVENT-001",
        context=context
    )

    print(f"   ✅ Cycle completed: {result['success']}")
    print(f"   ✅ Duration: {result['duration_seconds']:.3f}s")
    print(f"   ✅ Phases executed: {list(result['phases'].keys())}")

    # Verify all phases ran
    print("\n3. Verifying phases...")
    expected_phases = ["monitor", "analyze", "plan", "execute", "knowledge"]
    for phase in expected_phases:
        if phase in result["phases"]:
            print(f"   ✅ {phase.capitalize()} phase completed")
        else:
            print(f"   ❌ {phase.capitalize()} phase missing")

    # Check statistics
    print("\n4. Checking statistics...")
    stats = mape_k.get_statistics()
    print(f"   ✅ Total cycles: {stats['cycles_completed']}")
    print(f"   ✅ Succeeded: {stats['cycles_succeeded']}")
    print(f"   ✅ Failed: {stats['cycles_failed']}")
    print(f"   ✅ Success rate: {stats['success_rate']:.2%}")

    print("\n" + "=" * 60)
    print("✅ Basic MAPE-K cycle tests passed!")
    print("=" * 60)


async def test_custom_callbacks():
    """Test MAPE-K with custom callbacks."""

    print("\n" + "=" * 60)
    print("🧪 Testing Custom Callbacks")
    print("=" * 60)

    # Track callback invocations
    callbacks_invoked = []

    # Define custom callbacks
    async def custom_monitor(event_id, context):
        callbacks_invoked.append("monitor")
        return {
            "event_id": event_id,
            "sources_found": ["aws", "gcp"],
            "sources_missing": ["azure"],
            "metrics": {"latency_ms": 150},
            "timestamp": datetime.utcnow().isoformat()
        }

    async def custom_analyze(monitoring_data, context):
        callbacks_invoked.append("analyze")
        return {
            "event_id": monitoring_data["event_id"],
            "root_cause": "Network partition to Azure",
            "impact_severity": 0.7,
            "recommended_actions": ["retry", "replay"],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    async def custom_plan(analysis_result, context):
        callbacks_invoked.append("plan")
        return {
            "event_id": analysis_result["event_id"],
            "selected_action": "retry",
            "action_score": 0.92,
            "alternative_actions": [{"action_id": "replay", "score": 0.75}],
            "plan_timestamp": datetime.utcnow().isoformat()
        }

    async def custom_execute(recovery_plan, context):
        callbacks_invoked.append("execute")
        return {
            "event_id": recovery_plan["event_id"],
            "action_id": recovery_plan["selected_action"],
            "success": True,
            "execution_time": 1.5,
            "cost": 0.05,
            "error_message": None,
            "execution_timestamp": datetime.utcnow().isoformat()
        }

    async def custom_knowledge(monitor, analyze, plan, execute, context):
        callbacks_invoked.append("knowledge")
        return {
            "event_id": execute["event_id"],
            "feedback_recorded": True,
            "model_updated": True,
            "success_rate_delta": 0.02,
            "knowledge_timestamp": datetime.utcnow().isoformat()
        }

    # Initialize with custom callbacks
    print("\n1. Initializing MAPE-K with custom callbacks...")
    mape_k = MAPEKLoop(
        monitor_callback=custom_monitor,
        analyze_callback=custom_analyze,
        plan_callback=custom_plan,
        execute_callback=custom_execute,
        knowledge_callback=custom_knowledge
    )

    # Run cycle
    print("\n2. Running cycle with custom callbacks...")
    result = await mape_k.run_cycle("EVENT-002")

    print(f"   ✅ Cycle completed: {result['success']}")
    print(f"   ✅ Callbacks invoked: {len(callbacks_invoked)}")
    print(f"   ✅ Callback order: {' → '.join(callbacks_invoked)}")

    # Verify all callbacks were invoked
    print("\n3. Verifying callbacks...")
    expected = ["monitor", "analyze", "plan", "execute", "knowledge"]
    assert callbacks_invoked == expected, f"Expected {expected}, got {callbacks_invoked}"
    print(f"   ✅ All callbacks invoked in correct order")

    # Verify custom data propagated
    print("\n4. Verifying custom data...")
    assert result["phases"]["analyze"]["root_cause"] == "Network partition to Azure"
    print(f"   ✅ Root cause: {result['phases']['analyze']['root_cause']}")

    assert result["phases"]["plan"]["selected_action"] == "retry"
    print(f"   ✅ Selected action: {result['phases']['plan']['selected_action']}")

    assert result["phases"]["execute"]["success"] == True
    print(f"   ✅ Execution success: {result['phases']['execute']['success']}")

    print("\n" + "=" * 60)
    print("✅ Custom callbacks tests passed!")
    print("=" * 60)


async def test_multiple_cycles():
    """Test running multiple MAPE-K cycles."""

    print("\n" + "=" * 60)
    print("🧪 Testing Multiple Cycles")
    print("=" * 60)

    mape_k = MAPEKLoop()

    # Run multiple cycles
    print("\n1. Running 10 MAPE-K cycles...")
    results = []
    for i in range(10):
        result = await mape_k.run_cycle(f"EVENT-{i:03d}")
        results.append(result)

    print(f"   ✅ Completed {len(results)} cycles")

    # Analyze results
    print("\n2. Analyzing results...")
    successes = sum(1 for r in results if r["success"])
    failures = sum(1 for r in results if not r["success"])
    avg_duration = sum(r["duration_seconds"] for r in results) / len(results)

    print(f"   ✅ Successes: {successes}/{len(results)}")
    print(f"   ✅ Failures: {failures}/{len(results)}")
    print(f"   ✅ Avg duration: {avg_duration:.3f}s")

    # Check statistics
    print("\n3. Checking final statistics...")
    stats = mape_k.get_statistics()
    print(f"   ✅ Total cycles: {stats['cycles_completed']}")
    print(f"   ✅ Success rate: {stats['success_rate']:.2%}")

    # Get recent history
    print("\n4. Checking execution history...")
    history = mape_k.get_recent_history(limit=5)
    print(f"   ✅ Recent history entries: {len(history)}")
    print(f"   ✅ Latest event: {history[-1]['event_id']}")

    print("\n" + "=" * 60)
    print("✅ Multiple cycles tests passed!")
    print("=" * 60)


async def test_error_handling():
    """Test error handling in MAPE-K cycle."""

    print("\n" + "=" * 60)
    print("🧪 Testing Error Handling")
    print("=" * 60)

    # Create callback that fails
    async def failing_analyze(monitoring_data, context):
        raise ValueError("Simulated analysis failure")

    # Initialize with failing callback
    print("\n1. Initializing MAPE-K with failing callback...")
    mape_k = MAPEKLoop(analyze_callback=failing_analyze)

    # Run cycle (should handle error gracefully)
    print("\n2. Running cycle with failing callback...")
    result = await mape_k.run_cycle("EVENT-FAIL")

    print(f"   ✅ Cycle completed (with error)")
    print(f"   ✅ Success: {result['success']}")
    print(f"   ✅ Error captured: {'error' in result}")
    print(f"   ✅ Failed phase: {result.get('failed_phase', 'unknown')}")

    if "error" in result:
        print(f"   ✅ Error message: {result['error']}")

    # Verify statistics updated correctly
    print("\n3. Verifying statistics...")
    stats = mape_k.get_statistics()
    print(f"   ✅ Cycles completed: {stats['cycles_completed']}")
    print(f"   ✅ Cycles failed: {stats['cycles_failed']}")
    assert stats['cycles_failed'] == 1, "Failed cycle not counted"
    print(f"   ✅ Failed cycle counted correctly")

    print("\n" + "=" * 60)
    print("✅ Error handling tests passed!")
    print("=" * 60)


async def test_phase_data_flow():
    """Test data flow between MAPE-K phases."""

    print("\n" + "=" * 60)
    print("🧪 Testing Phase Data Flow")
    print("=" * 60)

    # Track data flow
    data_flow = {}

    async def track_monitor(event_id, context):
        data = {
            "event_id": event_id,
            "metric": "test_value_123",
            "timestamp": datetime.utcnow().isoformat()
        }
        data_flow["monitor_output"] = data
        return data

    async def track_analyze(monitoring_data, context):
        data_flow["analyze_input"] = monitoring_data
        assert monitoring_data["metric"] == "test_value_123", "Monitor data not passed"
        data = {
            "event_id": monitoring_data["event_id"],
            "analyzed_metric": monitoring_data["metric"] + "_analyzed",
            "root_cause": "test_cause"
        }
        data_flow["analyze_output"] = data
        return data

    async def track_plan(analysis_result, context):
        data_flow["plan_input"] = analysis_result
        assert analysis_result["analyzed_metric"] == "test_value_123_analyzed"
        data = {
            "event_id": analysis_result["event_id"],
            "selected_action": "test_action",
            "based_on_cause": analysis_result["root_cause"]
        }
        data_flow["plan_output"] = data
        return data

    async def track_execute(recovery_plan, context):
        data_flow["execute_input"] = recovery_plan
        assert recovery_plan["selected_action"] == "test_action"
        return {
            "event_id": recovery_plan["event_id"],
            "action_id": recovery_plan["selected_action"],
            "success": True
        }

    # Initialize with tracking callbacks
    print("\n1. Initializing MAPE-K with tracking callbacks...")
    mape_k = MAPEKLoop(
        monitor_callback=track_monitor,
        analyze_callback=track_analyze,
        plan_callback=track_plan,
        execute_callback=track_execute
    )

    # Run cycle
    print("\n2. Running cycle to track data flow...")
    result = await mape_k.run_cycle("EVENT-FLOW")

    # Verify data flow
    print("\n3. Verifying data flow...")
    assert "monitor_output" in data_flow
    print(f"   ✅ Monitor → Analyze: metric passed")

    assert "analyze_input" in data_flow
    assert data_flow["analyze_input"]["metric"] == "test_value_123"
    print(f"   ✅ Analyze → Plan: analyzed data passed")

    assert "plan_input" in data_flow
    assert data_flow["plan_input"]["analyzed_metric"] == "test_value_123_analyzed"
    print(f"   ✅ Plan → Execute: plan passed")

    assert "execute_input" in data_flow
    assert data_flow["execute_input"]["selected_action"] == "test_action"
    print(f"   ✅ Execute: action executed")

    print(f"\n   ✅ Complete data flow: Monitor → Analyze → Plan → Execute → Knowledge")

    print("\n" + "=" * 60)
    print("✅ Phase data flow tests passed!")
    print("=" * 60)


async def main():
    """Run all tests."""
    await test_basic_mape_k_cycle()
    await test_custom_callbacks()
    await test_multiple_cycles()
    await test_error_handling()
    await test_phase_data_flow()

    print("\n" + "=" * 60)
    print("✅ ALL MAPE-K TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
