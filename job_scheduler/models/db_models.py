"""Database models for job persistence."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class JobModel(Base):
    """Database model for jobs."""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=True)
    schedule = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    task_config = Column(Text, nullable=False)  # JSON string
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    executions = relationship("JobExecutionModel", back_populates="job", cascade="all, delete-orphan")


class JobExecutionModel(Base):
    """Database model for job executions."""
    __tablename__ = "job_executions"
    
    execution_id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String, nullable=False)  # SUCCESS, FAILURE, RUNNING
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    job = relationship("JobModel", back_populates="executions")


class SchedulerEventModel(Base):
    """Database model for scheduler events."""
    __tablename__ = "scheduler_events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String, nullable=False, index=True)  # ADD, UPDATE, DELETE, START, STOP, ERROR
    job_id = Column(String, nullable=True, index=True)
    old_schedule = Column(String, nullable=True)
    new_schedule = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

