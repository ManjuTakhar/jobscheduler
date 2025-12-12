# Changelog

## [2.0.0] - Production Release

### Added
- Database persistence layer (SQLite and PostgreSQL support)
- Configuration management with environment variables
- Retry mechanism for failed jobs
- Resource limiting and concurrency control
- Prometheus metrics collection
- Docker and docker-compose support
- CI/CD pipeline with GitHub Actions
- Comprehensive production documentation
- 25+ example job files
- Makefile for common tasks
- Health check support

### Changed
- Separated database models and session management
- Improved error handling
- Enhanced logging structure
- Better resource management

### Fixed
- Thread safety improvements
- Better error recovery

## [1.0.0] - Initial Release

### Added
- Basic job scheduling with cron and one-time schedules
- File-based job management
- Job execution logging
- Task executor framework

