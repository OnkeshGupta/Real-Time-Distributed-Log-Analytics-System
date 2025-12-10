"""
Stress test script for the log analytics system.
Tests the system's ability to handle high log volumes.
"""
import time
import statistics
import sys
import os
from typing import List
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_generator.generator import generate_batch_logs
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_LOGS_RAW", "logs_raw")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
NUM_BATCHES = int(os.getenv("NUM_BATCHES", "100"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
NUM_THREADS = int(os.getenv("NUM_THREADS", "4"))
QUERY_THREADS = int(os.getenv("QUERY_THREADS", "2"))


class StressTestRunner:
    """Runs stress tests on the log analytics system."""

    def __init__(self):
        """Initialize the stress test runner."""
        self.total_logs_sent = 0
        self.total_logs_indexed = 0
        self.send_times: List[float] = []
        self.query_times: List[float] = []
        self.errors: List[str] = []

    def send_logs_batch(self, batch_num: int) -> tuple:
        """
        Send a batch of logs to Kafka.

        Args:
            batch_num: The batch number.

        Returns:
            Tuple of (success_count, time_taken).
        """
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                compression_type="snappy",
                request_timeout_ms=10000,
            )

            logs = generate_batch_logs(batch_size=BATCH_SIZE)
            start_time = time.time()

            for log in logs:
                try:
                    future = producer.send(KAFKA_TOPIC, value=log)
                    future.get(timeout=5)
                except KafkaError as e:
                    self.errors.append(f"Kafka error: {e}")

            producer.flush()
            producer.close()

            elapsed = time.time() - start_time
            self.send_times.append(elapsed)
            self.total_logs_sent += len(logs)

            print(f"Batch {batch_num}: Sent {len(logs)} logs in {elapsed:.2f}s")
            return len(logs), elapsed

        except Exception as e:
            error_msg = f"Batch {batch_num} error: {e}"
            self.errors.append(error_msg)
            print(f"ERROR: {error_msg}")
            return 0, 0

    def run_ingestion_test(self):
        """Run the ingestion stress test."""
        print("\n" + "=" * 60)
        print("INGESTION STRESS TEST")
        print("=" * 60)
        print(f"Config: {NUM_BATCHES} batches × {BATCH_SIZE} logs, {NUM_THREADS} threads")
        print(f"Target: {NUM_BATCHES * BATCH_SIZE:,} logs")
        print()

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for batch_num in range(NUM_BATCHES):
                future = executor.submit(self.send_logs_batch, batch_num)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.errors.append(f"Thread error: {e}")

        total_time = time.time() - start_time

        print()
        print("INGESTION RESULTS:")
        print(f"  Total logs sent: {self.total_logs_sent:,}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {self.total_logs_sent / total_time:.0f} logs/sec")
        print(f"  Avg batch send time: {statistics.mean(self.send_times):.2f}s")
        print(f"  Min batch send time: {min(self.send_times):.2f}s")
        print(f"  Max batch send time: {max(self.send_times):.2f}s")

        if self.errors:
            print(f"  Errors: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"    - {error}")

    def query_logs(self, query_num: int) -> float:
        """
        Query logs from the API.

        Args:
            query_num: The query number.

        Returns:
            Time taken for the query.
        """
        try:
            queries = [
                {"url": f"{API_BASE_URL}/logs", "name": "list_logs"},
                {"url": f"{API_BASE_URL}/logs?level=ERROR", "name": "filter_error"},
                {"url": f"{API_BASE_URL}/logs?anomaly=true", "name": "filter_anomaly"},
                {"url": f"{API_BASE_URL}/logs/stats", "name": "stats"},
            ]

            query = queries[query_num % len(queries)]

            start_time = time.time()
            response = requests.get(query["url"], timeout=10)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                self.query_times.append(elapsed)
                print(f"Query {query_num} ({query['name']}): {elapsed:.3f}s")
                return elapsed
            else:
                error_msg = f"Query {query_num} returned {response.status_code}"
                self.errors.append(error_msg)
                print(f"ERROR: {error_msg}")
                return 0

        except Exception as e:
            error_msg = f"Query {query_num} error: {e}"
            self.errors.append(error_msg)
            print(f"ERROR: {error_msg}")
            return 0

    def run_query_test(self, num_queries: int = 100):
        """
        Run the query stress test.

        Args:
            num_queries: Number of queries to execute.
        """
        print("\n" + "=" * 60)
        print("QUERY STRESS TEST")
        print("=" * 60)
        print(f"Config: {num_queries} queries, {QUERY_THREADS} threads")
        print()

        # Wait for some logs to be indexed
        print("Waiting 15 seconds for logs to be indexed...")
        time.sleep(15)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=QUERY_THREADS) as executor:
            futures = []
            for query_num in range(num_queries):
                future = executor.submit(self.query_logs, query_num)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.errors.append(f"Thread error: {e}")

        total_time = time.time() - start_time

        print()
        print("QUERY RESULTS:")
        print(f"  Total queries: {len(self.query_times)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {len(self.query_times) / total_time:.1f} queries/sec")
        print(f"  Avg query time: {statistics.mean(self.query_times):.3f}s")
        print(f"  Median query time: {statistics.median(self.query_times):.3f}s")
        print(f"  Min query time: {min(self.query_times):.3f}s")
        print(f"  Max query time: {max(self.query_times):.3f}s")
        print(f"  P95 query time: {sorted(self.query_times)[int(len(self.query_times) * 0.95)]:.3f}s")

        if self.errors:
            print(f"  Errors: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"    - {error}")

    def run_full_test(self):
        """Run the full stress test suite."""
        print("\n" + "=" * 60)
        print("LOG ANALYTICS SYSTEM - STRESS TEST SUITE")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Test ingestion
            self.run_ingestion_test()

            # Test queries
            self.run_query_test(num_queries=100)

            # Summary
            print("\n" + "=" * 60)
            print("FINAL SUMMARY")
            print("=" * 60)
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total errors: {len(self.errors)}")

            if self.total_logs_sent > 0:
                print(f"\nPerformance Targets:")
                throughput = self.total_logs_sent / statistics.mean(
                    [self.send_times[i] for i in range(len(self.send_times))]
                )
                print(f"  ✓ Ingestion throughput: {throughput:.0f} logs/sec (target: 50,000+)")
                if throughput >= 50000:
                    print(f"    TARGET MET!")

            if self.query_times:
                avg_query_time = statistics.mean(self.query_times)
                print(f"  ✓ Avg query time: {avg_query_time:.3f}s (target: <0.5s)")
                if avg_query_time < 0.5:
                    print(f"    TARGET MET!")

        except Exception as e:
            print(f"ERROR: Stress test failed: {e}")
            return False

        return len(self.errors) == 0


def main():
    """Main entry point for the stress test."""
    runner = StressTestRunner()
    success = runner.run_full_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
