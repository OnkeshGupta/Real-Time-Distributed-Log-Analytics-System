"""
Unit tests for the API gateway endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_gateway.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test cases for health endpoint."""

    def test_health_check_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Log Analytics API"

    @patch("api_gateway.services.elastic_service.ElasticService.health_check")
    def test_health_endpoint_healthy(self, mock_health):
        """Test health endpoint when healthy."""
        mock_health.return_value = True

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["elasticsearch"] == "healthy"
        assert "timestamp" in data

    @patch("api_gateway.services.elastic_service.ElasticService.health_check")
    def test_health_endpoint_unhealthy(self, mock_health):
        """Test health endpoint when Elasticsearch is down."""
        mock_health.return_value = False

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["elasticsearch"] == "unhealthy"


class TestLogsEndpoint:
    """Test cases for logs endpoints."""

    @patch("api_gateway.services.elastic_service.ElasticService.search_logs")
    def test_search_logs_basic(self, mock_search):
        """Test basic logs search."""
        mock_search.return_value = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_source": {
                            "timestamp": 1000000,
                            "service_name": "test-service",
                            "level": "INFO",
                        }
                    },
                    {
                        "_source": {
                            "timestamp": 1000001,
                            "service_name": "test-service",
                            "level": "ERROR",
                        }
                    },
                ],
            }
        }

        response = client.get("/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["logs"]) == 2
        assert data["page"] == 1
        assert data["size"] == 20

    @patch("api_gateway.services.elastic_service.ElasticService.search_logs")
    def test_search_logs_with_filters(self, mock_search):
        """Test logs search with filters."""
        mock_search.return_value = {
            "hits": {"total": {"value": 1}, "hits": []},
        }

        response = client.get(
            "/logs?service_name=test-service&level=ERROR&page=1&size=10"
        )
        assert response.status_code == 200

        # Verify mock was called with correct parameters
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["service_name"] == "test-service"
        assert call_kwargs["level"] == "ERROR"

    @patch("api_gateway.services.elastic_service.ElasticService.get_stats")
    def test_stats_endpoint(self, mock_stats):
        """Test stats endpoint."""
        mock_stats.return_value = {
            "total_logs": 1000,
            "services": {"service-a": 500, "service-b": 500},
            "levels": {"INFO": 800, "ERROR": 200},
            "anomaly_count": 150,
            "error_count": 200,
        }

        response = client.get("/logs/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_logs"] == 1000
        assert data["anomaly_count"] == 150
        assert data["error_count"] == 200

    @patch("api_gateway.services.elastic_service.ElasticService.search_logs")
    def test_anomalies_endpoint(self, mock_search):
        """Test anomalies endpoint."""
        mock_search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "timestamp": 1000000,
                            "service_name": "test-service",
                            "level": "ERROR",
                            "anomaly": True,
                        }
                    }
                ],
            }
        }

        response = client.get("/logs/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["logs"]) == 1

        # Verify anomaly filter was used
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["anomaly"] is True

    @patch("api_gateway.services.elastic_service.ElasticService.search_logs")
    def test_search_page_size_limit(self, mock_search):
        """Test that page size is limited to max."""
        mock_search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
        }

        # Request size larger than max (100)
        response = client.get("/logs?size=200")
        assert response.status_code == 200

        # Verify size was clamped to max
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["size"] <= 100

    @patch("api_gateway.services.elastic_service.ElasticService.search_logs")
    def test_search_error_handling(self, mock_search):
        """Test error handling in search endpoint."""
        mock_search.side_effect = Exception("Elasticsearch connection error")

        response = client.get("/logs")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestModelValidation:
    """Test cases for Pydantic model validation."""

    def test_search_result_model(self):
        """Test SearchResult model validation."""
        from api_gateway.models.schemas import SearchResult

        data = {
            "total": 100,
            "page": 1,
            "size": 20,
            "logs": [{"timestamp": 1000, "service_name": "test"}],
        }

        result = SearchResult(**data)
        assert result.total == 100
        assert len(result.logs) == 1

    def test_log_stats_model(self):
        """Test LogStats model validation."""
        from api_gateway.models.schemas import LogStats

        data = {
            "total_logs": 1000,
            "services": {"service-a": 500},
            "levels": {"INFO": 700, "ERROR": 300},
            "anomaly_count": 150,
            "error_count": 300,
        }

        stats = LogStats(**data)
        assert stats.total_logs == 1000
        assert stats.anomaly_count == 150

    def test_health_response_model(self):
        """Test HealthResponse model validation."""
        from api_gateway.models.schemas import HealthResponse

        data = {
            "status": "healthy",
            "elasticsearch": "healthy",
            "timestamp": 1000000,
        }

        response = HealthResponse(**data)
        assert response.status == "healthy"
