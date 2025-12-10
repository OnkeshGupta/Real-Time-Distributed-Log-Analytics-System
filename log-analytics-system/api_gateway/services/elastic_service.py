"""
Elasticsearch service for API gateway.
Provides async and sync methods for querying Elasticsearch.
"""
import logging
from typing import Optional, Dict, Any
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log_processor.es_client import ElasticsearchClient
from configs.elastic_config import (
    ELASTIC_URL,
    ELASTIC_INDEX_NAME,
    ELASTIC_INDEX_MAPPING,
    ELASTIC_DEFAULT_PAGE_SIZE,
    ELASTIC_MAX_PAGE_SIZE,
)

logger = logging.getLogger(__name__)


class ElasticService:
    """Service for querying Elasticsearch."""

    _instance: Optional[ElasticsearchClient] = None

    @classmethod
    def get_client(cls) -> ElasticsearchClient:
        """
        Get or create the Elasticsearch client (singleton).

        Returns:
            The Elasticsearch client.
        """
        if cls._instance is None:
            try:
                cls._instance = ElasticsearchClient(
                    url=ELASTIC_URL,
                    index_name=ELASTIC_INDEX_NAME,
                    index_mapping=ELASTIC_INDEX_MAPPING,
                )
            except Exception as e:
                logger.error(f"Failed to create Elasticsearch client: {e}")
                raise
        return cls._instance

    @staticmethod
    def search_logs(
        service_name: Optional[str] = None,
        level: Optional[str] = None,
        status_code: Optional[int] = None,
        anomaly: Optional[bool] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        page: int = 1,
        size: int = ELASTIC_DEFAULT_PAGE_SIZE,
    ) -> Dict[str, Any]:
        """
        Search logs with filters.

        Args:
            service_name: Filter by service name.
            level: Filter by log level.
            status_code: Filter by status code.
            anomaly: Filter by anomaly flag.
            from_timestamp: Start timestamp in milliseconds.
            to_timestamp: End timestamp in milliseconds.
            page: Page number (1-indexed).
            size: Page size.

        Returns:
            Search results.
        """
        # Validate and clamp page size
        size = min(size, ELASTIC_MAX_PAGE_SIZE)
        size = max(size, 1)

        client = ElasticService.get_client()
        return client.search_with_filters(
            service_name=service_name,
            level=level,
            status_code=status_code,
            anomaly=anomaly,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            page=page,
            size=size,
        )

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """
        Get log statistics.

        Returns:
            Statistics dictionary.
        """
        client = ElasticService.get_client()
        return client.get_stats()

    @staticmethod
    def health_check() -> bool:
        """
        Check if Elasticsearch is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            client = ElasticService.get_client()
            return client.es.ping()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
