"""
Anomaly detection module.
Implements simple anomaly detection rules for log entries.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in log entries based on simple rules."""

    # Anomaly detection rules
    ERROR_LEVEL_THRESHOLD = 1.0  # ERROR level always anomaly
    WARN_LEVEL_THRESHOLD = 0.5  # 50% of WARN are anomalies
    ERROR_STATUS_CODE_THRESHOLD = 400  # Status codes >= 400 are anomalies
    RESPONSE_TIME_THRESHOLD_MS = 3000  # Response time > 3s is anomaly

    @staticmethod
    def detect(log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies in a log entry.

        Args:
            log_entry: The log entry to analyze.

        Returns:
            The log entry with anomaly and severity_score fields added/updated.
        """
        is_anomaly = False
        severity_score = 0

        # Rule 1: ERROR level logs are anomalies
        if log_entry.get("level") == "ERROR":
            is_anomaly = True
            severity_score = 100

        # Rule 2: High status codes (>= 400) indicate errors
        status_code = log_entry.get("status_code", 200)
        if status_code >= 400:
            is_anomaly = True
            severity_score = max(severity_score, (status_code - 400) * 2 + 50)

        # Rule 3: WARN logs have a probability of being anomalies
        elif log_entry.get("level") == "WARN":
            import random

            if random.random() < AnomalyDetector.WARN_LEVEL_THRESHOLD:
                is_anomaly = True
                severity_score = max(severity_score, 50)

        # Rule 4: High response times are anomalies
        response_time = log_entry.get("response_time_ms", 0)
        if response_time > AnomalyDetector.RESPONSE_TIME_THRESHOLD_MS:
            is_anomaly = True
            severity_score = max(severity_score, 60)

        # Rule 5: Specific error codes indicate anomalies
        if log_entry.get("error_code"):
            is_anomaly = True
            severity_score = max(severity_score, 75)

        # Cap severity score at 100
        severity_score = min(severity_score, 100)

        # Add fields to log entry
        log_entry["anomaly"] = is_anomaly
        log_entry["severity_score"] = severity_score

        return log_entry

    @staticmethod
    def get_severity_level(score: int) -> str:
        """
        Get the severity level based on severity score.

        Args:
            score: The severity score (0-100).

        Returns:
            The severity level as a string.
        """
        if score >= 90:
            return "CRITICAL"
        elif score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        elif score >= 25:
            return "LOW"
        else:
            return "INFO"
