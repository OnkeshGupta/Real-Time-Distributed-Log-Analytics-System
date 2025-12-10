"""
Log processor main module.
Consumes logs from Kafka, processes them, and indexes to Elasticsearch.
"""
import asyncio
import json
import logging
import time
from typing import Optional, List, Dict, Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from anomaly_detector import AnomalyDetector
from es_client import ElasticsearchClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LogProcessor:
    """Processes logs from Kafka and indexes them to Elasticsearch."""

    def __init__(
        self,
        kafka_bootstrap_servers: List[str] = None,
        kafka_topic: str = "logs_raw",
        kafka_group_id: str = "log_processor_group",
        elasticsearch_url: str = "http://elasticsearch:9200",
        elasticsearch_index: str = "logs-index",
        elasticsearch_mapping: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
        flush_interval_s: float = 5,
        poll_timeout_ms: int = 1000,
    ):
        """
        Initialize the log processor.

        Args:
            kafka_bootstrap_servers: Kafka bootstrap servers.
            kafka_topic: Kafka topic to consume from.
            kafka_group_id: Kafka consumer group ID.
            elasticsearch_url: Elasticsearch URL.
            elasticsearch_index: Elasticsearch index name.
            elasticsearch_mapping: Elasticsearch index mapping.
            batch_size: Number of logs to batch before indexing.
            flush_interval_s: Interval to flush logs to ES in seconds.
            poll_timeout_ms: Kafka poll timeout in milliseconds.
        """
        if kafka_bootstrap_servers is None:
            kafka_bootstrap_servers = ["kafka:9092"]

        self.batch_size = batch_size
        self.flush_interval_s = flush_interval_s
        self.poll_timeout_ms = poll_timeout_ms
        self.batch: List[Dict[str, Any]] = []
        self.last_flush_time = time.time()

        # Initialize Kafka consumer
        try:
            self.consumer = KafkaConsumer(
                kafka_topic,
                bootstrap_servers=kafka_bootstrap_servers,
                group_id=kafka_group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                max_poll_records=500,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info(f"Connected to Kafka topic: {kafka_topic}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

        # Initialize Elasticsearch client
        try:
            self.es_client = ElasticsearchClient(
                url=elasticsearch_url,
                index_name=elasticsearch_index,
                index_mapping=elasticsearch_mapping,
            )
            self.es_client.create_index()
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}")
            raise

    def process_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single log entry.

        Args:
            log_entry: The raw log entry.

        Returns:
            The processed log entry.
        """
        try:
            # Normalize timestamp if needed (already in ms)
            if "timestamp" not in log_entry:
                import time

                log_entry["timestamp"] = int(time.time() * 1000)

            # Detect anomalies
            log_entry = AnomalyDetector.detect(log_entry)

            # Validate required fields
            required_fields = ["timestamp", "service_name", "level", "message"]
            for field in required_fields:
                if field not in log_entry:
                    logger.warning(f"Missing required field: {field} in log: {log_entry}")
                    log_entry[field] = "unknown"

            return log_entry
        except Exception as e:
            logger.error(f"Failed to process log: {e}")
            return None

    def flush_batch(self) -> int:
        """
        Flush the current batch to Elasticsearch.

        Returns:
            Number of logs successfully indexed.
        """
        if not self.batch:
            return 0

        try:
            success_count, failed_count = self.es_client.bulk_index(self.batch)
            logger.info(
                f"Flushed batch: {success_count} successful, {failed_count} failed"
            )
            self.batch = []
            self.last_flush_time = time.time()
            return success_count
        except Exception as e:
            logger.error(f"Failed to flush batch to Elasticsearch: {e}")
            return 0

    def run(self, num_messages: Optional[int] = None):
        """
        Run the processor continuously.

        Args:
            num_messages: Number of messages to process. None = infinite.
        """
        processed_count = 0
        try:
            while num_messages is None or processed_count < num_messages:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=self.poll_timeout_ms)

                if not messages:
                    # Check if we need to flush based on time
                    if (
                        self.batch
                        and time.time() - self.last_flush_time > self.flush_interval_s
                    ):
                        logger.info(
                            f"Flushing batch due to time interval (size: {len(self.batch)})"
                        )
                        self.flush_batch()
                    continue

                # Process messages
                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            log_entry = message.value
                            processed_log = self.process_log(log_entry)
                            if processed_log:
                                self.batch.append(processed_log)
                                processed_count += 1

                                # Flush if batch is full
                                if len(self.batch) >= self.batch_size:
                                    logger.info(
                                        f"Flushing batch due to size (size: {len(self.batch)})"
                                    )
                                    self.flush_batch()

                                if processed_count % 1000 == 0:
                                    logger.info(
                                        f"Processed {processed_count} messages so far"
                                    )
                        except Exception as e:
                            logger.error(f"Failed to process message: {e}")

                    # Commit offsets after processing
                    try:
                        self.consumer.commit()
                    except Exception as e:
                        logger.error(f"Failed to commit offsets: {e}")

                # Flush if time interval exceeded
                if (
                    self.batch
                    and time.time() - self.last_flush_time > self.flush_interval_s
                ):
                    logger.info(
                        f"Flushing batch due to time interval (size: {len(self.batch)})"
                    )
                    self.flush_batch()

        except KeyboardInterrupt:
            logger.info("Processor interrupted by user")
        finally:
            # Flush any remaining messages
            if self.batch:
                logger.info(f"Flushing remaining batch (size: {len(self.batch)})")
                self.flush_batch()

            self.close()

    def close(self):
        """Close the processor."""
        self.consumer.close()
        self.es_client.close()
        logger.info("Log processor closed")


def main():
    """Main entry point for the log processor."""
    import os
    import sys

    from configs.kafka_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_LOGS_RAW
    from configs.elastic_config import (
        ELASTIC_URL,
        ELASTIC_INDEX_NAME,
        ELASTIC_INDEX_MAPPING,
        ELASTIC_BULK_SIZE,
        ELASTIC_BULK_TIMEOUT_S,
    )

    # Update module path to include parent directory for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info("Starting log processor...")

    processor = LogProcessor(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC_LOGS_RAW,
        elasticsearch_url=ELASTIC_URL,
        elasticsearch_index=ELASTIC_INDEX_NAME,
        elasticsearch_mapping=ELASTIC_INDEX_MAPPING,
        batch_size=ELASTIC_BULK_SIZE,
        flush_interval_s=ELASTIC_BULK_TIMEOUT_S,
    )

    processor.run()


if __name__ == "__main__":
    main()
