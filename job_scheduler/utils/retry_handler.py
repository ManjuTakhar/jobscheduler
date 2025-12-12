"""Retry mechanism for failed job executions."""
import time
import logging
from datetime import datetime, timezone
from typing import Optional
from threading import Lock

from .config import settings
from job_scheduler.models import Job
from job_scheduler.executors import TaskExecutorFactory

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retry logic for failed job executions."""
    
    def __init__(self):
        """Initialize retry handler."""
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self.retry_queue = []  # List of (job, execution_id, retry_count, error) tuples
        self.lock = Lock()
    
    def should_retry(self, retry_count: int, exit_code: Optional[int] = None) -> bool:
        """
        Determine if a job should be retried.
        
        Args:
            retry_count: Current retry count
            exit_code: Exit code from the failed execution
            
        Returns:
            True if job should be retried
        """
        if retry_count >= self.max_retries:
            return False
        
        # Don't retry on certain exit codes (e.g., permission denied)
        non_retryable_codes = [126, 127]  # Command not executable, command not found
        if exit_code in non_retryable_codes:
            return False
        
        return True
    
    def schedule_retry(
        self,
        job: Job,
        execution_id: str,
        retry_count: int,
        error_message: str
    ) -> None:
        """
        Schedule a job for retry.
        
        Args:
            job: The job to retry
            execution_id: Original execution ID
            retry_count: Current retry count
            error_message: Error message from failed execution
        """
        with self.lock:
            self.retry_queue.append((job, execution_id, retry_count, error_message))
            logger.info(
                f"Scheduled retry {retry_count + 1}/{self.max_retries} for job {job.job_id} "
                f"(execution {execution_id})"
            )
    
    def get_pending_retries(self) -> list:
        """Get all pending retries that are ready to execute."""
        with self.lock:
            ready_retries = []
            remaining_retries = []
            
            for job, execution_id, retry_count, error_message in self.retry_queue:
                # Simple retry delay: wait for retry_delay seconds
                # In a more sophisticated implementation, we'd track when each retry was scheduled
                ready_retries.append((job, execution_id, retry_count, error_message))
            
            self.retry_queue = remaining_retries
            return ready_retries
    
    def execute_retry(
        self,
        job: Job,
        original_execution_id: str,
        retry_count: int
    ) -> tuple[bool, str, str, int]:
        """
        Execute a retry attempt.
        
        Args:
            job: The job to retry
            original_execution_id: Original execution ID
            retry_count: Current retry count
            
        Returns:
            Tuple of (success, stdout, stderr, exit_code)
        """
        logger.info(
            f"Executing retry {retry_count + 1}/{self.max_retries} for job {job.job_id} "
            f"(original execution: {original_execution_id})"
        )
        
        # Wait before retrying (exponential backoff)
        delay = self.retry_delay * (2 ** retry_count)
        time.sleep(min(delay, 3600))  # Cap at 1 hour
        
        # Execute the task
        executor = TaskExecutorFactory.get_executor(job.task.type)
        return executor.execute(job.task)
    
    def clear_retries_for_job(self, job_id: str) -> None:
        """Clear all pending retries for a specific job."""
        with self.lock:
            self.retry_queue = [
                (job, exec_id, count, error)
                for job, exec_id, count, error in self.retry_queue
                if job.job_id != job_id
            ]

