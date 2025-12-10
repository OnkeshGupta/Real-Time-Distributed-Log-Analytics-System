"""
Logs router.
Provides endpoints for querying and retrieving logs.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from models.schemas import SearchResult, LogStats
from services.elastic_service import ElasticService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=SearchResult)
async def search_logs(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARN, ERROR, DEBUG)"),
    status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    anomaly: Optional[bool] = Query(None, description="Filter by anomaly flag"),
    from_timestamp: Optional[int] = Query(None, description="Start timestamp in milliseconds"),
    to_timestamp: Optional[int] = Query(None, description="End timestamp in milliseconds"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Number of results per page"),
):
    """
    Search logs with optional filters.

    Query Parameters:
    - service_name: Filter by service name
    - level: Filter by log level
    - status_code: Filter by HTTP status code
    - anomaly: Filter by anomaly flag (true/false)
    - from_timestamp: Start timestamp in milliseconds
    - to_timestamp: End timestamp in milliseconds
    - page: Page number (default 1)
    - size: Results per page (default 20, max 100)

    Returns:
        SearchResult with log entries and pagination info.
    """
    try:
        results = ElasticService.search_logs(
            service_name=service_name,
            level=level,
            status_code=status_code,
            anomaly=anomaly,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            page=page,
            size=size,
        )

        # Extract and format results
        hits = results.get("hits", {})
        total = hits.get("total", {})
        if isinstance(total, dict):
            total_count = total.get("value", 0)
        else:
            total_count = total

        logs = [hit["_source"] for hit in hits.get("hits", [])]

        return SearchResult(
            total=total_count,
            page=page,
            size=size,
            logs=logs,
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats", response_model=LogStats)
async def get_log_stats():
    """
    Get statistics about the logs.

    Returns:
        LogStats with aggregated statistics.
    """
    try:
        stats = ElasticService.get_stats()
        return LogStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/anomalies", response_model=SearchResult)
async def search_anomalies(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    from_timestamp: Optional[int] = Query(None, description="Start timestamp in milliseconds"),
    to_timestamp: Optional[int] = Query(None, description="End timestamp in milliseconds"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Number of results per page"),
):
    """
    Search for anomalies in logs.

    Query Parameters:
    - service_name: Filter by service name
    - from_timestamp: Start timestamp in milliseconds
    - to_timestamp: End timestamp in milliseconds
    - page: Page number (default 1)
    - size: Results per page (default 20, max 100)

    Returns:
        SearchResult with anomalous log entries.
    """
    try:
        results = ElasticService.search_logs(
            service_name=service_name,
            anomaly=True,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            page=page,
            size=size,
        )

        # Extract and format results
        hits = results.get("hits", {})
        total = hits.get("total", {})
        if isinstance(total, dict):
            total_count = total.get("value", 0)
        else:
            total_count = total

        logs = [hit["_source"] for hit in hits.get("hits", [])]

        return SearchResult(
            total=total_count,
            page=page,
            size=size,
            logs=logs,
        )
    except Exception as e:
        logger.error(f"Anomaly search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly search failed: {str(e)}")
