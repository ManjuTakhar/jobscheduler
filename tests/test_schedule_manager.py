"""Tests for schedule manager."""
import pytest
from datetime import datetime, timezone

from job_scheduler.core.schedule_manager import ScheduleManager
from job_scheduler.models import Job, ExecuteCommandTask
from job_scheduler.logging import SchedulerLogger


class TestScheduleManager:
    """Test cases for ScheduleManager."""
    
    @pytest.fixture
    def schedule_manager(self):
        """Create a schedule manager instance."""
        logger = SchedulerLogger("logs")
        return ScheduleManager(logger)
    
    def test_create_recurring_job(self, schedule_manager):
        """Test creating a recurring scheduled job."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "0 * * * *", task)
        
        scheduled_job = schedule_manager.create_scheduled_job(job)
        assert scheduled_job is not None
        assert scheduled_job.job == job
    
    def test_create_one_time_job(self, schedule_manager):
        """Test creating a one-time scheduled job."""
        task = ExecuteCommandTask("echo 'test'")
        future_time = "2026-12-31T23:59:59Z"
        job = Job("test", "", future_time, task)
        
        scheduled_job = schedule_manager.create_scheduled_job(job)
        assert scheduled_job is not None
        assert scheduled_job.job == job
    
    def test_invalid_cron_expression(self, schedule_manager):
        """Test handling invalid cron expression."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "invalid cron", task)
        
        scheduled_job = schedule_manager.create_scheduled_job(job)
        assert scheduled_job is None
    
    def test_invalid_timestamp(self, schedule_manager):
        """Test handling invalid timestamp."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test", "", "invalid-timestamp", task)
        
        scheduled_job = schedule_manager.create_scheduled_job(job)
        assert scheduled_job is None
    
    def test_past_one_time_job(self, schedule_manager):
        """Test that past one-time jobs are not scheduled."""
        task = ExecuteCommandTask("echo 'test'")
        past_time = "2020-01-01T00:00:00Z"
        job = Job("test", "", past_time, task)
        
        scheduled_job = schedule_manager.create_scheduled_job(job)
        assert scheduled_job is None

