"""Job-specific logging functionality."""
import logging
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone
from uuid import uuid4


class JobLogger:
    """Manages per-job log files."""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the job logger.
        
        Args:
            log_directory: Directory where job log files will be stored
        """
        # Convert to absolute path to avoid issues with relative paths
        self.log_directory = Path(log_directory).resolve()
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Log initialization for debugging
        import logging as std_logging
        std_logger = std_logging.getLogger(__name__)
        std_logger.info(f"JobLogger initialized with log directory: {self.log_directory}")
    
    def log_execution(self, job_id: str, execution_id: str, start_time: datetime, 
                     end_time: datetime, duration_seconds: float, status: str,
                     command: str = "", exit_code: int = 0, stdout: str = "", stderr: str = ""):
        """
        Log a job execution to logs/<job_id>/<execution_id>.log
        
        Args:
            job_id: The job ID
            execution_id: Unique execution ID (uuid4().hex)
            start_time: When execution started (ISO8601 UTC)
            end_time: When execution ended (ISO8601 UTC)
            duration_seconds: Execution duration in seconds
            status: SUCCESS or FAILURE
            command: Command that was executed
            exit_code: Exit code from command
            stdout: Standard output
            stderr: Standard error
        """
        try:
            # Create job-specific directory
            job_log_dir = self.log_directory / job_id
            os.makedirs(job_log_dir, exist_ok=True)
            
            # Create execution log file
            log_file = job_log_dir / f"{execution_id}.log"
            
            # Write execution log with required format
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"execution_id: {execution_id}\n")
                f.write(f"job_id: {job_id}\n")
                f.write(f"command: {command}\n")
                f.write(f"start_time: {start_time.isoformat()}\n")
                f.write(f"end_time: {end_time.isoformat()}\n")
                f.write(f"duration_seconds: {duration_seconds}\n")
                f.write(f"status: {status}\n")
                f.write(f"exit_code: {exit_code}\n")
                f.write("stdout:\n")
                f.write(stdout)
                if stdout and not stdout.endswith('\n'):
                    f.write('\n')
                f.write("stderr:\n")
                f.write(stderr)
                if stderr and not stderr.endswith('\n'):
                    f.write('\n')
            
        except Exception as e:
            # Fallback to main logger if job logger fails
            import logging
            main_logger = logging.getLogger(__name__)
            main_logger.error(f"Failed to write execution log file for {job_id}: {e}", exc_info=True)
            import sys
            print(f"ERROR: Failed to write execution log for job {job_id}: {e}", file=sys.stderr)
    

