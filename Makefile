# News Aggregator Makefile

.PHONY: help setup install clean test lint format run-api run-crawler run-processor run-web docker-build docker-up docker-down migrate migrate-create migrate-up migrate-down

# Default target
help:
	@echo "News Aggregator Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make help                 Show this help message"
	@echo "  make setup                Set up the development environment"
	@echo "  make install              Install Python dependencies"
	@echo "  make clean                Remove build artifacts and cache files"
	@echo "  make test                 Run tests"
	@echo "  make lint                 Run linters"
	@echo "  make format               Format code"
	@echo "  make run-api              Run the API server"
	@echo "  make run-crawler          Run the crawler"
	@echo "  make run-processor        Run the processor"
	@echo "  make run-web              Run the web interface"
	@echo "  make docker-build         Build Docker images"
	@echo "  make docker-up            Start Docker containers"
	@echo "  make docker-down          Stop Docker containers"
	@echo "  make migrate              Run database migrations"
	@echo "  make migrate-create       Create a new migration"
	@echo "  make migrate-up           Apply migrations"
	@echo "  make migrate-down         Rollback migrations"

# Setup
setup:
	@echo "Setting up development environment..."
	@bash scripts/setup.sh

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

# Clean
clean:
	@echo "Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .pytest_cache -exec rm -rf {} +
	@find . -type d -name .coverage -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -rf build/
	@rm -rf dist/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .pytest_cache/
	@rm -rf web/dist/
	@rm -rf web/node_modules/

# Testing
test:
	@echo "Running tests..."
	@pytest tests/ -v

# Linting
lint:
	@echo "Running linters..."
	@flake8 api/ crawler/ processor/ storage/ tests/
	@mypy api/ crawler/ processor/ storage/ tests/
	@cd web && npm run lint

# Formatting
format:
	@echo "Formatting code..."
	@black api/ crawler/ processor/ storage/ tests/
	@isort api/ crawler/ processor/ storage/ tests/
	@cd web && npm run format

# Run services
run-api:
	@echo "Running API server..."
	@uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-crawler:
	@echo "Running crawler..."
	@python -m crawler.main

run-processor:
	@echo "Running processor..."
	@python -m processor.main

run-web:
	@echo "Running web interface..."
	@cd web && npm start

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@docker-compose -f docker/docker-compose.yml build

docker-up:
	@echo "Starting Docker containers..."
	@docker-compose -f docker/docker-compose.yml up -d

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose -f docker/docker-compose.yml down

# Database migrations
migrate:
	@echo "Running database migrations..."
	@alembic upgrade head

migrate-create:
	@echo "Creating a new migration..."
	@alembic revision --autogenerate -m "$(message)"

migrate-up:
	@echo "Applying migrations..."
	@alembic upgrade +1

migrate-down:
	@echo "Rolling back migrations..."
	@alembic downgrade -1