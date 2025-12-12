"""Tests for task executors."""
import pytest
from unittest.mock import patch, MagicMock

from job_scheduler.executors import TaskExecutorFactory, ExecuteCommandExecutor
from job_scheduler.models import ExecuteCommandTask


class TestExecuteCommandExecutor:
    """Test cases for ExecuteCommandExecutor."""
    
    def test_execute_success(self):
        """Test successful command execution."""
        executor = ExecuteCommandExecutor()
        task = ExecuteCommandTask("echo 'success'")
        
        success, stdout, stderr, exit_code = executor.execute(task)
        
        assert success is True
        assert exit_code == 0
        assert "success" in stdout or stdout == ""
    
    def test_execute_failure(self):
        """Test failed command execution."""
        executor = ExecuteCommandExecutor()
        task = ExecuteCommandTask("false")  # Command that always fails
        
        success, stdout, stderr, exit_code = executor.execute(task)
        
        assert success is False
        assert exit_code != 0
    
    def test_execute_timeout(self):
        """Test command timeout."""
        executor = ExecuteCommandExecutor()
        task = ExecuteCommandTask("sleep 10")
        
        with patch('job_scheduler.executors.task_executors.subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")
            
            success, stdout, stderr, exit_code = executor.execute(task)
            
            assert success is False
            assert exit_code == -1
    
    def test_execute_exception(self):
        """Test exception handling during execution."""
        executor = ExecuteCommandExecutor()
        task = ExecuteCommandTask("nonexistent_command_xyz")
        
        success, stdout, stderr, exit_code = executor.execute(task)
        
        # Should handle exception gracefully
        assert isinstance(success, bool)


class TestTaskExecutorFactory:
    """Test cases for TaskExecutorFactory."""
    
    def test_get_executor(self):
        """Test getting an executor for a task type."""
        executor = TaskExecutorFactory.get_executor("execute_command")
        assert isinstance(executor, ExecuteCommandExecutor)
    
    def test_get_invalid_executor(self):
        """Test getting executor for invalid task type."""
        with pytest.raises(ValueError):
            TaskExecutorFactory.get_executor("invalid_type")
    
    def test_register_executor(self):
        """Test registering a new executor."""
        mock_executor = MagicMock()
        TaskExecutorFactory.register_executor("test_type", mock_executor)
        
        executor = TaskExecutorFactory.get_executor("test_type")
        assert executor == mock_executor

