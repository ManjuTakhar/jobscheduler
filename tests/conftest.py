"""Pytest configuration and fixtures."""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_jobs_dir():
    """Create a temporary directory for job files."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "job_id": "test-job",
        "description": "Test job",
        "schedule": "* * * * *",
        "task": {
            "type": "execute_command",
            "command": "echo 'test'"
        }
    }

