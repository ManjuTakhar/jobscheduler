"""Tests for the core scheduler."""
import time
import tempfile
import shutil
from pathlib import Path
import pytest

from job_scheduler.core import JobScheduler
from job_scheduler.watchers import JobFileWatcher
from job_scheduler.models import Job, ExecuteCommandTask


class TestJobScheduler:
    """Test cases for JobScheduler."""
    
    def test_scheduler_initialization(self):
        """Test scheduler can be initialized."""
        scheduler = JobScheduler()
        assert scheduler is not None
        assert not scheduler.running
        assert len(scheduler.jobs) == 0
    
    def test_add_job(self):
        """Test adding a job to the scheduler."""
        scheduler = JobScheduler()
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test-job", "Test job", "0 * * * *", task)
        
        scheduler.add_job(job)
        assert "test-job" in scheduler.jobs
        assert scheduler.jobs["test-job"] == job
    
    def test_remove_job(self):
        """Test removing a job from the scheduler."""
        scheduler = JobScheduler()
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test-job", "Test job", "0 * * * *", task)
        
        scheduler.add_job(job)
        assert "test-job" in scheduler.jobs
        
        scheduler.remove_job("test-job")
        assert "test-job" not in scheduler.jobs
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler."""
        scheduler = JobScheduler()
        scheduler.start()
        assert scheduler.running
        
        time.sleep(0.1)  # Give it a moment to start
        scheduler.stop()
        assert not scheduler.running
    
    def test_cron_schedule_parsing(self):
        """Test cron schedule parsing."""
        scheduler = JobScheduler()
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test-job", "Test job", "0 * * * *", task)
        
        scheduler.add_job(job)
        assert "test-job" in scheduler.scheduled_jobs
    
    def test_one_time_schedule_parsing(self):
        """Test one-time schedule parsing."""
        scheduler = JobScheduler()
        task = ExecuteCommandTask("echo 'test'")
        # Schedule for future
        future_time = "2026-12-31T23:59:59Z"
        job = Job("test-job", "Test job", future_time, task)
        
        scheduler.add_job(job)
        assert "test-job" in scheduler.scheduled_jobs
    
    def test_past_one_time_schedule(self):
        """Test that past one-time schedules are rejected."""
        scheduler = JobScheduler()
        task = ExecuteCommandTask("echo 'test'")
        # Schedule in the past
        past_time = "2020-01-01T00:00:00Z"
        job = Job("test-job", "Test job", past_time, task)
        
        scheduler.add_job(job)
        # Should not be scheduled
        assert "test-job" not in scheduler.scheduled_jobs or "test-job" not in scheduler.jobs


class TestFileWatcher:
    """Test cases for JobFileWatcher."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test jobs."""
        test_dir = Path(tempfile.mkdtemp())
        yield test_dir
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_file_watcher_initialization(self, temp_dir):
        """Test file watcher can be initialized."""
        scheduler = JobScheduler()
        watcher = JobFileWatcher(str(temp_dir), scheduler)
        assert watcher.watch_directory == temp_dir
        assert not watcher.running
    
    def test_load_existing_jobs(self, temp_dir):
        """Test loading existing job files."""
        scheduler = JobScheduler()
        watcher = JobFileWatcher(str(temp_dir), scheduler)
        
        # Create a test job file
        job_file = temp_dir / "test-job.json"
        job_file.write_text("""{
  "job_id": "test-job",
  "description": "Test job",
  "schedule": "* * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'test'"
  }
}""")
        
        watcher._load_existing_jobs()
        assert "test-job" in scheduler.jobs
    
    def test_detect_new_file(self, temp_dir):
        """Test detecting new job files."""
        scheduler = JobScheduler()
        watcher = JobFileWatcher(str(temp_dir), scheduler)
        watcher.start()
        
        # Create a new job file
        job_file = temp_dir / "new-job.json"
        job_file.write_text("""{
  "job_id": "new-job",
  "description": "New job",
  "schedule": "* * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'new'"
  }
}""")
        
        # Wait for watcher to detect
        time.sleep(3)
        assert "new-job" in scheduler.jobs
        
        watcher.stop()
    
    def test_detect_deleted_file(self, temp_dir):
        """Test detecting deleted job files."""
        scheduler = JobScheduler()
        watcher = JobFileWatcher(str(temp_dir), scheduler)
        
        # Create and load a job
        job_file = temp_dir / "test-job.json"
        job_file.write_text("""{
  "job_id": "test-job",
  "description": "Test job",
  "schedule": "* * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'test'"
  }
}""")
        
        watcher._load_existing_jobs()
        assert "test-job" in scheduler.jobs
        
        # Delete the file
        job_file.unlink()
        
        watcher.start()
        time.sleep(3)
        watcher.stop()
        
        # Job should be removed
        assert "test-job" not in scheduler.jobs
