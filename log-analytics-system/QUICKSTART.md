# Quick Start Guide

Get the Log Analytics System up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- ~4GB available RAM
- ~5GB available disk space
- Terminal/Command Prompt

## Step 1: Clone/Navigate to Project

```bash
cd log-analytics-system
```

## Step 2: Start the System (Choose Your OS)

### Linux/macOS:

```bash
# Option A: Using setup script (recommended)
chmod +x setup.sh
./setup.sh

# Option B: Using make
make build
make up

# Option C: Manual
docker-compose up --build -d
```

### Windows (PowerShell/Command Prompt):

```powershell
# Option A: Using setup script
.\setup.bat

# Option B: Manual
docker-compose up --build -d
```

## Step 3: Verify Everything is Running

```bash
# Check container status
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","elasticsearch":"healthy","timestamp":1702200000000}
```

## Step 4: Generate and Explore Logs

### View API Documentation
Open in browser: **http://localhost:8000/docs**

### Search Logs (API)

```bash
# Get first 20 logs
curl "http://localhost:8000/logs" | jq

# Filter by service
curl "http://localhost:8000/logs?service_name=payment-service" | jq

# Find errors
curl "http://localhost:8000/logs?level=ERROR" | jq

# Get statistics
curl "http://localhost:8000/logs/stats" | jq

# Find anomalies
curl "http://localhost:8000/logs/anomalies" | jq
```

### Explore Logs (Kibana UI)
Open in browser: **http://localhost:5601**

1. Go to **Discover** tab
2. Create index pattern: `logs-*`
3. Select `timestamp` as time field
4. Browse and filter logs visually

## Step 5: Run Tests

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_anomaly_detector.py -v

# Run with coverage
pytest tests/ --cov=log_generator --cov=log_processor --cov=api_gateway
```

## Common Commands

```bash
# View logs
docker-compose logs -f                 # All services
docker-compose logs -f log_processor   # Specific service

# Stop system
docker-compose down

# Clean up (delete volumes)
docker-compose down -v

# Restart
docker-compose restart

# Status
docker-compose ps
docker-compose stats
```

## Performance Testing

```bash
# Run stress test
python stress_test.py

# With custom settings
NUM_BATCHES=50 BATCH_SIZE=5000 QUERY_THREADS=4 python stress_test.py
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose down -v
docker-compose up --build
```

### API returns 503
```bash
# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Wait 30 seconds and retry
sleep 30
curl http://localhost:8000/health
```

### No logs appearing
```bash
# Check Kafka topic exists
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check processor logs
docker-compose logs log_processor | tail -20

# Check generator is running
docker-compose logs log_generator | tail -10
```

## Monitoring

```bash
# Container resource usage
docker-compose stats

# Elasticsearch cluster health
curl http://localhost:9200/_cluster/health | jq

# Elasticsearch indices
curl http://localhost:9200/_cat/indices | jq

# Kafka consumer lag
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group log_processor_group \
  --describe
```

## API Examples with Different Filters

```bash
# Errors only
curl "http://localhost:8000/logs?level=ERROR&page=1&size=10"

# Specific service + errors
curl "http://localhost:8000/logs?service_name=auth-service&level=ERROR"

# High status codes (400+)
curl "http://localhost:8000/logs?status_code=500"

# Anomalies in last hour
FROM_TIME=$(($(date +%s)*1000 - 3600000))
TO_TIME=$(date +%s)*1000
curl "http://localhost:8000/logs/anomalies?from_timestamp=$FROM_TIME&to_timestamp=$TO_TIME"

# Get 100 items per page (max)
curl "http://localhost:8000/logs?page=1&size=100"

# Navigate through results
curl "http://localhost:8000/logs?page=2&size=20"
curl "http://localhost:8000/logs?page=3&size=20"
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the code structure in each service folder
3. Review [docker-compose.yml](docker-compose.yml) for configuration
4. Check [tests/](tests/) for example usage patterns
5. Customize configuration in [configs/](configs/)

## System Architecture Quick Overview

```
Services → Kafka → Log Processor → Elasticsearch ← API Gateway
                                          ↓
                                       Kibana UI
```

- **Services**: Generate logs (simulated by log_generator)
- **Kafka**: Message broker (reliable log transport)
- **Log Processor**: Consumes logs, detects anomalies, indexes to ES
- **Elasticsearch**: Stores and indexes logs
- **API Gateway**: REST API for querying logs
- **Kibana**: Visual log explorer

## Performance Goals

- **Ingestion**: 50,000+ logs/second
- **Query**: <500ms for typical searches
- **Indexing Latency**: <5 seconds

## Production Considerations

Before deploying to production:

1. **Scaling**: Run multiple log processor instances
2. **Replication**: Set Elasticsearch replicas to 2+
3. **Retention**: Implement index rotation (daily)
4. **Monitoring**: Add Prometheus + Grafana
5. **Alerting**: Set up anomaly alerts
6. **Security**: Enable SSL/TLS, authentication
7. **Backup**: Configure snapshot backups

See [README.md](README.md) for detailed production guidelines.

## Need Help?

Check the troubleshooting section in the full README, or review logs:

```bash
docker-compose logs [service_name]
```

## Clean Up

When done:

```bash
# Stop and remove all containers
docker-compose down

# Remove volumes (including data)
docker-compose down -v

# Clean up local files
rm -rf .pytest_cache __pycache__
```

Enjoy! 🚀
