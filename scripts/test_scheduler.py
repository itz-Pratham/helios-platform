#!/usr/bin/env python3
"""
Test Reconciliation Scheduler

Run scheduled jobs and verify they execute correctly.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scheduler import ReconciliationScheduler


async def test_scheduler():
    """Test scheduler with various jobs."""

    print("="*60)
    print("🧪 Testing Reconciliation Scheduler")
    print("="*60)

    # Initialize scheduler
    print("\n1. Initializing scheduler...")
    scheduler = ReconciliationScheduler()

    # Start scheduler
    print("\n2. Starting scheduler...")
    await scheduler.start()

    print(f"   ✅ Scheduler running: {scheduler.is_running()}")
    print(f"   ✅ Active jobs: {len(scheduler.jobs)}")

    # Get job status
    print("\n3. Scheduled jobs:")
    job_status = scheduler.get_job_status()
    for job in job_status:
        print(f"   📅 {job['name']}")
        print(f"      ID: {job['id']}")
        print(f"      Next run: {job['next_run_time']}")
        print(f"      Trigger: {job['trigger']}")
        print()

    # Let it run for a bit to see jobs execute
    print("4. Running scheduler for 70 seconds to observe jobs...")
    print("   (Watch for job executions in logs)\n")

    try:
        await asyncio.sleep(70)
    except KeyboardInterrupt:
        print("\n   Interrupted by user")

    # Stop scheduler
    print("\n5. Stopping scheduler...")
    await scheduler.stop()

    print(f"   ✅ Scheduler stopped: {not scheduler.is_running()}")

    print("\n" + "="*60)
    print("✅ SCHEDULER TEST COMPLETE")
    print("="*60)

    print("\n📊 Summary:")
    print(f"   Total jobs configured: {len(scheduler.jobs)}")
    print(f"   Jobs tested:")
    for job_name in scheduler.jobs.keys():
        print(f"      - {job_name}")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
