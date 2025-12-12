"""Task executor implementations - extensible design."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import subprocess
import logging

logger = logging.getLogger(__name__)


class TaskExecutor(ABC):
    """Abstract base class for task executors."""
    
    @abstractmethod
    def execute(self, task: Any) -> Tuple[bool, str, str, int]:
        """
        Execute a task.
        
        Args:
            task: The task object to execute
            
        Returns:
            tuple: (success: bool, output: str, error: str, exit_code: int)
        """
        pass


class ExecuteCommandExecutor(TaskExecutor):
    """Executor for execute_command tasks."""
    
    def execute(self, task: Any) -> Tuple[bool, str, str, int]:
        """
        Execute a shell command.
        
        Args:
            task: ExecuteCommandTask instance
            
        Returns:
            tuple: (success: bool, output: str, error: str, exit_code: int)
        """
        try:
            logger.info(f"Executing command: {task.command}")
            result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            exit_code = result.returncode
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            
            if exit_code == 0:
                logger.info(f"Command succeeded: {task.command}")
                if stdout:
                    logger.debug(f"Command output: {stdout}")
                return True, stdout, "", exit_code
            else:
                error_msg = f"Command failed with exit code {exit_code}"
                logger.error(f"{error_msg}: {task.command}")
                if stderr:
                    logger.error(f"Command error: {stderr}")
                return False, stdout, stderr, exit_code
                
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out"
            logger.error(f"{error_msg}: {task.command}")
            return False, "", error_msg, -1
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(f"{error_msg}: {task.command}")
            return False, "", error_msg, -1


class TaskExecutorFactory:
    """Factory to get the appropriate executor for a task type."""
    
    _executors: Dict[str, TaskExecutor] = {
        'execute_command': ExecuteCommandExecutor(),
    }
    
    @classmethod
    def get_executor(cls, task_type: str) -> TaskExecutor:
        """
        Get the executor for a given task type.
        
        Args:
            task_type: The type of task (e.g., 'execute_command')
            
        Returns:
            TaskExecutor: The appropriate executor instance
            
        Raises:
            ValueError: If task type is not supported
        """
        executor = cls._executors.get(task_type)
        if executor is None:
            raise ValueError(f"Unsupported task type: {task_type}")
        return executor
    
    @classmethod
    def register_executor(cls, task_type: str, executor: TaskExecutor):
        """
        Register a new task executor type (for extensibility).
        
        Args:
            task_type: The task type identifier
            executor: The executor instance
        """
        cls._executors[task_type] = executor

