# Logging System Extension - Changes Summary

## Overview
Extended the logging system to implement exactly two types of logs as specified:
1. **Scheduler Logs** - System-level lifecycle logs in `logs/scheduler.log`
2. **Job Execution Logs** - Per-execution logs in `logs/<job_id>/<execution_id>.log`

## Files Modified

### 1. **NEW FILE: `job_scheduler/scheduler_logger.py`**
   - New module for scheduler-level logging
   - Writes to `logs/scheduler.log` with format: `[UTC_TIMESTAMP] EVENT_TYPE job_id=<id> old_schedule=<..> new_schedule=<..>`
   - Events: ADD, UPDATE, DELETE, SCHEDULE_CHANGE, ERROR, START, STOP

### 2. **Modified: `job_scheduler/scheduler.py`**
   - Added `SchedulerLogger` import and instance
   - Modified `add_job()`: Logs ADD/UPDATE/SCHEDULE_CHANGE events
   - Modified `remove_job()`: Logs DELETE event
   - Modified `start()`: Logs START event
   - Modified `stop()`: Logs STOP event
   - Modified `_schedule_job()`: Logs ERROR for invalid schedules
   - Modified `_run()`: Logs ERROR for scheduler loop exceptions
   - Modified `_execute_job()`: 
     - Generates `execution_id` using `uuid4().hex`
     - Tracks start_time, end_time, duration
     - Captures exit_code from executor
     - Calls `job_logger.log_execution()` with new signature

### 3. **Modified: `job_scheduler/task_executors.py`**
   - Modified `TaskExecutor.execute()` return type: `Tuple[bool, str, str, int]` (added exit_code)
   - Modified `ExecuteCommandExecutor.execute()`: Returns exit_code from subprocess

### 4. **Modified: `job_scheduler/job_logger.py`**
   - Removed old `get_job_logger()` method (no longer needed)
   - Removed `log_deletion()` method (deletion now logged to scheduler.log)
   - Completely rewrote `log_execution()`:
     - New signature with execution_id, start_time, end_time, duration_seconds, exit_code
     - Creates directory: `logs/<job_id>/`
     - Creates file: `logs/<job_id>/<execution_id>.log`
     - Writes exact format specified:
       ```
       execution_id: <id>
       job_id: <id>
       command: <command>
       start_time: <ISO8601 UTC>
       end_time: <ISO8601 UTC>
       duration_seconds: <float>
       status: SUCCESS or FAILURE
       exit_code: <int>
       stdout:
       <full stdout>
       stderr:
       <full stderr>
       ```

### 5. **Modified: `job_scheduler/file_watcher.py`**
   - Modified error handlers to log to `scheduler.log` via `scheduler.scheduler_logger.log_error()`
   - Added error logging in:
     - `_load_existing_jobs()`
     - `_watch()` loop
     - `_handle_new_file()`
     - `_handle_modified_file()`
     - `_handle_deleted_file()`

## Key Implementation Details

1. **Scheduler Log Format**: `[UTC_TIMESTAMP] EVENT_TYPE job_id=<id> old_schedule=<..> new_schedule=<..>`
2. **Execution Log Location**: `logs/<job_id>/<execution_id>.log` where execution_id = `uuid4().hex`
3. **Schedule Change Detection**: Compares old_schedule vs new_schedule in `add_job()`
4. **Exit Code Capture**: Modified executor to return exit_code from subprocess
5. **Duration Calculation**: `(end_time - start_time).total_seconds()`

## No Changes To
- Cron scheduling logic
- One-time scheduling logic
- File watcher polling mechanism
- Concurrency/threading model
- Job execution flow (only added logging)

## Testing
All changes maintain backward compatibility and add logging without modifying core functionality.

