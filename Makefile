.PHONY: help install dev docker-up docker-down docker-logs test lint format clean

help:
	@echo "Helios - Development Commands"
	@echo "=============================="
	@echo "install      - Install Python dependencies"
	@echo "dev          - Run development server"
	@echo "docker-up    - Start all Docker services"
	@echo "docker-down  - Stop all Docker services"
	@echo "docker-logs  - View Docker logs"
	@echo "test         - Run tests"
	@echo "lint         - Run linters"
	@echo "format       - Format code"
	@echo "clean        - Clean temporary files"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services are up!"
	@echo "API Docs: http://localhost:8001/docs"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Redpanda Console: http://localhost:8080"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

test:
	pytest tests/ -v --cov=.

lint:
	ruff check .
	mypy .

format:
	black .
	ruff check --fix .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ dist/ build/
