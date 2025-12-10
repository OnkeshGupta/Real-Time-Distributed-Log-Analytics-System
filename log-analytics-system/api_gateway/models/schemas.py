"""
Pydantic models for API requests and responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Model for a single log entry."""

    timestamp: int = Field(..., description="Timestamp in milliseconds")
    service_name: str = Field(..., description="Name of the service")
    level: str = Field(..., description="Log level (INFO, WARN, ERROR, DEBUG)")
    message: str = Field(..., description="Log message")
    request_id: str = Field(..., description="Request ID")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    user_id: Optional[str] = Field(None, description="User ID")
    path: Optional[str] = Field(None, description="Request path")
    method: Optional[str] = Field(None, description="HTTP method")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    anomaly: bool = Field(default=False, description="Whether this is an anomaly")
    severity_score: int = Field(default=0, description="Severity score 0-100")
    tags: List[str] = Field(default_factory=list, description="Tags for the log")


class LogSearchQuery(BaseModel):
    """Model for log search query parameters."""

    service_name: Optional[str] = None
    level: Optional[str] = None
    status_code: Optional[int] = None
    anomaly: Optional[bool] = None
    from_timestamp: Optional[int] = None
    to_timestamp: Optional[int] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    """Model for search results."""

    total: int = Field(..., description="Total number of hits")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    logs: List[Dict[str, Any]] = Field(..., description="List of log entries")


class LogStats(BaseModel):
    """Model for log statistics."""

    total_logs: int = Field(..., description="Total number of logs")
    services: Dict[str, int] = Field(..., description="Log count by service")
    levels: Dict[str, int] = Field(..., description="Log count by level")
    anomaly_count: int = Field(..., description="Total number of anomalies")
    error_count: int = Field(..., description="Total number of errors")


class HealthResponse(BaseModel):
    """Model for health check response."""

    status: str = Field(..., description="Health status")
    elasticsearch: str = Field(..., description="Elasticsearch connection status")
    timestamp: int = Field(..., description="Current timestamp in milliseconds")
