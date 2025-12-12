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

### Components

1. **JobScheduler**: Core scheduling engine that manages job execution
2. **JobFileWatcher**: Monitors the jobs directory for file changes
3. **TaskExecutor**: Extensible system for executing different task types
4. **Models**: Job and Task data structures

### Extensibility

To add a new task type:

1. Create a new task class in `models.py` (e.g., `HttpRequestTask`)
2. Create a corresponding executor in `task_executors.py` (e.g., `HttpRequestExecutor`)
3. Register the executor in `TaskExecutorFactory`
4. Update `Task.from_dict()` to handle the new type

Example:

```python
# In task_executors.py
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

## Limitations

- **In-Memory Only**: Job state is not persisted. Restarting the service rebuilds state from job files.
- **No Job History**: Execution history is not stored beyond logs.
- **File-Based Only**: Jobs must be defined as JSON files in the watched directory.

## Requirements

- Python 3.7+
- `croniter` library for cron expression parsing

## License

This is a demonstration project for the Eightfold coding challenge.

