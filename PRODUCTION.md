# Production Deployment Guide

## Overview

This guide covers deploying the Job Scheduler in a production environment.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL (optional, SQLite is default)
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Direct Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Initialize database
python -c "from job_scheduler.db_session import init_db; init_db()"
```

### Option 2: Docker Deployment

```bash
# Build image
docker build -t job-scheduler:latest .

# Run with docker-compose
docker-compose up -d
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Job Directory
JOBS_DIR=/etc/chronoflow/jobs.d

# Database (SQLite default)
DATABASE_URL=sqlite:///./jobscheduler.db

# For PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/jobscheduler

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Scheduler Settings
MAX_CONCURRENT_JOBS=50
JOB_TIMEOUT=3600
MAX_RETRIES=3
RETRY_DELAY=60

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Running the Scheduler

### Development

```bash
python -m job_scheduler.main --jobs-dir ./examples/jobs.d --log-level INFO
```

### Production

```bash
# Using systemd service
sudo systemctl start job-scheduler

# Or using supervisor
supervisord -c supervisor.conf
```

## Monitoring

### Metrics

Prometheus metrics are available on port 9090 (configurable):

- `job_executions_total` - Total job executions by status
- `job_execution_duration_seconds` - Execution duration histogram
- `active_jobs` - Current number of active jobs
- `scheduler_events_total` - Scheduler events counter
- `failed_jobs_total` - Failed job counter

### Logs

- Scheduler logs: `logs/scheduler.log`
- Job execution logs: `logs/<job_id>/<execution_id>.log`

## Database

### SQLite (Default)

No additional setup required. Database file created automatically.

### PostgreSQL

1. Create database:
```sql
CREATE DATABASE jobscheduler;
```

2. Update `DATABASE_URL` in `.env`

3. Initialize tables:
```bash
python -c "from job_scheduler.db_session import init_db; init_db()"
```

## High Availability

For high availability:

1. Use PostgreSQL instead of SQLite
2. Deploy multiple scheduler instances (only one should be active)
3. Use external job queue (Redis, RabbitMQ) for distributed execution
4. Monitor with Prometheus and alerting

## Security

1. Set appropriate file permissions on job files
2. Use read-only mounts for job directory
3. Run scheduler with non-root user
4. Enable firewall rules for metrics port
5. Use secrets management for sensitive configuration

## Backup

1. Backup job definition files regularly
2. Backup database (SQLite file or PostgreSQL dump)
3. Backup log files for audit trail

## Troubleshooting

### Jobs not executing

- Check scheduler.log for errors
- Verify job files are valid JSON
- Check cron expression validity
- Verify file permissions

### High resource usage

- Reduce `MAX_CONCURRENT_JOBS`
- Increase `SCHEDULER_CHECK_INTERVAL`
- Review job execution times

### Database issues

- Check database connection string
- Verify database permissions
- Check disk space

## Performance Tuning

- Adjust `MAX_CONCURRENT_JOBS` based on system resources
- Use PostgreSQL for better performance with many jobs
- Increase `SCHEDULER_CHECK_INTERVAL` to reduce CPU usage
- Monitor metrics to identify bottlenecks

