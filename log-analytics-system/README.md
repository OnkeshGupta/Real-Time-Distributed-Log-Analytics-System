# Real-Time Distributed Log Analytics System

A production-ready, scalable log analytics system built with modern Python stack for ingesting, processing, and analyzing logs from distributed microservices in real-time.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Log Analytics System Architecture             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    Microservices Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ auth-service │  │payment-service│ │inventory-svc │  ...   │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────┬──────────────────────────────────┘
                            │ Generates logs
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Log Generator                               │
│  (Simulates services emitting logs in JSON format)            │
└────────────────────────┬─────────────────────────────────────┘
                         │ Publishes logs
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                    Apache Kafka                                │
│              Topic: logs_raw (Partitioned)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │ Consumes logs
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                   Log Processor (Consumer)                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ • Parse & Validate JSON                                │ │
│  │ • Normalize timestamps                                 │ │
│  │ • Anomaly Detection (score, classify)                 │ │
│  │ • Batch & Bulk Index                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │ Indexes logs
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                  Elasticsearch Cluster                         │
│              (Distributed Search & Analytics)                 │
│  Index: logs-index with full-text & keyword fields           │
└────────────────────────┬──────────────────────┬───────────────┘
         │               │                      │
    REST API         Query Interface      Visualization
         │               │                      │
         ▼               ▼                      ▼
┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│  API Gateway     │ │   Kibana UI     │ │  Grafana Dashboards
│  (FastAPI)       │ │   (Port 5601)   │ │  (Optional)
│  (Port 8000)     │ └─────────────────┘ └──────────────────┘
└──────────────────┘
```

## Key Components

### 1. **Log Generator** (`log_generator/`)
- Simulates 5 microservices (auth, payment, inventory, user, api-gateway)
- Generates realistic logs with:
  - Timestamps, service names, log levels (INFO, WARN, ERROR, DEBUG)
  - HTTP status codes, request IDs, user IDs
  - Response times, error codes, tags
- Configurable batch size and flush intervals

### 2. **Log Producer** (Integrated in Log Generator)
- Kafka producer that sends logs to `logs_raw` topic
- Supports batching and compression (snappy)
- Automatic retries on failure

### 3. **Log Processor** (`log_processor/`)
- **Kafka Consumer**: Subscribes to `logs_raw` topic
- **Anomaly Detector**: Marks logs as anomalies based on rules:
  - ERROR level logs → anomaly
  - Status codes ≥ 400 → anomaly
  - Response time > 3000ms → anomaly
  - Presence of error codes → anomaly
  - Assigns severity score (0-100)
- **Elasticsearch Indexer**: Bulk indexes processed logs

### 4. **API Gateway** (`api_gateway/`)
FastAPI application with REST endpoints:
- `GET /health` - Service health check
- `GET /logs` - Search logs with filters (service_name, level, status_code, anomaly, timestamps, pagination)
- `GET /logs/stats` - Aggregated statistics
- `GET /logs/anomalies` - Find anomalies
- `GET /docs` - Swagger UI (interactive API documentation)

### 5. **Infrastructure**
- **Zookeeper**: Kafka coordination
- **Kafka**: Event streaming (3 brokers recommended for production)
- **Elasticsearch**: Search & indexing
- **Kibana**: Log visualization & exploration

## Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python 3.11+** (for local development/testing)
- **4GB RAM** minimum (8GB recommended)
- **Linux/macOS** or **Windows with WSL2** (Windows PowerShell supported for deployment)

## Quick Start

### 1. Clone/Setup the Project

```bash
cd log-analytics-system
```

### 2. Start the System

```bash
docker-compose up --build
```

This will:
- Build all service images
- Start all containers (Zookeeper, Kafka, Elasticsearch, Kibana, services)
- Create Kafka topics automatically
- Initialize Elasticsearch indices

Expected startup time: 30-60 seconds (first time)

### 3. Verify System is Running

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f

# Check API health
curl http://localhost:8000/health
```

## Usage

### API Gateway Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "elasticsearch": "healthy",
  "timestamp": 1702200000000
}
```

#### Search Logs
```bash
# Get all logs (page 1, 20 per page)
curl "http://localhost:8000/logs"

# Filter by service
curl "http://localhost:8000/logs?service_name=payment-service"

# Filter by error level
curl "http://localhost:8000/logs?level=ERROR"

# Filter by status code
curl "http://localhost:8000/logs?status_code=500"

# Get anomalies only
curl "http://localhost:8000/logs?anomaly=true"

# Filter by timestamp range (milliseconds since epoch)
curl "http://localhost:8000/logs?from_timestamp=1702100000000&to_timestamp=1702200000000"

# Pagination
curl "http://localhost:8000/logs?page=2&size=50"

# Combined filters
curl "http://localhost:8000/logs?service_name=auth-service&level=ERROR&anomaly=true&page=1&size=20"
```

#### Get Statistics
```bash
curl "http://localhost:8000/logs/stats"
```

Response:
```json
{
  "total_logs": 50000,
  "services": {
    "auth-service": 10000,
    "payment-service": 12000,
    "inventory-service": 15000,
    "user-service": 8000,
    "api-gateway": 5000
  },
  "levels": {
    "INFO": 40000,
    "WARN": 8000,
    "ERROR": 1800,
    "DEBUG": 200
  },
  "anomaly_count": 2500,
  "error_count": 1800
}
```

#### Search Anomalies
```bash
curl "http://localhost:8000/logs/anomalies"

# Filter by service
curl "http://localhost:8000/logs/anomalies?service_name=payment-service"
```

### Kibana UI

Access Kibana at: **http://localhost:5601**

1. **Create Index Pattern**:
   - Go to Stack Management > Index Patterns
   - Create pattern: `logs-*`
   - Timestamp field: `timestamp`

2. **Explore Logs**:
   - Go to Discover tab
   - Filter and search logs
   - Create visualizations

3. **Create Dashboards**:
   - Visualize error trends
   - Monitor anomalies
   - Track by service

### Interactive API Documentation

Swagger UI: **http://localhost:8000/docs**

ReDoc: **http://localhost:8000/redoc**

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_LOGS_RAW=logs_raw
KAFKA_LOG_BATCH_SIZE=100
KAFKA_LOG_FLUSH_INTERVAL_MS=5000

# Elasticsearch
ELASTIC_HOST=elasticsearch
ELASTIC_PORT=9200
ELASTIC_SCHEME=http
ELASTIC_INDEX_NAME=logs-index
ELASTIC_BULK_SIZE=1000
ELASTIC_BULK_TIMEOUT_S=5

# API Gateway
API_PORT=8000
```

### Tuning for Performance

**Log Generator** (`log_generator/main.py`):
- Increase `batch_size` for more logs per batch (e.g., 1000)
- Decrease `flush_interval_ms` for more frequent flushes

**Log Processor** (`log_processor/consumer.py`):
- Increase `batch_size` for larger Elasticsearch bulk operations
- Increase `flush_interval_s` to batch more before flushing
- Increase number of consumer instances for parallel processing

**Elasticsearch**:
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Allocate more heap for production
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_anomaly_detector.py -v

# Run with coverage
pytest tests/ --cov=log_generator --cov=log_processor --cov=api_gateway

# Run specific test
pytest tests/test_anomaly_detector.py::TestAnomalyDetector::test_error_level_is_anomaly -v
```

### Test Components

- **Anomaly Detector**: Tests for anomaly detection rules and severity scoring
- **Log Generator**: Tests for log generation and field validation
- **API Gateway**: Tests for endpoints, error handling, and model validation

## Project Structure

```
log-analytics-system/
├── docker-compose.yml          # Docker Compose orchestration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── configs/                    # Configuration modules
│   ├── kafka_config.py        # Kafka settings
│   └── elastic_config.py      # Elasticsearch settings
│
├── log_generator/             # Log generation service
│   ├── Dockerfile
│   ├── __init__.py
│   ├── generator.py           # Log generation logic
│   └── main.py               # Entry point, Kafka producer
│
├── log_processor/             # Log processing service
│   ├── Dockerfile
│   ├── __init__.py
│   ├── anomaly_detector.py   # Anomaly detection rules
│   ├── es_client.py          # Elasticsearch client
│   └── consumer.py           # Entry point, Kafka consumer
│
├── api_gateway/               # FastAPI application
│   ├── Dockerfile
│   ├── __init__.py
│   ├── main.py               # FastAPI app setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py         # Health check endpoint
│   │   └── logs.py           # Log search endpoints
│   └── services/
│       ├── __init__.py
│       └── elastic_service.py # Elasticsearch queries
│
└── tests/                     # Unit tests
    ├── __init__.py
    ├── conftest.py           # Pytest configuration
    ├── test_anomaly_detector.py
    ├── test_log_generator.py
    └── test_api_gateway.py
```

## Production Deployment Considerations

### Scaling the System

1. **Multiple Kafka Consumers**:
   ```yaml
   log_processor_1:
     build: ...
     environment:
       KAFKA_CONSUMER_GROUP: log_processor_group
   
   log_processor_2:
     build: ...
     environment:
       KAFKA_CONSUMER_GROUP: log_processor_group
   ```

2. **Elasticsearch Cluster**:
   - Use 3+ nodes for production
   - Set `number_of_replicas: 2`
   - Enable cross-cluster replication

3. **Kafka Cluster**:
   - Use 3-5 brokers for reliability
   - Enable log compaction for topics

4. **API Gateway Load Balancing**:
   ```yaml
   nginx:
     image: nginx:latest
     ports:
       - "80:80"
     volumes:
       - ./nginx.conf:/etc/nginx/nginx.conf
   ```

### Monitoring

- Use Prometheus + Grafana for metrics
- Enable Elasticsearch monitoring
- Configure log alerts for anomalies
- Set up distributed tracing (Jaeger)

### Data Retention

- Configure Elasticsearch index lifecycle management (ILM)
- Implement daily index rotation: `logs-2024.01.15`
- Archive old indices to S3/cold storage

### High Availability

- Use RabbitMQ or Kafka replicated topics
- Deploy Elasticsearch cluster across availability zones
- Implement circuit breakers in API Gateway
- Enable auto-healing of failed containers

## Troubleshooting

### Containers Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up --build

# Check disk space
docker system df
```

### Kafka Connection Issues

```bash
# Check Kafka is running
docker-compose ps kafka

# Test Kafka connectivity
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# View Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Elasticsearch Issues

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check indices
curl http://localhost:9200/_cat/indices

# Delete index if corrupted
curl -X DELETE http://localhost:9200/logs-index
```

### API Gateway Errors

```bash
# Check API logs
docker-compose logs api_gateway

# Test API directly
curl http://localhost:8000/health

# Check Pydantic validation errors
docker-compose logs api_gateway | grep "validation error"
```

## Performance Metrics

### Target Performance

- **Throughput**: 50,000+ logs/second (with batching and compression)
- **Indexing Latency**: <5 seconds (batch size 1000)
- **Query Latency**: <500ms for most queries
- **CPU Usage**: ~10-15% per service
- **Memory**: ~512MB per service

### Load Testing Example

```bash
# Generate 100 batches of 1000 logs each
# Monitor with:
curl http://localhost:8000/logs/stats

# Watch processor throughput
docker-compose logs log_processor | grep "Flushed batch"

# Check Elasticsearch indexing
curl http://localhost:9200/logs-index/_stats | jq '.indices."logs-index".primaries.indexing'
```

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Type hints required for all functions

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Check Docker logs: `docker-compose logs -f [service]`
- Review configuration files
- Check test coverage: `pytest --cov`
- Verify all containers are healthy: `docker-compose ps`

## Changelog

### v1.0.0 (Initial Release)
- ✅ Kafka-based log streaming
- ✅ Elasticsearch indexing
- ✅ Anomaly detection
- ✅ FastAPI REST endpoints
- ✅ Comprehensive tests
- ✅ Docker containerization
- ✅ Kibana integration
