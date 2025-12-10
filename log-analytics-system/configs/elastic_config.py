"""
Elasticsearch configuration module.
Contains all Elasticsearch-related settings for the log analytics system.
"""
import os
from typing import Dict, Any

# Elasticsearch connection settings
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "elasticsearch")
ELASTIC_PORT = int(os.getenv("ELASTIC_PORT", "9200"))
ELASTIC_SCHEME = os.getenv("ELASTIC_SCHEME", "http")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", "")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")

# Build connection URL
if ELASTIC_USERNAME and ELASTIC_PASSWORD:
    ELASTIC_URL = f"{ELASTIC_SCHEME}://{ELASTIC_USERNAME}:{ELASTIC_PASSWORD}@{ELASTIC_HOST}:{ELASTIC_PORT}"
else:
    ELASTIC_URL = f"{ELASTIC_SCHEME}://{ELASTIC_HOST}:{ELASTIC_PORT}"

# Index settings
ELASTIC_INDEX_NAME = os.getenv("ELASTIC_INDEX_NAME", "logs-index")
ELASTIC_INDEX_ALIAS = os.getenv("ELASTIC_INDEX_ALIAS", "logs")

# Index mapping with proper field types and analyzers
ELASTIC_INDEX_MAPPING: Dict[str, Any] = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "log_analyzer": {
                    "type": "standard",
                    "stopwords": "_english_",
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "timestamp": {"type": "date", "format": "epoch_millis||ISO_8601"},
            "service_name": {
                "type": "keyword",
                "fields": {"text": {"type": "text", "analyzer": "standard"}},
            },
            "level": {"type": "keyword"},
            "message": {
                "type": "text",
                "analyzer": "log_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "request_id": {"type": "keyword"},
            "status_code": {"type": "integer"},
            "anomaly": {"type": "boolean"},
            "severity_score": {"type": "integer"},
            "user_id": {"type": "keyword"},
            "path": {"type": "keyword"},
            "method": {"type": "keyword"},
            "response_time_ms": {"type": "integer"},
            "error_code": {"type": "keyword"},
            "tags": {"type": "keyword"},
        }
    },
}

# Bulk indexing settings
ELASTIC_BULK_SIZE = int(os.getenv("ELASTIC_BULK_SIZE", "1000"))
ELASTIC_BULK_TIMEOUT_S = int(os.getenv("ELASTIC_BULK_TIMEOUT_S", "30"))

# Search settings
ELASTIC_DEFAULT_PAGE_SIZE = int(os.getenv("ELASTIC_DEFAULT_PAGE_SIZE", "20"))
ELASTIC_MAX_PAGE_SIZE = int(os.getenv("ELASTIC_MAX_PAGE_SIZE", "100"))

# Retry settings
ELASTIC_MAX_RETRIES = int(os.getenv("ELASTIC_MAX_RETRIES", "3"))
ELASTIC_RETRY_TIMEOUT_S = int(os.getenv("ELASTIC_RETRY_TIMEOUT_S", "30"))
