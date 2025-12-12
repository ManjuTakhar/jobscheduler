"""Core scheduler implementation."""
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from croniter import croniter
import logging
from uuid import uuid4

from .models import Job
from .task_executors import TaskExecutorFactory
from .job_logger import JobLogger
from .scheduler_logger import SchedulerLogger

logger = logging.getLogger(__name__)


class JobScheduler:
    """In-memory job scheduler supporting cron and one-time schedules."""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the job scheduler.
        
        Args:
            log_directory: Directory where job log files will be stored
        """
        self.jobs: Dict[str, Job] = {}
        self.scheduled_jobs: Dict[str, 'ScheduledJob'] = {}
        self.lock = threading.Lock()
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.job_logger = JobLogger(log_directory)
        self.scheduler_logger = SchedulerLogger(log_directory)
    
    def add_job(self, job: Job):
        """
        Add or update a job in the scheduler.
        
        Args:
            job: The job to add or update
        """
        with self.lock:
            is_new = job.job_id not in self.jobs
            old_schedule = self.jobs.get(job.job_id, Job("", "", "", None)).schedule if job.job_id in self.jobs else ""
            
            self.jobs[job.job_id] = job
            self._schedule_job(job)
            
            # Log to scheduler.log
            if is_new:
                self.scheduler_logger.log_add(job.job_id, job.schedule)
            else:
                # Check if schedule changed
                if old_schedule != job.schedule:
                    self.scheduler_logger.log_schedule_change(job.job_id, old_schedule, job.schedule)
                else:
                    self.scheduler_logger.log_update(job.job_id, job.schedule)
            
            logger.info(f"Job added/updated: {job.job_id}")
    
    def remove_job(self, job_id: str):
        """
        Remove a job from the scheduler.
        
        Args:
            job_id: The ID of the job to remove
        """
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
            if job_id in self.scheduled_jobs:
                self.scheduled_jobs[job_id].cancel()
                del self.scheduled_jobs[job_id]
            
            # Log deletion to scheduler.log
            self.scheduler_logger.log_delete(job_id)
            
            logger.info(f"Job removed: {job_id}")
    
    def _schedule_job(self, job: Job):
        """Schedule a job for execution."""
        # Cancel existing scheduled job if updating
        if job.job_id in self.scheduled_jobs:
            self.scheduled_jobs[job.job_id].cancel()
        
        if job.is_one_time_schedule():
            # Parse ISO 8601 timestamp
            try:
                schedule_str = job.schedule
                # Handle 'Z' timezone indicator (UTC)
                if schedule_str.endswith('Z'):
                    schedule_str = schedule_str[:-1] + '+00:00'
                # Parse the timestamp
                schedule_time = datetime.fromisoformat(schedule_str)
                if schedule_time.tzinfo is None:
                    schedule_time = schedule_time.replace(tzinfo=timezone.utc)
                
                # Check if the one-time job is in the past
                now = datetime.now(timezone.utc)
                if schedule_time <= now:
                    logger.warning(
                        f"One-time job {job.job_id} scheduled time is in the past, skipping"
                    )
                    return
                
                scheduled_job = OneTimeScheduledJob(job, schedule_time)
                
            except ValueError as e:
                error_msg = f"Invalid schedule format for job {job.job_id}: {e}"
                logger.error(error_msg)
                self.scheduler_logger.log_error(job_id=job.job_id, error_msg=error_msg)
                return
        else:
            # Cron schedule
            try:
                cron = croniter(job.schedule, datetime.now(timezone.utc))
                scheduled_job = RecurringScheduledJob(job, cron)
            except Exception as e:
                error_msg = f"Invalid cron expression for job {job.job_id}: {e}"
                logger.error(error_msg)
                self.scheduler_logger.log_error(job_id=job.job_id, error_msg=error_msg)
                return
        
        self.scheduled_jobs[job.job_id] = scheduled_job
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run, daemon=True)
        self.scheduler_thread.start()
        self.scheduler_logger.log_start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.scheduler_logger.log_stop()
        logger.info("Scheduler stopped")
    
    def _run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                with self.lock:
                    jobs_to_run = []
                    for scheduled_job in self.scheduled_jobs.values():
                        if scheduled_job.should_run():
                            jobs_to_run.append(scheduled_job)
                
                # Execute jobs that are due (outside the lock)
                for scheduled_job in jobs_to_run:
                    logger.debug(f"Executing job: {scheduled_job.job.job_id}")
                    self._execute_job(scheduled_job)
                    scheduled_job.mark_executed()
                    
                    # Reschedule recurring jobs
                    with self.lock:
                        if isinstance(scheduled_job, RecurringScheduledJob):
                            scheduled_job.reschedule()
                            logger.debug(
                                f"Rescheduled job {scheduled_job.job.job_id}, "
                                f"next run: {scheduled_job.next_run_time}"
                            )
                        elif isinstance(scheduled_job, OneTimeScheduledJob):
                            # Remove one-time jobs after execution
                            if scheduled_job.job.job_id in self.scheduled_jobs:
                                del self.scheduled_jobs[scheduled_job.job.job_id]
                                logger.info(f"Removed one-time job: {scheduled_job.job.job_id}")
            
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self.scheduler_logger.log_error(error_msg=str(e))
            
            time.sleep(1)  # Check every second
    
    def _execute_job(self, scheduled_job: 'ScheduledJob'):
        """Execute a job in a separate thread."""
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


class ScheduledJob:
    """Base class for scheduled job execution."""
    
    def __init__(self, job: Job):
        self.job = job
        self.cancelled = False
    
    def cancel(self):
        """Cancel this scheduled job."""
        self.cancelled = True
    
    def should_run(self) -> bool:
        """Check if the job should run now."""
        raise NotImplementedError
    
    def mark_executed(self):
        """Mark the job as executed."""
        pass


class OneTimeScheduledJob(ScheduledJob):
    """A job scheduled to run once at a specific time."""
    
    def __init__(self, job: Job, schedule_time: datetime):
        super().__init__(job)
        self.schedule_time = schedule_time
    
    def should_run(self) -> bool:
        """Check if the scheduled time has arrived."""
        if self.cancelled:
            return False
        now = datetime.now(timezone.utc)
        return now >= self.schedule_time


class RecurringScheduledJob(ScheduledJob):
    """A job scheduled to run repeatedly based on a cron expression."""
    
    def __init__(self, job: Job, cron: Any):
        super().__init__(job)
        self.cron = cron
        self.next_run_time = cron.get_next(datetime)
        self.last_check_time = datetime.now(timezone.utc)
    
    def should_run(self) -> bool:
        """Check if it's time to run based on cron schedule."""
        if self.cancelled:
            return False
        now = datetime.now(timezone.utc)
        return now >= self.next_run_time
    
    def mark_executed(self):
        """Update the last check time after execution."""
        self.last_check_time = datetime.now(timezone.utc)
    
    def reschedule(self):
        """Calculate the next run time."""
        self.next_run_time = self.cron.get_next(datetime)

