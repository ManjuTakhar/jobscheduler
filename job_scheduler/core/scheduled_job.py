"""Scheduled job classes for different schedule types."""
from datetime import datetime, timezone
from typing import Any

from job_scheduler.models import Job


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

