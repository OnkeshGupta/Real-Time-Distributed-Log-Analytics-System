"""
Log generator main module.
Continuously generates and sends logs to Kafka.
"""
import asyncio
import json
import logging
import time
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from generator import generate_batch_logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class KafkaLogProducer:
    """Produces log events to Kafka."""

    def __init__(
        self,
        bootstrap_servers: list = None,
        topic: str = "logs_raw",
        batch_size: int = 100,
        flush_interval_ms: int = 5000,
    ):
        """
        Initialize the Kafka log producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers.
            topic: Kafka topic to produce to.
            batch_size: Number of logs to generate per batch.
            flush_interval_ms: Interval to flush logs to Kafka in milliseconds.
        """
        if bootstrap_servers is None:
            bootstrap_servers = ["kafka:9092"]

        self.topic = topic
        self.batch_size = batch_size
        self.flush_interval_s = flush_interval_ms / 1000.0

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                compression_type="snappy",
            )
            logger.info(f"Connected to Kafka: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send_logs(self, logs: list) -> int:
        """
        Send logs to Kafka.

        Args:
            logs: List of log entries to send.

        Returns:
            Number of logs successfully sent.
        """
        sent_count = 0
        for log in logs:
            try:
                future = self.producer.send(self.topic, value=log)
                # Wait for the send to complete
                record_metadata = future.get(timeout=10)
                sent_count += 1
                logger.debug(
                    f"Log sent to {record_metadata.topic} "
                    f"partition {record_metadata.partition} "
                    f"at offset {record_metadata.offset}"
                )
            except KafkaError as e:
                logger.error(f"Failed to send log to Kafka: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending log: {e}")

        return sent_count

    def run_continuous(self, num_batches: Optional[int] = None):
        """
        Run the producer continuously.

        Args:
            num_batches: Number of batches to generate. None = infinite.
        """
        batch_count = 0
        try:
            while num_batches is None or batch_count < num_batches:
                logs = generate_batch_logs(batch_size=self.batch_size)
                sent_count = self.send_logs(logs)
                batch_count += 1
                logger.info(
                    f"Batch {batch_count}: Generated and sent {sent_count}/{len(logs)} logs"
                )
                time.sleep(self.flush_interval_s)
        except KeyboardInterrupt:
            logger.info("Generator interrupted by user")
        finally:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")

    def close(self):
        """Close the producer."""
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka producer closed")


def main():
    """Main entry point for the log generator."""
    import os

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
    topic = os.getenv("KAFKA_TOPIC_LOGS_RAW", "logs_raw")
    batch_size = int(os.getenv("KAFKA_LOG_BATCH_SIZE", "100"))
    flush_interval_ms = int(os.getenv("KAFKA_LOG_FLUSH_INTERVAL_MS", "5000"))

    logger.info("Starting log generator...")
    producer = KafkaLogProducer(
        bootstrap_servers=bootstrap_servers,
        topic=topic,
        batch_size=batch_size,
        flush_interval_ms=flush_interval_ms,
    )
    producer.run_continuous()


if __name__ == "__main__":
    main()
