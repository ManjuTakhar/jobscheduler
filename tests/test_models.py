"""Tests for data models."""
import pytest
from datetime import datetime

from job_scheduler.models import Job, Task, ExecuteCommandTask


class TestTask:
    """Test cases for Task models."""
    
    def test_execute_command_task_creation(self):
        """Test creating an ExecuteCommandTask."""
        task = ExecuteCommandTask("echo 'test'")
        assert task.type == "execute_command"
        assert task.command == "echo 'test'"
    
    def test_task_from_dict(self):
        """Test creating a task from dictionary."""
        task_data = {
            "type": "execute_command",
            "command": "echo 'test'"
        }
        task = Task.from_dict(task_data)
        assert isinstance(task, ExecuteCommandTask)
        assert task.command == "echo 'test'"
    
    def test_invalid_task_type(self):
        """Test that invalid task type raises error."""
        task_data = {
            "type": "invalid_type",
            "command": "echo 'test'"
        }
        with pytest.raises(ValueError):
            Task.from_dict(task_data)


class TestJob:
    """Test cases for Job model."""
    
    def test_job_creation(self):
        """Test creating a job."""
        task = ExecuteCommandTask("echo 'test'")
        job = Job("test-job", "Test job", "0 * * * *", task)
        
        assert job.job_id == "test-job"
        assert job.description == "Test job"
        assert job.schedule == "0 * * * *"
        assert job.task == task
    
    def test_job_from_dict(self):
        """Test creating a job from dictionary."""
        job_data = {
            "job_id": "test-job",
            "description": "Test job",
            "schedule": "0 * * * *",
            "task": {
                "type": "execute_command",
                "command": "echo 'test'"
            }
        }
        job = Job.from_dict(job_data)
        
        assert job.job_id == "test-job"
        assert job.description == "Test job"
        assert isinstance(job.task, ExecuteCommandTask)
    
    def test_job_from_json_file(self, tmp_path):
        """Test loading a job from JSON file."""
        job_file = tmp_path / "test-job.json"
        job_file.write_text("""{
  "job_id": "test-job",
  "description": "Test job",
  "schedule": "0 * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'test'"
  }
}""")
        
        job = Job.from_json_file(str(job_file))
        assert job.job_id == "test-job"
        assert isinstance(job.task, ExecuteCommandTask)
    
    def test_job_missing_required_fields(self):
        """Test that missing required fields raise errors."""
        # Missing job_id
        with pytest.raises(ValueError):
            Job.from_dict({
                "description": "Test",
                "schedule": "0 * * * *",
                "task": {"type": "execute_command", "command": "echo"}
            })
        
        # Missing schedule
        with pytest.raises(ValueError):
            Job.from_dict({
                "job_id": "test",
                "description": "Test",
                "task": {"type": "execute_command", "command": "echo"}
            })
        
        # Missing task
        with pytest.raises(ValueError):
            Job.from_dict({
                "job_id": "test",
                "description": "Test",
                "schedule": "0 * * * *"
            })
    
    def test_is_cron_schedule(self):
        """Test cron schedule detection."""
        task = ExecuteCommandTask("echo 'test'")
        cron_job = Job("test", "", "0 * * * *", task)
        assert cron_job.is_cron_schedule()
        assert not cron_job.is_one_time_schedule()
    
    def test_is_one_time_schedule(self):
        """Test one-time schedule detection."""
        task = ExecuteCommandTask("echo 'test'")
        one_time_job = Job("test", "", "2025-12-31T23:59:59Z", task)
        assert one_time_job.is_one_time_schedule()
        assert not one_time_job.is_cron_schedule()

