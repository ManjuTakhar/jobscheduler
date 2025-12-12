#!/usr/bin/env python3
"""Test script to verify job execution."""
import json
import time
from datetime import datetime, timezone, timedelta
from job_scheduler.scheduler import JobScheduler
from job_scheduler.models import Job

def test_recurring_job():
    """Test a recurring job that runs every minute."""
    print("=" * 60)
    print("Testing Recurring Job (every minute)")
    print("=" * 60)
    
    job_data = {
        'job_id': 'test-recurring',
        'description': 'Test recurring job',
        'schedule': '*/1 * * * *',  # Every minute
        'task': {
            'type': 'execute_command',
            'command': 'echo "Recurring job executed at $(date)"'
        }
    }
    
    job = Job.from_dict(job_data)
    scheduler = JobScheduler()
    scheduler.add_job(job)
    
    if 'test-recurring' in scheduler.scheduled_jobs:
        scheduled_job = scheduler.scheduled_jobs['test-recurring']
        print(f"Job scheduled. Next run time: {scheduled_job.next_run_time}")
        print(f"Current time: {datetime.now(timezone.utc)}")
        print(f"Should run now: {scheduled_job.should_run()}")
    
    scheduler.start()
    print("\nScheduler started. Waiting 65 seconds to see execution...")
    print("(You should see job execution logs)\n")
    
    time.sleep(65)
    scheduler.stop()
    print("\nScheduler stopped.")


def test_one_time_job():
    """Test a one-time job scheduled for the near future."""
    print("\n" + "=" * 60)
    print("Testing One-Time Job")
    print("=" * 60)
    
    # Schedule for 30 seconds from now
    future_time = datetime.now(timezone.utc) + timedelta(seconds=30)
    schedule_str = future_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Scheduling one-time job for: {schedule_str}")
    
    job_data = {
        'job_id': 'test-onetime',
        'description': 'Test one-time job',
        'schedule': schedule_str,
        'task': {
            'type': 'execute_command',
            'command': 'echo "One-time job executed at $(date)"'
        }
    }
    
    job = Job.from_dict(job_data)
    scheduler = JobScheduler()
    scheduler.add_job(job)
    
    if 'test-onetime' in scheduler.scheduled_jobs:
        scheduled_job = scheduler.scheduled_jobs['test-onetime']
        print(f"Job scheduled. Scheduled time: {scheduled_job.schedule_time}")
        print(f"Current time: {datetime.now(timezone.utc)}")
        print(f"Should run now: {scheduled_job.should_run()}")
    
    scheduler.start()
    print("\nScheduler started. Waiting 35 seconds for execution...")
    print("(You should see job execution log)\n")
    
    time.sleep(35)
    scheduler.stop()
    print("\nScheduler stopped.")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'onetime':
        test_one_time_job()
    elif len(sys.argv) > 1 and sys.argv[1] == 'recurring':
        test_recurring_job()
    else:
        print("Usage: python test_job_execution.py [recurring|onetime]")
        print("\nRunning both tests...\n")
        test_recurring_job()
        test_one_time_job()

