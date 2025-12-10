"""
Kafka configuration module.
Contains all Kafka-related settings for the log analytics system.
"""
import os
from typing import Dict, Any

# Kafka connection settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_TOPIC_LOGS_RAW = os.getenv("KAFKA_TOPIC_LOGS_RAW", "logs_raw")

# Producer settings
KAFKA_PRODUCER_CONFIG: Dict[str, Any] = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "acks": "all",
    "retries": 3,
    "max_in_flight_requests_per_connection": 1,
    "compression_type": "snappy",
}

# Consumer settings
KAFKA_CONSUMER_CONFIG: Dict[str, Any] = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "group_id": os.getenv("KAFKA_CONSUMER_GROUP", "log_processor_group"),
    "auto_offset_reset": "earliest",
    "enable_auto_commit": False,
    "max_poll_records": 500,
    "session_timeout_ms": 30000,
    "heartbeat_interval_ms": 10000,
}

# Log generation settings
KAFKA_LOG_BATCH_SIZE = int(os.getenv("KAFKA_LOG_BATCH_SIZE", "100"))
KAFKA_LOG_FLUSH_INTERVAL_MS = int(os.getenv("KAFKA_LOG_FLUSH_INTERVAL_MS", "5000"))

# Consumer processor settings
KAFKA_CONSUMER_POLL_TIMEOUT_MS = int(os.getenv("KAFKA_CONSUMER_POLL_TIMEOUT_MS", "1000"))
KAFKA_CONSUMER_BATCH_SIZE = int(os.getenv("KAFKA_CONSUMER_BATCH_SIZE", "1000"))
KAFKA_CONSUMER_ES_FLUSH_INTERVAL_S = int(os.getenv("KAFKA_CONSUMER_ES_FLUSH_INTERVAL_S", "5"))
