"""Job and Task models for the scheduler."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import json


@dataclass
class Task:
    """Base task class - extensible for different task types."""
    type: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Factory method to create task instances from JSON."""
        task_type = data.get('type')
        if task_type == 'execute_command':
            return ExecuteCommandTask.from_dict(data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")


@dataclass
class ExecuteCommandTask(Task):
    """Task that executes a shell command."""
    command: str
    
    def __init__(self, command: str):
        super().__init__(type='execute_command')
        self.command = command
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecuteCommandTask':
        if data.get('type') != 'execute_command':
            raise ValueError("Invalid task type for ExecuteCommandTask")
        command = data.get('command')
        if not command:
            raise ValueError("Command is required for execute_command task")
        return cls(command=command)


@dataclass
class Job:
    """Job definition with schedule and task."""
    job_id: str
    description: str
    schedule: str  # Can be cron string or ISO 8601 timestamp
    task: Task
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create a Job instance from a dictionary (parsed JSON)."""
        job_id = data.get('job_id')
        if not job_id:
            raise ValueError("job_id is required")
        
        description = data.get('description', '')
        schedule = data.get('schedule')
        if not schedule:
            raise ValueError("schedule is required")
        
        task_data = data.get('task')
        if not task_data:
            raise ValueError("task is required")
        
        task = Task.from_dict(task_data)
        
        return cls(
            job_id=job_id,
            description=description,
            schedule=schedule,
            task=task
        )
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'Job':
        """Load a job from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def is_cron_schedule(self) -> bool:
        """Check if schedule is a cron string (not ISO 8601 timestamp)."""
        # Simple heuristic: cron strings don't contain 'T' or 'Z'
        return 'T' not in self.schedule and 'Z' not in self.schedule
    
    def is_one_time_schedule(self) -> bool:
        """Check if schedule is a one-time ISO 8601 timestamp."""
        return not self.is_cron_schedule()

