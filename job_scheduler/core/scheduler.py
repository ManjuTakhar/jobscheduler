"""Core scheduler implementation."""
import threading
import time
from typing import Dict, Optional
import logging

from job_scheduler.models import Job
from job_scheduler.logging import JobLogger, SchedulerLogger
from .scheduled_job import ScheduledJob, OneTimeScheduledJob, RecurringScheduledJob
from .job_executor import JobExecutor
from .schedule_manager import ScheduleManager

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
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.lock = threading.Lock()
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.job_logger = JobLogger(log_directory)
        self.scheduler_logger = SchedulerLogger(log_directory)
        self.job_executor = JobExecutor(self.job_logger, self.scheduler_logger)
        self.schedule_manager = ScheduleManager(self.scheduler_logger)
    
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
        
        # Create scheduled job using schedule manager
        scheduled_job = self.schedule_manager.create_scheduled_job(job)
        if scheduled_job:
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
                    self.job_executor.execute(scheduled_job)
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

