#!/usr/bin/env python3
"""Simple test script to verify the scheduler works."""
import time
import tempfile
import shutil
from pathlib import Path
from job_scheduler.scheduler import JobScheduler
from job_scheduler.file_watcher import JobFileWatcher
from job_scheduler.models import Job

def test_basic_functionality():
    """Test basic scheduler functionality."""
    print("Testing Job Scheduler...")
    
    # Create a temporary directory for test jobs
    test_dir = Path(tempfile.mkdtemp())
    print(f"Using test directory: {test_dir}")
    
    try:
        # Create scheduler and watcher
        scheduler = JobScheduler()
        watcher = JobFileWatcher(str(test_dir), scheduler)
        
        # Start services
        scheduler.start()
        watcher.start()
        
        # Create a test job file that runs every minute
        test_job_file = test_dir / "test-job.json"
        test_job_file.write_text("""{
  "job_id": "test-job",
  "description": "Test job that runs every minute",
  "schedule": "* * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'Test job executed'"
  }
}""")
        
        print("Created test job file. Waiting for scheduler to pick it up...")
        time.sleep(3)
        
        # Check if job was loaded
        if "test-job" in scheduler.jobs:
            print("✓ Job loaded successfully")
        else:
            print("✗ Job not loaded")
        
        # Wait a bit to see if it executes
        print("Waiting 65 seconds to see job execution...")
        time.sleep(65)
        
        # Cleanup
        scheduler.stop()
        watcher.stop()
        print("Test completed!")
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_basic_functionality()

