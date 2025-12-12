"""Database persistence layer for jobs and executions."""
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from job_scheduler.models import JobModel, JobExecutionModel, SchedulerEventModel, Job, Task
from .db_session import get_db_sync


class JobPersistence:
    """Handles persistence of jobs to database."""
    
    @staticmethod
    def save_job(job: Job) -> None:
        """Save or update a job in the database."""
        db = get_db_sync()
        try:
            # Convert task to JSON
            task_config = json.dumps({
                "type": job.task.type,
                **{k: v for k, v in job.task.__dict__.items() if k != "type"}
            })
            
            db_job = db.query(JobModel).filter(JobModel.job_id == job.job_id).first()
            
            if db_job:
                # Update existing job
                db_job.description = job.description
                db_job.schedule = job.schedule
                db_job.task_type = job.task.type
                db_job.task_config = task_config
                db_job.updated_at = datetime.now(timezone.utc)
            else:
                # Create new job
                db_job = JobModel(
                    job_id=job.job_id,
                    description=job.description,
                    schedule=job.schedule,
                    task_type=job.task.type,
                    task_config=task_config,
                    enabled=True
                )
                db.add(db_job)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def load_job(job_id: str) -> Optional[Job]:
        """Load a job from the database."""
        db = get_db_sync()
        try:
            db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if not db_job or not db_job.enabled:
                return None
            
            # Reconstruct task from JSON
            task_data = json.loads(db_job.task_config)
            task = Task.from_dict(task_data)
            
            return Job(
                job_id=db_job.job_id,
                description=db_job.description,
                schedule=db_job.schedule,
                task=task
            )
        finally:
            db.close()
    
    @staticmethod
    def load_all_jobs() -> List[Job]:
        """Load all enabled jobs from the database."""
        db = get_db_sync()
        try:
            db_jobs = db.query(JobModel).filter(JobModel.enabled == True).all()
            jobs = []
            
            for db_job in db_jobs:
                try:
                    task_data = json.loads(db_job.task_config)
                    task = Task.from_dict(task_data)
                    jobs.append(Job(
                        job_id=db_job.job_id,
                        description=db_job.description,
                        schedule=db_job.schedule,
                        task=task
                    ))
                except Exception as e:
                    # Skip jobs with invalid task configs
                    import logging
                    logging.getLogger(__name__).error(f"Failed to load job {db_job.job_id}: {e}")
            
            return jobs
        finally:
            db.close()
    
    @staticmethod
    def delete_job(job_id: str) -> None:
        """Delete a job from the database."""
        db = get_db_sync()
        try:
            db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if db_job:
                db.delete(db_job)
                db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def disable_job(job_id: str) -> None:
        """Disable a job without deleting it."""
        db = get_db_sync()
        try:
            db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
            if db_job:
                db_job.enabled = False
                db_job.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()


class ExecutionPersistence:
    """Handles persistence of job executions to database."""
    
    @staticmethod
    def save_execution(
        execution_id: str,
        job_id: str,
        start_time: datetime,
        end_time: Optional[datetime],
        duration_seconds: Optional[float],
        status: str,
        exit_code: Optional[int] = None,
        stdout: str = "",
        stderr: str = "",
        error_message: Optional[str] = None,
        retry_count: int = 0
    ) -> None:
        """Save a job execution to the database."""
        db = get_db_sync()
        try:
            execution = JobExecutionModel(
                execution_id=execution_id,
                job_id=job_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                status=status,
                exit_code=exit_code,
                stdout=stdout[:10000] if stdout else None,  # Limit size
                stderr=stderr[:10000] if stderr else None,  # Limit size
                error_message=error_message[:1000] if error_message else None,
                retry_count=retry_count
            )
            db.add(execution)
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_executions(
        job_id: Optional[str] = None,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get job executions from the database."""
        db = get_db_sync()
        try:
            query = db.query(JobExecutionModel)
            
            if job_id:
                query = query.filter(JobExecutionModel.job_id == job_id)
            if status:
                query = query.filter(JobExecutionModel.status == status)
            
            executions = query.order_by(JobExecutionModel.start_time.desc()).limit(limit).all()
            
            return [
                {
                    "execution_id": e.execution_id,
                    "job_id": e.job_id,
                    "start_time": e.start_time.isoformat() if e.start_time else None,
                    "end_time": e.end_time.isoformat() if e.end_time else None,
                    "duration_seconds": e.duration_seconds,
                    "status": e.status,
                    "exit_code": e.exit_code,
                    "retry_count": e.retry_count
                }
                for e in executions
            ]
        finally:
            db.close()


class EventPersistence:
    """Handles persistence of scheduler events to database."""
    
    @staticmethod
    def save_event(
        event_type: str,
        job_id: Optional[str] = None,
        old_schedule: Optional[str] = None,
        new_schedule: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Save a scheduler event to the database."""
        db = get_db_sync()
        try:
            event = SchedulerEventModel(
                event_type=event_type,
                job_id=job_id,
                old_schedule=old_schedule,
                new_schedule=new_schedule,
                error_message=error_message[:1000] if error_message else None
            )
            db.add(event)
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

