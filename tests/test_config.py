"""Tests for configuration management."""
import os
import pytest
from unittest.mock import patch

from job_scheduler.utils.config import Settings, settings


class TestSettings:
    """Test cases for Settings."""
    
    def test_default_settings(self):
        """Test default settings values."""
        test_settings = Settings()
        assert test_settings.jobs_dir == "/etc/chronoflow/jobs.d"
        assert test_settings.log_level == "INFO"
        assert test_settings.database_url == "sqlite:///./jobscheduler.db"
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {"JOBS_DIR": "/custom/jobs", "LOG_LEVEL": "DEBUG"}):
            test_settings = Settings()
            assert test_settings.jobs_dir == "/custom/jobs"
            assert test_settings.log_level == "DEBUG"
    
    def test_log_level_validation(self):
        """Test log level validation."""
        with pytest.raises(ValueError):
            Settings(log_level="INVALID")
    
    def test_valid_log_levels(self):
        """Test valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            test_settings = Settings(log_level=level)
            assert test_settings.log_level == level
    
    def test_database_url_validation(self):
        """Test database URL validation."""
        with pytest.raises(ValueError):
            Settings(database_url="")
    
    def test_settings_instance(self):
        """Test that settings instance is accessible."""
        assert isinstance(settings, Settings)
        assert settings.jobs_dir is not None

