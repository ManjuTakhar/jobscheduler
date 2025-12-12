FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /etc/chronoflow/jobs.d logs

# Install the package
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV JOBS_DIR=/etc/chronoflow/jobs.d
ENV LOG_DIR=/app/logs
ENV DATABASE_URL=sqlite:///./jobscheduler.db

# Expose metrics port
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/logs/scheduler.log') else 1)"

# Run the scheduler
CMD ["python", "-m", "job_scheduler.main", "--jobs-dir", "/etc/chronoflow/jobs.d"]

