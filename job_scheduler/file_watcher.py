"""File system watcher for dynamic job management."""
import os
import time
import threading
from pathlib import Path
from typing import Dict, Optional
import logging

from .models import Job
from .scheduler import JobScheduler

logger = logging.getLogger(__name__)


class JobFileWatcher:
    """Monitors a directory for job definition files and updates the scheduler."""
    
    def __init__(self, watch_directory: str, scheduler: JobScheduler):
        """
        Initialize the file watcher.
        
        Args:
            watch_directory: Path to directory containing job JSON files
            scheduler: The JobScheduler instance to update
        """
        self.watch_directory = Path(watch_directory)
        self.scheduler = scheduler
        self.running = False
        self.watcher_thread: Optional[threading.Thread] = None
        self.file_timestamps: Dict[str, float] = {}
        self.file_to_job_id: Dict[str, str] = {}  # Track file path -> job_id mapping
    
    def start(self):
        """Start watching the directory."""
        if self.running:
            logger.warning("File watcher is already running")
            return
        
        # Ensure directory exists
        self.watch_directory.mkdir(parents=True, exist_ok=True)
        
        # Load existing jobs on startup
        self._load_existing_jobs()
        
        self.running = True
        self.watcher_thread = threading.Thread(target=self._watch, daemon=True)
        self.watcher_thread.start()
        logger.info(f"File watcher started for directory: {self.watch_directory}")
    
    def stop(self):
        """Stop watching the directory."""
        self.running = False
        if self.watcher_thread:
            self.watcher_thread.join(timeout=5)
        logger.info("File watcher stopped")
    
    def _load_existing_jobs(self):
        """Load all existing job files on startup."""
        if not self.watch_directory.exists():
            logger.warning(f"Watch directory does not exist: {self.watch_directory}")
            return
        
        json_files = list(self.watch_directory.glob("*.json"))
        logger.info(f"Loading {len(json_files)} existing job files")
        
        for json_file in json_files:
            try:
                job = Job.from_json_file(str(json_file))
                self.scheduler.add_job(job)
                file_path = str(json_file)
                self.file_timestamps[file_path] = json_file.stat().st_mtime
                self.file_to_job_id[file_path] = job.job_id
            except Exception as e:
                error_msg = f"Error loading job file {json_file}: {e}"
                logger.error(error_msg)
                # Log to scheduler.log via scheduler's logger
                self.scheduler.scheduler_logger.log_error(error_msg=error_msg)
    
    def _watch(self):
        """Main watch loop - checks for file changes periodically."""
        while self.running:
            try:
                if not self.watch_directory.exists():
                    time.sleep(5)
                    continue
                
                # Get current JSON files
                current_files = {
                    str(f): f.stat().st_mtime
                    for f in self.watch_directory.glob("*.json")
                }
                
                # Check for new or modified files
                for file_path, mtime in current_files.items():
                    if file_path not in self.file_timestamps:
                        # New file
                        self._handle_new_file(file_path)
                        self.file_timestamps[file_path] = mtime
                    elif self.file_timestamps[file_path] != mtime:
                        # Modified file
                        self._handle_modified_file(file_path)
                        self.file_timestamps[file_path] = mtime
                
                # Check for deleted files
                deleted_files = set(self.file_timestamps.keys()) - set(current_files.keys())
                for file_path in deleted_files:
                    self._handle_deleted_file(file_path)
                    del self.file_timestamps[file_path]
            
            except Exception as e:
                error_msg = f"Error in file watcher loop: {e}"
                logger.error(error_msg)
                self.scheduler.scheduler_logger.log_error(error_msg=error_msg)
            
            time.sleep(2)  # Check every 2 seconds
    
    def _handle_new_file(self, file_path: str):
        """Handle a newly added job file."""
        try:
            logger.info(f"New job file detected: {file_path}")
            job = Job.from_json_file(file_path)
            self.scheduler.add_job(job)
            self.file_to_job_id[file_path] = job.job_id
        except Exception as e:
            error_msg = f"Error processing new job file {file_path}: {e}"
            logger.error(error_msg)
            self.scheduler.scheduler_logger.log_error(error_msg=error_msg)
    
    def _handle_modified_file(self, file_path: str):
        """Handle a modified job file."""
        try:
            logger.info(f"Job file modified: {file_path}")
            job = Job.from_json_file(file_path)
            # If job_id changed, remove old job
            if file_path in self.file_to_job_id:
                old_job_id = self.file_to_job_id[file_path]
                if old_job_id != job.job_id:
                    self.scheduler.remove_job(old_job_id)
            self.scheduler.add_job(job)  # add_job handles updates
            self.file_to_job_id[file_path] = job.job_id
        except Exception as e:
            error_msg = f"Error processing modified job file {file_path}: {e}"
            logger.error(error_msg)
            self.scheduler.scheduler_logger.log_error(error_msg=error_msg)
    
    def _handle_deleted_file(self, file_path: str):
        """Handle a deleted job file."""
        try:
            logger.info(f"Job file deleted: {file_path}")
            if file_path in self.file_to_job_id:
                job_id = self.file_to_job_id[file_path]
                self.scheduler.remove_job(job_id)
                del self.file_to_job_id[file_path]
            else:
                logger.warning(f"Could not determine job_id for deleted file: {file_path}")
        except Exception as e:
            error_msg = f"Error processing deleted job file {file_path}: {e}"
            logger.error(error_msg)
            self.scheduler.scheduler_logger.log_error(error_msg=error_msg)

