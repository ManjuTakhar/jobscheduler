.PHONY: install test lint format clean docker-build docker-run docker-stop help

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  docker-stop  - Stop Docker container"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=job_scheduler --cov-report=html

lint:
	black --check job_scheduler/
	flake8 job_scheduler/ --max-line-length=120
	mypy job_scheduler/ --ignore-missing-imports

format:
	black job_scheduler/
	black tests/

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker-build:
	docker build -t job-scheduler:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

init-db:
	python -c "from job_scheduler.db_session import init_db; init_db()"

