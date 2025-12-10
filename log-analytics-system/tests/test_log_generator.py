"""
Unit tests for the log generator module.
"""
import pytest
import json
from log_generator.generator import LogGenerator, generate_batch_logs


class TestLogGenerator:
    """Test cases for LogGenerator."""

    def test_log_generation(self):
        """Test that logs are generated with required fields."""
        generator = LogGenerator("test-service")
        log = generator.generate_log()

        # Check required fields
        assert "timestamp" in log
        assert "service_name" in log
        assert "level" in log
        assert "message" in log
        assert "request_id" in log
        assert "status_code" in log

        # Verify values
        assert log["service_name"] == "test-service"
        assert log["level"] in ["INFO", "WARN", "ERROR", "DEBUG"]
        assert isinstance(log["timestamp"], int)
        assert log["timestamp"] > 0

    def test_log_service_name(self):
        """Test that generated logs have correct service name."""
        service_name = "payment-service"
        generator = LogGenerator(service_name)
        log = generator.generate_log()

        assert log["service_name"] == service_name

    def test_log_level_distribution(self):
        """Test that log levels are generated."""
        generator = LogGenerator("test-service")
        levels = set()

        for _ in range(1000):
            log = generator.generate_log()
            levels.add(log["level"])

        # Should generate at least 2 different levels from a 1000 sample
        assert len(levels) >= 2

    def test_batch_generation(self):
        """Test batch log generation."""
        batch_size = 50
        logs = generate_batch_logs(batch_size=batch_size)

        assert len(logs) == batch_size
        for log in logs:
            assert "timestamp" in log
            assert "service_name" in log

    def test_batch_generation_with_custom_services(self):
        """Test batch generation with custom service list."""
        services = ["service-a", "service-b"]
        batch_size = 20
        logs = generate_batch_logs(batch_size=batch_size, services=services)

        assert len(logs) == batch_size
        for log in logs:
            assert log["service_name"] in services

    def test_logs_are_json_serializable(self):
        """Test that generated logs can be serialized to JSON."""
        logs = generate_batch_logs(batch_size=10)

        for log in logs:
            json_str = json.dumps(log)
            deserialized = json.loads(json_str)
            assert deserialized["service_name"] == log["service_name"]

    def test_status_code_based_on_level(self):
        """Test that status codes are appropriate for log level."""
        generator = LogGenerator("test-service")

        # Generate many logs and check status code patterns
        for _ in range(100):
            log = generator.generate_log()

            if log["level"] == "ERROR":
                assert log["status_code"] >= 400
            elif log["level"] == "INFO":
                assert log["status_code"] >= 200
                assert log["status_code"] < 400

    def test_error_message_for_error_level(self):
        """Test that ERROR level logs have error messages."""
        generator = LogGenerator("test-service")

        error_found = False
        for _ in range(100):
            log = generator.generate_log()
            if log["level"] == "ERROR":
                # Error logs should have messages related to errors
                assert isinstance(log["message"], str)
                assert len(log["message"]) > 0
                error_found = True

        # Should have found at least one error in 100 samples
        assert error_found
