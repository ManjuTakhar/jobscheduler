"""Job execution logic."""
import threading
import logging
from datetime import datetime, timezone
from uuid import uuid4

from job_scheduler.models import Job
from job_scheduler.executors import TaskExecutorFactory
from job_scheduler.logging import JobLogger, SchedulerLogger
from .scheduled_job import ScheduledJob

logger = logging.getLogger(__name__)


class JobExecutor:
    """Handles execution of scheduled jobs."""
    
    def __init__(self, job_logger: JobLogger, scheduler_logger: SchedulerLogger):
        """
        Initialize the job executor.
        
        Args:
            job_logger: Logger for job execution logs
            scheduler_logger: Logger for scheduler events
        """
        self.job_logger = job_logger
        self.scheduler_logger = scheduler_logger
    
    def execute(self, scheduled_job: ScheduledJob) -> None:
        """
        Execute a scheduled job in a separate thread.
        
        Args:
            scheduled_job: The scheduled job to execute
        """
        def run():
            job = scheduled_job.job
            execution_id = uuid4().hex
            start_time = datetime.now(timezone.utc)
            
            # Log to main logger
            logger.info(
                f"Job execution started - ID: {job.job_id}, "
                f"Execution ID: {execution_id}, Time: {start_time.isoformat()}"
            )
            
            # Get command string if it's an execute_command task
            command = ""
            if hasattr(job.task, 'command'):
                command = job.task.command
            
            # Execute the task
            executor = TaskExecutorFactory.get_executor(job.task.type)
            success, stdout, stderr, exit_code = executor.execute(job.task)
            end_time = datetime.now(timezone.utc)
            duration_seconds = (end_time - start_time).total_seconds()
            status = "SUCCESS" if success else "FAILURE"
            
            # Log to execution log file
            try:
                self.job_logger.log_execution(
                    job_id=job.job_id,
                    execution_id=execution_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration_seconds,
                    status=status,
                    command=command,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr
                )
            except Exception as e:
                logger.error(f"Failed to log execution to job log file for {job.job_id}: {e}", exc_info=True)
                self.scheduler_logger.log_error(job_id=job.job_id, error_msg=f"Failed to write execution log: {e}")
            
            # Log to main logger
            logger.info(
                f"Job execution completed - ID: {job.job_id}, "
                f"Execution ID: {execution_id}, Status: {status}"
            )
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

