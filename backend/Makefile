.PHONY: help install dev start start-prod test format lint clean

# Default target
help:
	@echo "FastAPI Supabase Backend Development Commands"
	@echo ""
	@echo "  install    - Install dependencies and setup the project"
	@echo "  dev        - Install development dependencies"
	@echo "  start      - Start the development server"
	@echo "  start-prod - Start the production server"
	@echo "  test       - Run tests"
	@echo "  format     - Format code with black and ruff"
	@echo "  lint       - Run linting checks"
	@echo "  clean      - Clean cache files"

# Install production dependencies
install:
	python -m venv venv
	. venv/bin/activate && pip install -e .

# Install development dependencies
dev: install
	. venv/bin/activate && pip install -e .[dev]

# Start development server
start:
	@./scripts/start.sh

# Start production server
start-prod:
	. venv/bin/activate && uvicorn main_app.main:app --host 0.0.0.0 --port 8000

# Run tests
test:
	. venv/bin/activate && pytest

# Format code
format:
	. venv/bin/activate && black src tests
	. venv/bin/activate && ruff check --fix src tests

# Run linting
lint:
	. venv/bin/activate && black --check src tests
	. venv/bin/activate && ruff check src tests
	. venv/bin/activate && mypy src

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache