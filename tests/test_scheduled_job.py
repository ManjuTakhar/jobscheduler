"""Tests for scheduled job classes."""
from datetime import datetime, timezone, timedelta
import pytest

from job_scheduler.core.scheduled_job import (
    ScheduledJob,
    OneTimeScheduledJob,
    RecurringScheduledJob
)
from job_scheduler.models import Job, ExecuteCommandTask
from croniter import croniter


class TestScheduledJob:
    """Test cases for ScheduledJob base class."""
    
    def test_scheduled_job_initialization(self):
        """Test scheduled job initialization."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        scheduled_job = ScheduledJob(job)
        
        assert scheduled_job.job == job
        assert not scheduled_job.cancelled
    
    def test_cancel(self):
        """Test canceling a scheduled job."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        scheduled_job = ScheduledJob(job)
        
        scheduled_job.cancel()
        assert scheduled_job.cancelled


class TestOneTimeScheduledJob:
    """Test cases for OneTimeScheduledJob."""
    
    def test_one_time_job_initialization(self):
        """Test one-time job initialization."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "2025-12-31T23:59:59Z", task)
        schedule_time = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        scheduled_job = OneTimeScheduledJob(job, schedule_time)
        assert scheduled_job.schedule_time == schedule_time
    
    def test_should_run_future(self):
        """Test should_run for future schedule."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "2025-12-31T23:59:59Z", task)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        scheduled_job = OneTimeScheduledJob(job, future_time)
        assert not scheduled_job.should_run()
    
    def test_should_run_past(self):
        """Test should_run for past schedule."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "2020-01-01T00:00:00Z", task)
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        scheduled_job = OneTimeScheduledJob(job, past_time)
        assert scheduled_job.should_run()
    
    def test_should_run_cancelled(self):
        """Test should_run when cancelled."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "2020-01-01T00:00:00Z", task)
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        scheduled_job = OneTimeScheduledJob(job, past_time)
        scheduled_job.cancel()
        assert not scheduled_job.should_run()


class TestRecurringScheduledJob:
    """Test cases for RecurringScheduledJob."""
    
    def test_recurring_job_initialization(self):
        """Test recurring job initialization."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        cron = croniter("0 * * * *", datetime.now(timezone.utc))
        
        scheduled_job = RecurringScheduledJob(job, cron)
        assert scheduled_job.cron == cron
        assert scheduled_job.next_run_time is not None
    
    def test_reschedule(self):
        """Test rescheduling a recurring job."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        cron = croniter("0 * * * *", datetime.now(timezone.utc))
        
        scheduled_job = RecurringScheduledJob(job, cron)
        old_next_run = scheduled_job.next_run_time
        
        scheduled_job.reschedule()
        assert scheduled_job.next_run_time != old_next_run
        assert scheduled_job.next_run_time > old_next_run
    
    def test_should_run_cancelled(self):
        """Test should_run when cancelled."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        cron = croniter("0 * * * *", datetime.now(timezone.utc) - timedelta(hours=1))
        
        scheduled_job = RecurringScheduledJob(job, cron)
        scheduled_job.cancel()
        assert not scheduled_job.should_run()
    
    def test_mark_executed(self):
        """Test marking job as executed."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        cron = croniter("0 * * * *", datetime.now(timezone.utc))
        
        scheduled_job = RecurringScheduledJob(job, cron)
        old_check_time = scheduled_job.last_check_time
        
        scheduled_job.mark_executed()
        assert scheduled_job.last_check_time >= old_check_time

