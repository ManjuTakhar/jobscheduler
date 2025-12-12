"""Scheduler-level logging to logs/scheduler.log"""
import os
from pathlib import Path
from datetime import datetime, timezone


class SchedulerLogger:
    """Handles scheduler lifecycle and job management logs."""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the scheduler logger.
        
        Args:
            log_directory: Base directory for logs
        """
        self.log_directory = Path(log_directory).resolve()
        self.log_file = self.log_directory / "scheduler.log"
        # Ensure directory exists
        os.makedirs(self.log_directory, exist_ok=True)
    
    def _write_log(self, event_type: str, job_id: str = "", old_schedule: str = "", new_schedule: str = "", error_msg: str = ""):
        """
        Write a log entry to scheduler.log
        
        Format: [UTC_TIMESTAMP] EVENT_TYPE job_id=<id> old_schedule=<..> new_schedule=<..>
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        parts = [f"[{timestamp}]", event_type]
        
        if job_id:
            parts.append(f"job_id={job_id}")
        if old_schedule:
            parts.append(f"old_schedule={old_schedule}")
        if new_schedule:
            parts.append(f"new_schedule={new_schedule}")
        if error_msg:
            parts.append(f"error={error_msg}")
        
        log_line = " ".join(parts) + "\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            # Fallback to stderr if logging fails
            import sys
            print(f"ERROR: Failed to write to scheduler.log: {e}", file=sys.stderr)
    
    def log_add(self, job_id: str, schedule: str):
        """Log job addition."""
        self._write_log("ADD", job_id=job_id, new_schedule=schedule)
    
    def log_update(self, job_id: str, schedule: str):
        """Log job update."""
        self._write_log("UPDATE", job_id=job_id, new_schedule=schedule)
    
    def log_delete(self, job_id: str):
        """Log job deletion."""
        self._write_log("DELETE", job_id=job_id)
    
    def log_schedule_change(self, job_id: str, old_schedule: str, new_schedule: str):
        """Log schedule change."""
        self._write_log("SCHEDULE_CHANGE", job_id=job_id, old_schedule=old_schedule, new_schedule=new_schedule)
    
    def log_start(self):
        """Log scheduler start."""
        self._write_log("START")
    
    def log_stop(self):
        """Log scheduler stop."""
        self._write_log("STOP")
    
    def log_error(self, job_id: str = "", error_msg: str = ""):
        """Log error."""
        self._write_log("ERROR", job_id=job_id, error_msg=error_msg)

