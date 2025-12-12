"""Comprehensive tests for file watcher."""
import time
import tempfile
import shutil
from pathlib import Path
import pytest
import json

from job_scheduler.core import JobScheduler
from job_scheduler.watchers import JobFileWatcher
from job_scheduler.models import Job


class TestJobFileWatcher:
    """Test cases for JobFileWatcher."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test jobs."""
        test_dir = Path(tempfile.mkdtemp())
        yield test_dir
        shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance."""
        return JobScheduler()
    
    @pytest.fixture
    def watcher(self, temp_dir, scheduler):
        """Create a file watcher instance."""
        return JobFileWatcher(str(temp_dir), scheduler)
    
    def test_watcher_initialization(self, temp_dir, scheduler):
        """Test file watcher can be initialized."""
        watcher = JobFileWatcher(str(temp_dir), scheduler)
        assert watcher.watch_directory == temp_dir
        assert watcher.scheduler == scheduler
        assert not watcher.running
        assert len(watcher.file_timestamps) == 0
        assert len(watcher.file_to_job_id) == 0
    
    def test_watcher_start_stop(self, watcher):
        """Test starting and stopping the watcher."""
        watcher.start()
        assert watcher.running
        assert watcher.watcher_thread is not None
        
        time.sleep(0.1)  # Give it a moment
        watcher.stop()
        assert not watcher.running
    
    def test_load_existing_jobs(self, temp_dir, watcher):
        """Test loading existing job files on startup."""
        # Create multiple job files
        job1 = temp_dir / "job1.json"
        job1.write_text(json.dumps({
            "job_id": "job-1",
            "description": "Job 1",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'job1'"
            }
        }))
        
        job2 = temp_dir / "job2.json"
        job2.write_text(json.dumps({
            "job_id": "job-2",
            "description": "Job 2",
            "schedule": "0 * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'job2'"
            }
        }))
        
        watcher._load_existing_jobs()
        
        assert "job-1" in watcher.scheduler.jobs
        assert "job-2" in watcher.scheduler.jobs
        assert str(job1) in watcher.file_timestamps
        assert str(job2) in watcher.file_timestamps
        assert watcher.file_to_job_id[str(job1)] == "job-1"
        assert watcher.file_to_job_id[str(job2)] == "job-2"
    
    def test_load_invalid_job_file(self, temp_dir, watcher):
        """Test handling invalid job files."""
        invalid_job = temp_dir / "invalid.json"
        invalid_job.write_text("invalid json content")
        
        # Should not raise exception, but log error
        watcher._load_existing_jobs()
        assert "invalid.json" not in [f.name for f in temp_dir.glob("*.json") if f.name == "invalid.json"] or "invalid" not in watcher.scheduler.jobs
    
    def test_detect_new_file(self, temp_dir, watcher):
        """Test detecting newly added job files."""
        watcher.start()
        
        # Create a new job file after watcher started
        new_job = temp_dir / "new-job.json"
        new_job.write_text(json.dumps({
            "job_id": "new-job",
            "description": "New job",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'new'"
            }
        }))
        
        # Wait for watcher to detect (check interval is 2 seconds)
        time.sleep(3)
        
        assert "new-job" in watcher.scheduler.jobs
        assert str(new_job) in watcher.file_timestamps
        assert watcher.file_to_job_id[str(new_job)] == "new-job"
        
        watcher.stop()
    
    def test_detect_modified_file(self, temp_dir, watcher):
        """Test detecting modified job files."""
        # Create initial job
        job_file = temp_dir / "modify-job.json"
        job_file.write_text(json.dumps({
            "job_id": "modify-job",
            "description": "Original",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'original'"
            }
        }))
        
        watcher._load_existing_jobs()
        assert watcher.scheduler.jobs["modify-job"].description == "Original"
        
        watcher.start()
        
        # Modify the job file
        time.sleep(0.5)  # Small delay to ensure different mtime
        job_file.write_text(json.dumps({
            "job_id": "modify-job",
            "description": "Modified",
            "schedule": "0 * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'modified'"
            }
        }))
        
        # Wait for watcher to detect
        time.sleep(3)
        
        assert watcher.scheduler.jobs["modify-job"].description == "Modified"
        assert watcher.scheduler.jobs["modify-job"].schedule == "0 * * * *"
        
        watcher.stop()
    
    def test_detect_deleted_file(self, temp_dir, watcher):
        """Test detecting deleted job files."""
        # Create and load a job
        job_file = temp_dir / "delete-job.json"
        job_file.write_text(json.dumps({
            "job_id": "delete-job",
            "description": "To be deleted",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'delete'"
            }
        }))
        
        watcher._load_existing_jobs()
        assert "delete-job" in watcher.scheduler.jobs
        
        watcher.start()
        
        # Delete the file
        job_file.unlink()
        
        # Wait for watcher to detect
        time.sleep(3)
        
        assert "delete-job" not in watcher.scheduler.jobs
        assert str(job_file) not in watcher.file_timestamps
        assert str(job_file) not in watcher.file_to_job_id
        
        watcher.stop()
    
    def test_job_id_change_on_modify(self, temp_dir, watcher):
        """Test handling job_id change in modified file."""
        # Create initial job
        job_file = temp_dir / "change-id.json"
        job_file.write_text(json.dumps({
            "job_id": "old-id",
            "description": "Old job",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'old'"
            }
        }))
        
        watcher._load_existing_jobs()
        assert "old-id" in watcher.scheduler.jobs
        
        watcher.start()
        
        # Change job_id
        time.sleep(0.5)
        job_file.write_text(json.dumps({
            "job_id": "new-id",
            "description": "New job",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'new'"
            }
        }))
        
        # Wait for watcher to detect
        time.sleep(3)
        
        # Old job should be removed, new job added
        assert "old-id" not in watcher.scheduler.jobs
        assert "new-id" in watcher.scheduler.jobs
        assert watcher.file_to_job_id[str(job_file)] == "new-id"
        
        watcher.stop()
    
    def test_multiple_files_simultaneous(self, temp_dir, watcher):
        """Test handling multiple files added simultaneously."""
        watcher.start()
        
        # Create multiple job files at once
        for i in range(3):
            job_file = temp_dir / f"multi-job-{i}.json"
            job_file.write_text(json.dumps({
                "job_id": f"multi-{i}",
                "description": f"Multi job {i}",
                "schedule": "* * * * *",
                "task": {
                    "type": "execute_command",
                    "command": f"echo 'multi{i}'"
                }
            }))
        
        # Wait for watcher to detect
        time.sleep(3)
        
        for i in range(3):
            assert f"multi-{i}" in watcher.scheduler.jobs
        
        watcher.stop()
    
    def test_nonexistent_directory(self):
        """Test watcher with nonexistent directory."""
        scheduler = JobScheduler()
        nonexistent_dir = Path(tempfile.mkdtemp()) / "nonexistent"
        watcher = JobFileWatcher(str(nonexistent_dir), scheduler)
        
        # Should create directory on start
        watcher.start()
        assert nonexistent_dir.exists()
        
        watcher.stop()
        shutil.rmtree(nonexistent_dir.parent, ignore_errors=True)
    
    def test_empty_directory(self, temp_dir, watcher):
        """Test watcher with empty directory."""
        watcher._load_existing_jobs()
        assert len(watcher.scheduler.jobs) == 0
        assert len(watcher.file_timestamps) == 0
    
    def test_malformed_json_file(self, temp_dir, watcher):
        """Test handling malformed JSON files."""
        malformed = temp_dir / "malformed.json"
        malformed.write_text("{ invalid json }")
        
        watcher._load_existing_jobs()
        # Should not crash, job should not be loaded
        assert "malformed" not in watcher.scheduler.jobs
    
    def test_missing_required_fields(self, temp_dir, watcher):
        """Test handling job files with missing required fields."""
        incomplete = temp_dir / "incomplete.json"
        incomplete.write_text(json.dumps({
            "description": "Missing job_id and schedule",
            "task": {
                "type": "execute_command",
                "command": "echo 'test'"
            }
        }))
        
        watcher._load_existing_jobs()
        # Should not crash, job should not be loaded
        assert len([j for j in watcher.scheduler.jobs.values() if j.description == "Missing job_id and schedule"]) == 0
    
    def test_file_watcher_cleanup_on_stop(self, temp_dir, watcher):
        """Test that watcher cleans up properly on stop."""
        watcher.start()
        assert watcher.running
        
        watcher.stop()
        assert not watcher.running
        # Thread should be stopped
        if watcher.watcher_thread:
            assert not watcher.watcher_thread.is_alive()
    
    def test_concurrent_file_operations(self, temp_dir, watcher):
        """Test watcher handling concurrent file operations."""
        watcher.start()
        
        # Rapidly add, modify, and delete files
        job_file = temp_dir / "concurrent.json"
        job_file.write_text(json.dumps({
            "job_id": "concurrent",
            "description": "Concurrent test",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'concurrent'"
            }
        }))
        
        time.sleep(1)
        
        # Modify
        job_file.write_text(json.dumps({
            "job_id": "concurrent",
            "description": "Modified concurrent",
            "schedule": "0 * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'modified'"
            }
        }))
        
        time.sleep(1)
        
        # Delete
        job_file.unlink()
        
        # Wait for all operations to be processed
        time.sleep(3)
        
        assert "concurrent" not in watcher.scheduler.jobs
        
        watcher.stop()
    
    def test_special_characters_in_job_id(self, temp_dir, watcher):
        """Test handling special characters in job IDs."""
        job_file = temp_dir / "special-job.json"
        job_file.write_text(json.dumps({
            "job_id": "job-with-special-chars_123",
            "description": "Special chars",
            "schedule": "* * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'special'"
            }
        }))
        
        watcher._load_existing_jobs()
        assert "job-with-special-chars_123" in watcher.scheduler.jobs
    
    def test_one_time_schedule_file(self, temp_dir, watcher):
        """Test loading job file with one-time schedule."""
        job_file = temp_dir / "onetime.json"
        job_file.write_text(json.dumps({
            "job_id": "onetime-job",
            "description": "One-time job",
            "schedule": "2026-12-31T23:59:59Z",
            "task": {
                "type": "execute_command",
                "command": "echo 'onetime'"
            }
        }))
        
        watcher._load_existing_jobs()
        assert "onetime-job" in watcher.scheduler.jobs
        job = watcher.scheduler.jobs["onetime-job"]
        assert job.is_one_time_schedule()

