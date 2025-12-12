# Job Scheduler

A lightweight, in-memory job scheduling service that monitors a directory for job definition files and executes them according to their schedules.

## Features

- **Dynamic Job Management**: Automatically detects new, modified, and deleted job files without requiring service restart
- **Flexible Scheduling**: Supports both cron expressions (recurring) and ISO 8601 timestamps (one-time)
- **Extensible Task System**: Easy to add new task types without modifying core scheduling logic
- **Concurrent Execution**: Runs multiple jobs concurrently when schedules overlap
- **Comprehensive Logging**: Logs all job executions with job ID, execution time, and status

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Install as a package:
```bash
pip install -e .
```

## Usage

### Basic Usage

Start the scheduler with the default jobs directory (`/etc/chronoflow/jobs.d`):

```bash
python -m job_scheduler.main
```

Or specify a custom jobs directory:

```bash
python -m job_scheduler.main --jobs-dir /path/to/jobs.d
```

### Command Line Options

- `--jobs-dir`: Directory containing job definition files (default: `/etc/chronoflow/jobs.d`)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, or ERROR (default: INFO)

### Example

```bash
python -m job_scheduler.main --jobs-dir ./examples/jobs.d --log-level INFO
```

## Job Definition Format

Jobs are defined as JSON files in the watched directory. Each job file must contain:

- `job_id` (required): Unique identifier for the job
- `description` (optional): Human-readable description
- `schedule` (required): Either a cron expression or ISO 8601 timestamp
- `task` (required): Task definition object

### Task Types

#### execute_command

Executes a shell command:

```json
{
  "type": "execute_command",
  "command": "/usr/bin/python /opt/scripts/generate_sales_report.py"
}
```

### Schedule Formats

#### Cron Expression (Recurring)

Use standard cron syntax for recurring jobs:

```json
{
  "schedule": "0 1 * * *"
}
```

This runs daily at 1:00 AM.

#### ISO 8601 Timestamp (One-Time)

Use ISO 8601 format for one-time jobs:

```json
{
  "schedule": "2025-09-20T02:00:00Z"
}
```

This runs once at the specified time (UTC).

## Example Job Files

See the `examples/jobs.d/` directory for example job definitions:

- `daily-report.json`: Daily recurring report generation
- `onetime-cleanup.json`: One-time cleanup task
- `frequent-task.json`: Task that runs every 5 minutes

## Architecture

### Project Structure

The project is organized into modular components:

```
job_scheduler/
├── core/                    # Core scheduling components
│   ├── scheduler.py         # Main JobScheduler class
│   ├── scheduled_job.py     # ScheduledJob base and implementations
│   ├── job_executor.py      # Job execution logic
│   └── schedule_manager.py  # Schedule parsing and creation
├── models/                  # Data models
│   ├── job_models.py        # Job and Task models
│   └── db_models.py         # Database models
├── database/                # Database components
│   ├── db_session.py        # Database session management
│   └── persistence.py       # Persistence layer
├── executors/               # Task executors
│   └── task_executors.py    # Task execution implementations
├── watchers/                # File watchers
│   └── file_watcher.py      # Job file watcher
├── logging/                 # Logging components
│   ├── job_logger.py        # Job execution logging
│   └── scheduler_logger.py  # Scheduler event logging
├── utils/                   # Utility components
│   ├── config.py            # Configuration management
│   ├── retry_handler.py    # Retry mechanism
│   ├── resource_limiter.py # Resource management
│   └── metrics.py           # Metrics collection
├── main.py                  # Application entry point
└── __init__.py              # Package exports
```

### Components

1. **JobScheduler** (`core/scheduler.py`): Core scheduling engine that manages job execution
2. **JobFileWatcher** (`watchers/file_watcher.py`): Monitors the jobs directory for file changes
3. **TaskExecutor** (`executors/task_executors.py`): Extensible system for executing different task types
4. **Models** (`models/`): Job and Task data structures
5. **Database** (`database/`): Persistence layer for jobs and executions
6. **Logging** (`logging/`): Structured logging for jobs and scheduler events
7. **Utils** (`utils/`): Configuration, retry handling, resource management, and metrics

### Extensibility

To add a new task type:

1. Create a new task class in `models/job_models.py` (e.g., `HttpRequestTask`)
2. Create a corresponding executor in `executors/task_executors.py` (e.g., `HttpRequestExecutor`)
3. Register the executor in `TaskExecutorFactory`
4. Update `Task.from_dict()` in `models/job_models.py` to handle the new type

Example:

```python
# In executors/task_executors.py
class HttpRequestExecutor(TaskExecutor):
    def execute(self, task: HttpRequestTask) -> bool:
        # Implementation
        pass

# Register it
TaskExecutorFactory.register_executor('http_request', HttpRequestExecutor())
```

## Logging

The scheduler logs all job executions with the following information:

- Job ID
- Execution timestamp (ISO 8601 format)
- Status (SUCCESS or FAILURE)

Logs are output to stdout/stderr and can be redirected to files or log management systems.

## Production Features

- **Database Persistence**: Optional SQLite or PostgreSQL support for job and execution history
- **Configuration Management**: Environment-based configuration with validation
- **Retry Mechanism**: Automatic retries for failed jobs with exponential backoff
- **Resource Management**: Concurrency limits and resource tracking
- **Metrics**: Prometheus metrics for monitoring
- **Docker Support**: Containerized deployment with docker-compose

See `PRODUCTION.md` and `DEPLOYMENT.md` for production deployment details.

## Requirements

- Python 3.7+
- `croniter` library for cron expression parsing

## License

This is a demonstration project for the Eightfold coding challenge.

