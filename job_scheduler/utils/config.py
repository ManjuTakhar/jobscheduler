"""Configuration management for production deployment."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Job Directory
    jobs_dir: str = Field(
        default="/etc/chronoflow/jobs.d",
        env="JOBS_DIR",
        description="Directory containing job definition files"
    )
    
    # Logging
    log_dir: str = Field(
        default="logs",
        env="LOG_DIR",
        description="Directory for log files"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite:///./jobscheduler.db",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    database_pool_size: int = Field(
        default=10,
        env="DATABASE_POOL_SIZE",
        description="Database connection pool size"
    )
    
    # Scheduler
    scheduler_check_interval: float = Field(
        default=1.0,
        env="SCHEDULER_CHECK_INTERVAL",
        description="Scheduler check interval in seconds"
    )
    max_concurrent_jobs: int = Field(
        default=50,
        env="MAX_CONCURRENT_JOBS",
        description="Maximum concurrent job executions"
    )
    job_timeout: int = Field(
        default=3600,
        env="JOB_TIMEOUT",
        description="Default job timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        env="MAX_RETRIES",
        description="Maximum retry attempts for failed jobs"
    )
    retry_delay: int = Field(
        default=60,
        env="RETRY_DELAY",
        description="Delay between retries in seconds"
    )
    
    # Monitoring
    enable_metrics: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable Prometheus metrics"
    )
    # File Watcher
    file_watcher_interval: float = Field(
        default=2.0,
        env="FILE_WATCHER_INTERVAL",
        description="File watcher check interval in seconds"
    )
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Ensure database URL is valid."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

