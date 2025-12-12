"""Metrics collection for monitoring."""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
job_executions_total = Counter(
    'job_executions_total',
    'Total number of job executions',
    ['job_id', 'status']
)

job_execution_duration = Histogram(
    'job_execution_duration_seconds',
    'Job execution duration in seconds',
    ['job_id'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

active_jobs = Gauge(
    'active_jobs',
    'Number of currently active jobs'
)

scheduler_events_total = Counter(
    'scheduler_events_total',
    'Total number of scheduler events',
    ['event_type']
)

failed_jobs = Counter(
    'failed_jobs_total',
    'Total number of failed jobs',
    ['job_id']
)


class MetricsCollector:
    """Collects and exposes metrics for monitoring."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.enabled = settings.enable_metrics
        self.metrics_port = getattr(settings, 'metrics_port', 9090)
    
    def start(self) -> None:
        """Start metrics HTTP server."""
        if self.enabled:
            try:
                start_http_server(self.metrics_port)
                logger.info(f"Metrics server started on port {self.metrics_port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {e}")
    
    def record_execution(
        self,
        job_id: str,
        status: str,
        duration_seconds: float
    ) -> None:
        """Record a job execution."""
        if not self.enabled:
            return
        
        job_executions_total.labels(job_id=job_id, status=status).inc()
        job_execution_duration.labels(job_id=job_id).observe(duration_seconds)
        
        if status == "FAILURE":
            failed_jobs.labels(job_id=job_id).inc()
    
    def record_event(self, event_type: str) -> None:
        """Record a scheduler event."""
        if not self.enabled:
            return
        
        scheduler_events_total.labels(event_type=event_type).inc()
    
    def set_active_jobs(self, count: int) -> None:
        """Set the number of active jobs."""
        if not self.enabled:
            return
        
        active_jobs.set(count)

