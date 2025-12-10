@echo off
REM Log Analytics System Setup Script for Windows
REM This script sets up the development environment and starts the system

setlocal enabledelayedexpansion

REM Colors simulation (limited in Windows batch)
echo.
echo ================================================================
echo   Real-Time Distributed Log Analytics System Setup
echo ================================================================
echo.

REM Check Docker
echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed
    echo Please install Docker from https://www.docker.com
    exit /b 1
)
echo [OK] Docker is installed

REM Check Docker Compose
echo Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed
    echo Please install Docker Compose
    exit /b 1
)
echo [OK] Docker Compose is installed

REM Offer to rebuild images
echo.
set /p REBUILD="Do you want to rebuild Docker images? (y/n): "
if /i "%REBUILD%"=="y" (
    echo Building Docker images...
    docker-compose build
    if errorlevel 1 (
        echo [ERROR] Failed to build images
        exit /b 1
    )
    echo [OK] Docker images built
)

REM Start services
echo.
echo Starting services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)
echo [OK] Services started

REM Wait for services
echo.
echo Waiting for services to be ready...

REM Wait for Elasticsearch
echo Checking Elasticsearch...
for /L %%i in (1,1,30) do (
    curl -s http://localhost:9200 >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Elasticsearch is ready
        goto elasticsearch_ok
    )
    timeout /t 1 /nobreak >nul
)
echo [WARNING] Elasticsearch may still be starting

:elasticsearch_ok
REM Wait for API Gateway
echo Checking API Gateway...
for /L %%i in (1,1,30) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo [OK] API Gateway is ready
        goto api_ok
    )
    timeout /t 1 /nobreak >nul
)
echo [WARNING] API Gateway may still be starting

:api_ok
REM Show status
echo.
echo System Status:
docker-compose ps
echo.

REM Show endpoints
echo Service Endpoints:
echo   API Gateway:     http://localhost:8000
echo   API Docs:        http://localhost:8000/docs
echo   Kibana:          http://localhost:5601
echo   Elasticsearch:   http://localhost:9200
echo.

REM Show example queries
echo Example Queries:
echo   REM Get health status
echo   curl http://localhost:8000/health
echo.
echo   REM Search all logs
echo   curl http://localhost:8000/logs
echo.
echo   REM Get statistics
echo   curl http://localhost:8000/logs/stats
echo.
echo   REM Find anomalies
echo   curl http://localhost:8000/logs/anomalies
echo.

echo Setup complete!
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down
echo To run tests: pytest tests/ -v
echo.

endlocal
