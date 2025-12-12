"""Integration tests for job execution."""
import json
import time
import pytest
from datetime import datetime, timezone, timedelta
from job_scheduler.core import JobScheduler
from job_scheduler.models import Job


class TestRecurringJob:
    """Test recurring job execution."""
    
    def test_recurring_job_scheduling(self):
        """Test scheduling a recurring job."""
        job_data = {
            'job_id': 'test-recurring',
            'description': 'Test recurring job',
            'schedule': '*/1 * * * *',  # Every minute
            'task': {
                'type': 'execute_command',
                'command': 'echo "Recurring job executed"'
            }
        }
        
        job = Job.from_dict(job_data)
        scheduler = JobScheduler()
        scheduler.add_job(job)
        
        assert 'test-recurring' in scheduler.jobs
        assert 'test-recurring' in scheduler.scheduled_jobs


class TestOneTimeJob:
    """Test one-time job execution."""
    
    def test_one_time_job_scheduling(self):
        """Test scheduling a one-time job."""
        # Schedule for 1 minute from now
        future_time = datetime.now(timezone.utc) + timedelta(minutes=1)
        schedule_str = future_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        job_data = {
            'job_id': 'test-onetime',
            'description': 'Test one-time job',
            'schedule': schedule_str,
            'task': {
                'type': 'execute_command',
                'command': 'echo "One-time job executed"'
            }
        }
        
        job = Job.from_dict(job_data)
        scheduler = JobScheduler()
        scheduler.add_job(job)
        
        assert 'test-onetime' in scheduler.jobs
        assert 'test-onetime' in scheduler.scheduled_jobs

