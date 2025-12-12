"""Schedule management and job scheduling logic."""
from datetime import datetime, timezone
from croniter import croniter
import logging
from typing import Optional

from job_scheduler.models import Job
from .scheduled_job import ScheduledJob, OneTimeScheduledJob, RecurringScheduledJob
from job_scheduler.logging import SchedulerLogger

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Manages scheduling of jobs."""
    
    def __init__(self, scheduler_logger: SchedulerLogger):
        """
        Initialize the schedule manager.
        
        Args:
            scheduler_logger: Logger for scheduler events
        """
        self.scheduler_logger = scheduler_logger
    
    def create_scheduled_job(self, job: Job) -> Optional[ScheduledJob]:
        """
        Create a scheduled job from a job definition.
        
        Args:
            job: The job to schedule
            
        Returns:
            ScheduledJob instance or None if scheduling failed
        """
        if job.is_one_time_schedule():
            return self._create_one_time_job(job)
        else:
            return self._create_recurring_job(job)
    
    def _create_one_time_job(self, job: Job) -> Optional[ScheduledJob]:
        """
        Create a one-time scheduled job.
        
        Args:
            job: The job to schedule
            
        Returns:
            OneTimeScheduledJob instance or None if scheduling failed
        """
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
                return None
            
            return OneTimeScheduledJob(job, schedule_time)
            
        except ValueError as e:
            error_msg = f"Invalid schedule format for job {job.job_id}: {e}"
            logger.error(error_msg)
            self.scheduler_logger.log_error(job_id=job.job_id, error_msg=error_msg)
            return None
    
    def _create_recurring_job(self, job: Job) -> Optional[ScheduledJob]:
        """
        Create a recurring scheduled job.
        
        Args:
            job: The job to schedule
            
        Returns:
            RecurringScheduledJob instance or None if scheduling failed
        """
        try:
            cron = croniter(job.schedule, datetime.now(timezone.utc))
            return RecurringScheduledJob(job, cron)
        except Exception as e:
            error_msg = f"Invalid cron expression for job {job.job_id}: {e}"
            logger.error(error_msg)
            self.scheduler_logger.log_error(job_id=job.job_id, error_msg=error_msg)
            return None

