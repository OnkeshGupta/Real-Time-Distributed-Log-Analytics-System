"""
Unit tests for the anomaly detector module.
"""
import pytest
from log_processor.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Test cases for AnomalyDetector."""

    def test_error_level_is_anomaly(self):
        """Test that ERROR level logs are marked as anomalies."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "ERROR",
            "message": "An error occurred",
            "request_id": "req123",
            "status_code": 500,
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["anomaly"] is True
        assert result["severity_score"] >= 90

    def test_high_status_code_is_anomaly(self):
        """Test that high status codes (>= 400) are marked as anomalies."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "INFO",
            "message": "Request failed",
            "request_id": "req123",
            "status_code": 404,
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["anomaly"] is True
        assert result["severity_score"] > 0

    def test_info_level_is_not_anomaly(self):
        """Test that INFO level logs are not marked as anomalies (usually)."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "INFO",
            "message": "Request processed successfully",
            "request_id": "req123",
            "status_code": 200,
            "response_time_ms": 100,
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["anomaly"] is False
        assert result["severity_score"] == 0

    def test_high_response_time_is_anomaly(self):
        """Test that high response times are marked as anomalies."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "INFO",
            "message": "Request processed",
            "request_id": "req123",
            "status_code": 200,
            "response_time_ms": 5000,  # > 3000ms threshold
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["anomaly"] is True
        assert result["severity_score"] > 0

    def test_error_code_is_anomaly(self):
        """Test that logs with error codes are marked as anomalies."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "WARN",
            "message": "Warning",
            "request_id": "req123",
            "status_code": 200,
            "error_code": "ERR_5001",
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["anomaly"] is True
        assert result["severity_score"] > 0

    def test_severity_score_capped_at_100(self):
        """Test that severity score is capped at 100."""
        log_entry = {
            "timestamp": 1000000,
            "service_name": "test-service",
            "level": "ERROR",
            "message": "Error",
            "request_id": "req123",
            "status_code": 500,
            "response_time_ms": 5000,
            "error_code": "ERR_5001",
        }

        result = AnomalyDetector.detect(log_entry)

        assert result["severity_score"] <= 100

    def test_severity_level_critical(self):
        """Test severity level classification - CRITICAL."""
        assert AnomalyDetector.get_severity_level(95) == "CRITICAL"

    def test_severity_level_high(self):
        """Test severity level classification - HIGH."""
        assert AnomalyDetector.get_severity_level(75) == "HIGH"

    def test_severity_level_medium(self):
        """Test severity level classification - MEDIUM."""
        assert AnomalyDetector.get_severity_level(60) == "MEDIUM"

    def test_severity_level_low(self):
        """Test severity level classification - LOW."""
        assert AnomalyDetector.get_severity_level(30) == "LOW"

    def test_severity_level_info(self):
        """Test severity level classification - INFO."""
        assert AnomalyDetector.get_severity_level(5) == "INFO"
