"""
Log generator module.
Simulates multiple microservices emitting logs with realistic data.
"""
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service names to simulate
SERVICES = ["auth-service", "payment-service", "inventory-service", "user-service", "api-gateway"]

# HTTP methods
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

# Common paths
PATHS = [
    "/api/users",
    "/api/payments",
    "/api/inventory",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/orders",
    "/api/products",
    "/health",
    "/metrics",
]

# Log levels and their distribution
LOG_LEVELS = {
    "INFO": 0.60,
    "WARN": 0.25,
    "ERROR": 0.12,
    "DEBUG": 0.03,
}

# Error messages
ERROR_MESSAGES = [
    "Database connection timeout",
    "Authentication failed",
    "Invalid request payload",
    "Service unavailable",
    "Internal server error",
    "Rate limit exceeded",
    "Unauthorized access",
    "Resource not found",
]

# Info messages
INFO_MESSAGES = [
    "Request processed successfully",
    "User authenticated",
    "Payment processed",
    "Inventory updated",
    "Order created",
    "Cache hit",
]


class LogGenerator:
    """Generates realistic log entries for multiple microservices."""

    def __init__(self, service_name: str):
        """
        Initialize the log generator.

        Args:
            service_name: Name of the service to generate logs for.
        """
        self.service_name = service_name

    def generate_log(self) -> Dict[str, Any]:
        """
        Generate a single log entry.

        Returns:
            A dictionary containing a log entry.
        """
        level = self._choose_level()
        status_code = self._generate_status_code(level)
        timestamp = datetime.utcnow() - timedelta(seconds=random.randint(0, 300))

        log_entry = {
            "timestamp": int(timestamp.timestamp() * 1000),  # milliseconds
            "service_name": self.service_name,
            "level": level,
            "message": self._generate_message(level),
            "request_id": str(uuid.uuid4()),
            "status_code": status_code,
            "user_id": f"user_{random.randint(1000, 9999)}",
            "path": random.choice(PATHS),
            "method": random.choice(METHODS),
            "response_time_ms": random.randint(10, 5000),
            "error_code": self._generate_error_code(level),
            "tags": self._generate_tags(),
        }

        return log_entry

    def _choose_level(self) -> str:
        """Choose a log level based on distribution."""
        rand = random.random()
        cumulative = 0.0
        for level, probability in LOG_LEVELS.items():
            cumulative += probability
            if rand <= cumulative:
                return level
        return "INFO"

    def _generate_status_code(self, level: str) -> int:
        """Generate an HTTP status code based on log level."""
        if level == "ERROR":
            return random.choice([400, 401, 403, 404, 500, 502, 503])
        elif level == "WARN":
            return random.choice([200, 201, 204, 400, 429])
        else:
            return random.choice([200, 201, 204, 304])

    def _generate_message(self, level: str) -> str:
        """Generate a log message based on level."""
        if level in ("ERROR", "WARN"):
            return random.choice(ERROR_MESSAGES)
        else:
            return random.choice(INFO_MESSAGES)

    def _generate_error_code(self, level: str) -> str:
        """Generate an error code if applicable."""
        if level == "ERROR":
            return f"ERR_{random.randint(1000, 9999)}"
        return ""

    def _generate_tags(self) -> list:
        """Generate tags for the log entry."""
        available_tags = ["external_api", "database", "cache", "auth", "payment", "critical"]
        num_tags = random.randint(0, 3)
        return random.sample(available_tags, min(num_tags, len(available_tags)))


def generate_batch_logs(
    batch_size: int = 10, services: list = None
) -> list:
    """
    Generate a batch of log entries.

    Args:
        batch_size: Number of logs to generate.
        services: List of service names. Uses default if None.

    Returns:
        A list of log entries.
    """
    if services is None:
        services = SERVICES

    logs = []
    for _ in range(batch_size):
        service = random.choice(services)
        generator = LogGenerator(service)
        logs.append(generator.generate_log())

    return logs


if __name__ == "__main__":
    # Example: Generate and print 5 logs
    logs = generate_batch_logs(batch_size=5)
    for log in logs:
        print(json.dumps(log, indent=2))
