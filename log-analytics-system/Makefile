.PHONY: help build up down logs test clean restart health

# Default target
help:
	@echo "Log Analytics System - Available Commands"
	@echo "=========================================="
	@echo "make build          - Build all Docker images"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make restart        - Restart all services"
	@echo "make logs           - View logs from all services"
	@echo "make logs-generator - View log generator logs"
	@echo "make logs-processor - View log processor logs"
	@echo "make logs-api       - View API gateway logs"
	@echo "make health         - Check system health"
	@echo "make test           - Run all tests"
	@echo "make test-coverage  - Run tests with coverage report"
	@echo "make clean          - Clean up containers and volumes"
	@echo "make ps             - Show running containers"
	@echo ""
	@echo "Endpoints:"
	@echo "=========="
	@echo "API:     http://localhost:8000"
	@echo "Docs:    http://localhost:8000/docs"
	@echo "Kibana:  http://localhost:5601"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 15
	@make health

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-generator:
	docker-compose logs -f log_generator

logs-processor:
	docker-compose logs -f log_processor

logs-api:
	docker-compose logs -f api_gateway

# Check system health
health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not ready yet"
	@echo ""
	@docker-compose ps

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest tests/ -v --cov=log_generator --cov=log_processor --cov=api_gateway --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Show running containers
ps:
	docker-compose ps

# Clean up
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete

# Generate sample logs
generate-sample:
	docker-compose exec log_generator python -c "from log_generator.generator import generate_batch_logs; import json; [print(json.dumps(log)) for log in generate_batch_logs(10)]"

# Query API for logs
query-logs:
	curl "http://localhost:8000/logs?page=1&size=10" | python3 -m json.tool

# Get statistics
stats:
	curl "http://localhost:8000/logs/stats" | python3 -m json.tool

# Get anomalies
anomalies:
	curl "http://localhost:8000/logs/anomalies?page=1&size=10" | python3 -m json.tool

# Development: Run with attached logs
dev:
	docker-compose up

# Production: Run in background
prod:
	docker-compose up -d
	@make health
