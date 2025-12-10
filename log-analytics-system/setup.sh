#!/bin/bash

# Log Analytics System Setup Script
# This script sets up the development environment and starts the system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        echo "Please install Docker from https://www.docker.com"
        exit 1
    fi
    log_success "Docker is installed"
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        echo "Please install Docker Compose from https://www.docker.com"
        exit 1
    fi
    log_success "Docker Compose is installed"
}

check_disk_space() {
    available=$(df /var/lib/docker 2>/dev/null | awk 'NR==2 {print $4}' || echo "unknown")
    if [ "$available" != "unknown" ] && [ "$available" -lt 5242880 ]; then
        log_warning "Low disk space available ($(($available / 1024))MB)"
    fi
    log_success "Disk space check complete"
}

build_images() {
    log_info "Building Docker images..."
    docker-compose build --no-cache
    log_success "Docker images built successfully"
}

start_services() {
    log_info "Starting services..."
    docker-compose up -d
    log_success "Services started"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for Elasticsearch
    log_info "Waiting for Elasticsearch..."
    for i in {1..30}; do
        if curl -s http://localhost:9200 > /dev/null 2>&1; then
            log_success "Elasticsearch is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Elasticsearch failed to start"
            return 1
        fi
        sleep 1
    done
    
    # Wait for Kafka
    log_info "Waiting for Kafka..."
    for i in {1..30}; do
        if docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
            log_success "Kafka is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Kafka failed to start"
            return 1
        fi
        sleep 1
    done
    
    # Wait for API Gateway
    log_info "Waiting for API Gateway..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API Gateway is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "API Gateway failed to start"
            return 1
        fi
        sleep 1
    done
}

show_status() {
    log_info "System Status:"
    echo ""
    docker-compose ps
    echo ""
}

show_endpoints() {
    log_info "Service Endpoints:"
    echo ""
    echo "  API Gateway:  ${BLUE}http://localhost:8000${NC}"
    echo "  API Docs:     ${BLUE}http://localhost:8000/docs${NC}"
    echo "  Kibana:       ${BLUE}http://localhost:5601${NC}"
    echo "  Elasticsearch: ${BLUE}http://localhost:9200${NC}"
    echo ""
}

show_example_queries() {
    log_info "Example Queries:"
    echo ""
    echo "  # Get health status"
    echo "  curl http://localhost:8000/health | jq"
    echo ""
    echo "  # Search all logs"
    echo "  curl http://localhost:8000/logs | jq"
    echo ""
    echo "  # Get statistics"
    echo "  curl http://localhost:8000/logs/stats | jq"
    echo ""
    echo "  # Find anomalies"
    echo "  curl http://localhost:8000/logs/anomalies | jq"
    echo ""
    echo "  # Filter by service"
    echo "  curl 'http://localhost:8000/logs?service_name=payment-service' | jq"
    echo ""
}

main() {
    clear
    
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   Real-Time Distributed Log Analytics System Setup    ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    log_info "Starting setup..."
    echo ""
    
    # Checks
    log_info "Running pre-flight checks..."
    check_docker
    check_docker_compose
    check_disk_space
    echo ""
    
    # Build and start
    log_info "Preparing to start system..."
    read -p "Do you want to rebuild Docker images? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_images
    else
        log_info "Skipping image rebuild"
    fi
    echo ""
    
    start_services
    wait_for_services
    echo ""
    
    show_status
    show_endpoints
    show_example_queries
    
    log_success "Setup complete!"
    echo ""
    log_info "To view logs: docker-compose logs -f"
    log_info "To stop services: docker-compose down"
    log_info "To run tests: pytest tests/ -v"
    echo ""
}

main "$@"
