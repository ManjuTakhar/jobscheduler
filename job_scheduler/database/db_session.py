"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from job_scheduler.utils.config import settings
from job_scheduler.models.db_models import Base


def get_engine():
    """Get database engine."""
    database_url = settings.database_url
    
    # Special handling for SQLite
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        pool_size = getattr(settings, 'database_pool_size', 10)
        engine = create_engine(
            database_url,
            pool_size=pool_size,
            echo=False
        )
    
    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session (context manager)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync() -> Session:
    """Get database session (synchronous)."""
    return SessionLocal()

