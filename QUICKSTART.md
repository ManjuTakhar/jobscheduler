# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Scheduler

```bash
# Run with example jobs
python -m job_scheduler.main --jobs-dir ./examples/jobs.d

# Run with custom directory
python -m job_scheduler.main --jobs-dir /path/to/your/jobs.d

# Run with debug logging
python -m job_scheduler.main --jobs-dir ./examples/jobs.d --log-level DEBUG
```

## Testing

Create a test job file in your jobs directory:

```json
{
  "job_id": "test-echo",
  "description": "Test job",
  "schedule": "* * * * *",
  "task": {
    "type": "execute_command",
    "command": "echo 'Hello from scheduler!'"
  }
}
```

This will run every minute. Watch the logs to see it execute.

## Key Features Demonstrated

1. **Dynamic Job Management**: Add/modify/delete JSON files in the jobs directory - no restart needed
2. **Cron Scheduling**: Use cron expressions like `*/5 * * * *` for recurring jobs
3. **One-Time Jobs**: Use ISO 8601 timestamps like `2025-12-25T00:00:00Z` for one-time execution
4. **Concurrent Execution**: Multiple jobs can run simultaneously
5. **Logging**: All executions are logged with job ID, timestamp, and status

## Example Schedules

- `0 1 * * *` - Daily at 1:00 AM
- `*/5 * * * *` - Every 5 minutes
- `0 */2 * * *` - Every 2 hours
- `2025-12-25T00:00:00Z` - One-time execution on Christmas 2025

