# Deployment Guide

## Quick Start

### Using Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f scheduler

# Stop
docker-compose down
```

### Using Systemd

1. Create service file `/etc/systemd/system/job-scheduler.service`:

```ini
[Unit]
Description=Job Scheduler Service
After=network.target

[Service]
Type=simple
User=scheduler
WorkingDirectory=/opt/job-scheduler
Environment="PATH=/opt/job-scheduler/venv/bin"
ExecStart=/opt/job-scheduler/venv/bin/python -m job_scheduler.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:

```bash
sudo systemctl enable job-scheduler
sudo systemctl start job-scheduler
sudo systemctl status job-scheduler
```

### Using Supervisor

1. Install supervisor:
```bash
apt-get install supervisor
```

2. Create config `/etc/supervisor/conf.d/job-scheduler.conf`:

```ini
[program:job-scheduler]
command=/opt/job-scheduler/venv/bin/python -m job_scheduler.main
directory=/opt/job-scheduler
user=scheduler
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/job-scheduler.log
```

3. Start:
```bash
supervisorctl reread
supervisorctl update
supervisorctl start job-scheduler
```

## Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

## Health Checks

The scheduler creates `logs/scheduler.log` when running. Use this for health checks:

```bash
# Health check script
#!/bin/bash
if [ -f /app/logs/scheduler.log ]; then
    exit 0
else
    exit 1
fi
```

## Monitoring

### Prometheus

Metrics endpoint: `http://localhost:9090/metrics`

### Log Aggregation

Configure log aggregation tools (ELK, Loki, etc.) to collect:
- `logs/scheduler.log`
- `logs/<job_id>/*.log`

## Backup Strategy

1. **Job Files**: Backup `/etc/chronoflow/jobs.d/` regularly
2. **Database**: 
   - SQLite: Backup `jobscheduler.db` file
   - PostgreSQL: Use `pg_dump`
3. **Logs**: Archive old logs monthly

## Scaling

For horizontal scaling:
- Use shared database (PostgreSQL)
- Only one scheduler instance should be active
- Consider job queue system for distributed execution

