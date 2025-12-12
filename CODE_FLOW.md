# Job Scheduler - Code Flow

## High-Level Architecture

```
┌─────────────────┐
│   main.py       │  Entry point
│   (CLI)         │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ JobScheduler    │  │ JobFileWatcher  │
│ (Core Engine)   │  │ (File Monitor)  │
└─────────────────┘  └─────────────────┘
```

## Detailed Flow

### 1. **Startup Phase** (`main.py`)

```
main()
  │
  ├─> Parse command line arguments (--jobs-dir, --log-level)
  │
  ├─> setup_logging() - Configure logging
  │
  ├─> Create JobScheduler() instance
  │   └─> Initialize:
  │       - self.jobs: Dict[str, Job]  (job definitions)
  │       - self.scheduled_jobs: Dict[str, ScheduledJob]  (scheduled instances)
  │       - self.lock: threading.Lock()  (thread safety)
  │
  ├─> Create JobFileWatcher(jobs_dir, scheduler)
  │   └─> Initialize:
  │       - self.file_timestamps: Dict[str, float]  (track file mtimes)
  │       - self.file_to_job_id: Dict[str, str]  (file → job_id mapping)
  │
  ├─> Setup signal handlers (SIGINT, SIGTERM) for graceful shutdown
  │
  ├─> scheduler.start()  [See Step 2]
  │
  └─> file_watcher.start()  [See Step 3]
```

### 2. **Scheduler Startup** (`scheduler.py`)

```
scheduler.start()
  │
  ├─> Set self.running = True
  │
  └─> Start background thread: scheduler_thread
      └─> Thread runs: _run() method  [See Step 6]
```

### 3. **File Watcher Startup** (`file_watcher.py`)

```
file_watcher.start()
  │
  ├─> Ensure watch_directory exists (create if needed)
  │
  ├─> _load_existing_jobs()  [See Step 4]
  │
  ├─> Set self.running = True
  │
  └─> Start background thread: watcher_thread
      └─> Thread runs: _watch() method  [See Step 5]
```

### 4. **Load Existing Jobs** (`file_watcher.py`)

```
_load_existing_jobs()
  │
  ├─> Scan directory: glob("*.json")
  │
  └─> For each JSON file:
      │
      ├─> Job.from_json_file(file_path)
      │   └─> Parse JSON → Create Job object
      │       ├─> job_id, description, schedule, task
      │       └─> Task.from_dict() → Create ExecuteCommandTask
      │
      ├─> scheduler.add_job(job)  [See Step 7]
      │
      ├─> Store file_timestamps[file_path] = mtime
      │
      └─> Store file_to_job_id[file_path] = job.job_id
```

### 5. **File Watching Loop** (`file_watcher.py`)

```
_watch()  [Runs every 2 seconds]
  │
  ├─> Scan directory: glob("*.json")
  │   └─> Get current_files: Dict[file_path, mtime]
  │
  ├─> Detect NEW files:
  │   └─> If file_path not in file_timestamps:
  │       ├─> _handle_new_file(file_path)
  │       │   ├─> Job.from_json_file(file_path)
  │       │   └─> scheduler.add_job(job)  [See Step 7]
  │       └─> Update file_timestamps
  │
  ├─> Detect MODIFIED files:
  │   └─> If mtime != file_timestamps[file_path]:
  │       ├─> _handle_modified_file(file_path)
  │       │   ├─> Job.from_json_file(file_path)
  │       │   ├─> If job_id changed: scheduler.remove_job(old_job_id)
  │       │   └─> scheduler.add_job(job)  [See Step 7]
  │       └─> Update file_timestamps
  │
  └─> Detect DELETED files:
      └─> If file_path in file_timestamps but not in current_files:
          ├─> _handle_deleted_file(file_path)
          │   └─> scheduler.remove_job(job_id)
          └─> Remove from file_timestamps
```

### 6. **Scheduler Execution Loop** (`scheduler.py`)

```
_run()  [Runs every 1 second]
  │
  ├─> while self.running:
  │   │
  │   ├─> Acquire lock
  │   │
  │   ├─> Check all scheduled_jobs:
  │   │   └─> For each scheduled_job:
  │   │       └─> if scheduled_job.should_run():
  │   │           └─> Add to jobs_to_run list
  │   │
  │   └─> Release lock
  │
  ├─> Execute jobs (outside lock):
  │   └─> For each job in jobs_to_run:
  │       ├─> _execute_job(scheduled_job)  [See Step 8]
  │       ├─> scheduled_job.mark_executed()
  │       │
  │       ├─> If RecurringScheduledJob:
  │       │   └─> scheduled_job.reschedule()
  │       │       └─> Calculate next_run_time = cron.get_next(datetime)
  │       │
  │       └─> If OneTimeScheduledJob:
  │           └─> Remove from scheduled_jobs (already executed)
  │
  └─> sleep(1)  # Check again in 1 second
```

### 7. **Add/Update Job** (`scheduler.py`)

```
scheduler.add_job(job)
  │
  ├─> Acquire lock
  │
  ├─> Store: self.jobs[job.job_id] = job
  │
  ├─> _schedule_job(job)
  │   │
  │   ├─> If job already scheduled:
  │   │   └─> Cancel existing scheduled_job
  │   │
  │   ├─> Check schedule type:
  │   │
  │   ├─> If ONE-TIME (ISO 8601 timestamp):
  │   │   ├─> Parse: datetime.fromisoformat(schedule)
  │   │   ├─> Check if in past → skip if so
  │   │   └─> Create: OneTimeScheduledJob(job, schedule_time)
  │   │
  │   └─> If RECURRING (cron expression):
  │       ├─> Create: croniter(schedule, now)
  │       └─> Create: RecurringScheduledJob(job, cron)
  │           └─> Calculate: next_run_time = cron.get_next(datetime)
  │
  └─> Store: self.scheduled_jobs[job.job_id] = scheduled_job
```

### 8. **Execute Job** (`scheduler.py`)

```
_execute_job(scheduled_job)
  │
  └─> Start new thread (non-blocking):
      │
      └─> run():
          │
          ├─> Get job and executor:
          │   ├─> job = scheduled_job.job
          │   └─> executor = TaskExecutorFactory.get_executor(job.task.type)
          │
          ├─> Log: "Job execution started"
          │
          ├─> executor.execute(job.task)
          │   └─> ExecuteCommandExecutor.execute(task)
          │       ├─> subprocess.run(task.command, shell=True)
          │       └─> Return True/False (success/failure)
          │
          └─> Log: "Job execution completed" (with status)
```

## Data Flow Example

### Example: Adding a new job file

```
1. User creates: /jobs.d/new-job.json
   │
2. File Watcher detects (within 2 seconds):
   │
3. _handle_new_file("new-job.json")
   │
4. Job.from_json_file() → Parse JSON
   │   └─> Creates Job object with:
   │       - job_id: "new-job"
   │       - schedule: "*/5 * * * *"
   │       - task: ExecuteCommandTask
   │
5. scheduler.add_job(job)
   │
6. _schedule_job(job)
   │   ├─> Creates croniter("*/5 * * * *", now)
   │   └─> Creates RecurringScheduledJob
   │       └─> next_run_time = cron.get_next(datetime)
   │
7. Job stored in scheduled_jobs["new-job"]
   │
8. Scheduler loop checks every second:
   │   └─> When now >= next_run_time:
   │       └─> _execute_job() → Runs command
   │
9. After execution:
   │   └─> reschedule() → Calculate next_run_time
```

## Threading Model

```
Main Thread:
  └─> Keeps process alive (sleep loop)

Scheduler Thread:
  └─> Continuously checks and executes jobs

File Watcher Thread:
  └─> Continuously monitors directory for changes

Job Execution Threads:
  └─> One per job execution (concurrent execution)
```

## Key Components

1. **JobScheduler**: Core scheduling engine
   - Manages job lifecycle
   - Executes jobs at scheduled times
   - Thread-safe operations

2. **JobFileWatcher**: File system monitor
   - Detects file changes (polling)
   - Loads/updates/removes jobs dynamically

3. **ScheduledJob**: Wrapper for scheduled execution
   - OneTimeScheduledJob: Runs once at specific time
   - RecurringScheduledJob: Runs repeatedly via cron

4. **TaskExecutor**: Executes different task types
   - ExecuteCommandExecutor: Runs shell commands
   - Extensible for future task types

