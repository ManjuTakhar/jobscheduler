"""Resource limiting and concurrency control."""
import threading
import logging
from typing import Optional
from collections import deque
from datetime import datetime, timezone

from .config import settings

logger = logging.getLogger(__name__)


class ResourceLimiter:
    """Manages resource limits for job execution."""
    
    def __init__(self):
        """Initialize resource limiter."""
        self.max_concurrent = settings.max_concurrent_jobs
        self.active_jobs = {}  # job_id -> execution_id
        self.lock = threading.Lock()
        self.semaphore = threading.Semaphore(self.max_concurrent)
    
    def acquire(self, job_id: str, execution_id: str) -> bool:
        """
        Acquire resources for a job execution.
        
        Args:
            job_id: Job ID
            execution_id: Execution ID
            
        Returns:
            True if resources were acquired, False if limit reached
        """
        acquired = self.semaphore.acquire(blocking=False)
        if acquired:
            with self.lock:
                self.active_jobs[job_id] = execution_id
                logger.debug(
                    f"Acquired resources for job {job_id} "
                    f"(active: {len(self.active_jobs)}/{self.max_concurrent})"
                )
        else:
            logger.warning(
                f"Resource limit reached: {len(self.active_jobs)}/{self.max_concurrent} "
                f"jobs running. Job {job_id} queued."
            )
        return acquired
    
    def release(self, job_id: str) -> None:
        """
        Release resources for a job execution.
        
        Args:
            job_id: Job ID
        """
        with self.lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
                self.semaphore.release()
                logger.debug(
                    f"Released resources for job {job_id} "
                    f"(active: {len(self.active_jobs)}/{self.max_concurrent})"
                )
    
    def get_active_count(self) -> int:
        """Get the number of currently active jobs."""
        with self.lock:
            return len(self.active_jobs)
    
    def get_active_jobs(self) -> dict:
        """Get a copy of active jobs."""
        with self.lock:
            return self.active_jobs.copy()

