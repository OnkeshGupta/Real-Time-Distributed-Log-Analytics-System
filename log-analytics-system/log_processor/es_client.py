"""
Elasticsearch client module.
Provides utilities for interacting with Elasticsearch.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError, ConnectionError

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Client for interacting with Elasticsearch."""

    def __init__(
        self,
        url: str = "http://elasticsearch:9200",
        index_name: str = "logs-index",
        index_mapping: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Elasticsearch client.

        Args:
            url: Elasticsearch URL.
            index_name: Name of the index.
            index_mapping: Index mapping configuration.
        """
        self.url = url
        self.index_name = index_name
        self.index_mapping = index_mapping

        try:
            self.es = Elasticsearch([url], timeout=30)
            if self.es.ping():
                logger.info(f"Connected to Elasticsearch at {url}")
            else:
                logger.warning("Could not ping Elasticsearch")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    def create_index(self, force: bool = False) -> bool:
        """
        Create the index if it doesn't exist.

        Args:
            force: If True, delete and recreate the index.

        Returns:
            True if index was created or already exists, False otherwise.
        """
        try:
            if force and self.es.indices.exists(index=self.index_name):
                logger.info(f"Deleting existing index: {self.index_name}")
                self.es.indices.delete(index=self.index_name)

            if not self.es.indices.exists(index=self.index_name):
                if self.index_mapping:
                    self.es.indices.create(index=self.index_name, body=self.index_mapping)
                else:
                    self.es.indices.create(index=self.index_name)
                logger.info(f"Created index: {self.index_name}")
            else:
                logger.info(f"Index already exists: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    def bulk_index(self, documents: List[Dict[str, Any]]) -> tuple:
        """
        Bulk index documents into Elasticsearch.

        Args:
            documents: List of documents to index.

        Returns:
            Tuple of (successful_count, failed_count).
        """
        try:
            actions = [
                {"_index": self.index_name, "_source": doc} for doc in documents
            ]
            success, failed = bulk(
                self.es, actions, chunk_size=1000, raise_on_error=False
            )
            logger.info(
                f"Bulk indexing completed: {success} successful, {len(failed)} failed"
            )
            if failed:
                logger.warning(f"Failed documents: {failed}")
            return success, len(failed)
        except Exception as e:
            logger.error(f"Failed to bulk index documents: {e}")
            return 0, len(documents)

    def search(
        self,
        query: Dict[str, Any],
        size: int = 20,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for documents in Elasticsearch.

        Args:
            query: Elasticsearch query DSL.
            size: Number of results to return.
            from_: Offset for pagination.

        Returns:
            Search results.
        """
        try:
            results = self.es.search(
                index=self.index_name,
                body={"query": query, "size": size, "from": from_},
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search Elasticsearch: {e}")
            return {"hits": {"total": 0, "hits": []}}

    def search_with_filters(
        self,
        service_name: Optional[str] = None,
        level: Optional[str] = None,
        status_code: Optional[int] = None,
        anomaly: Optional[bool] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search with common filters.

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
        must_clauses = []

        if service_name:
            must_clauses.append({"term": {"service_name": service_name}})

        if level:
            must_clauses.append({"term": {"level": level}})

        if status_code is not None:
            must_clauses.append({"term": {"status_code": status_code}})

        if anomaly is not None:
            must_clauses.append({"term": {"anomaly": anomaly}})

        if from_timestamp or to_timestamp:
            range_clause = {}
            if from_timestamp:
                range_clause["gte"] = from_timestamp
            if to_timestamp:
                range_clause["lte"] = to_timestamp
            if range_clause:
                must_clauses.append({"range": {"timestamp": range_clause}})

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

        from_ = (page - 1) * size
        return self.search(query, size=size, from_=from_)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about the logs.

        Returns:
            Dictionary containing statistics.
        """
        try:
            # Total count
            total_count_result = self.es.count(index=self.index_name)
            total_count = total_count_result.get("count", 0)

            # Aggregations
            agg_query = {
                "size": 0,
                "aggs": {
                    "services": {
                        "terms": {"field": "service_name", "size": 100}
                    },
                    "levels": {
                        "terms": {"field": "level", "size": 100}
                    },
                    "anomalies": {
                        "filter": {"term": {"anomaly": True}},
                        "aggs": {
                            "count": {"value_count": {"field": "_id"}}
                        },
                    },
                    "errors": {
                        "filter": {
                            "range": {"status_code": {"gte": 400}}
                        },
                        "aggs": {
                            "count": {"value_count": {"field": "_id"}}
                        },
                    },
                },
            }

            results = self.es.search(index=self.index_name, body=agg_query)

            stats = {
                "total_logs": total_count,
                "services": {},
                "levels": {},
                "anomaly_count": 0,
                "error_count": 0,
            }

            # Process aggregations
            aggs = results.get("aggregations", {})

            for service_bucket in aggs.get("services", {}).get("buckets", []):
                stats["services"][service_bucket["key"]] = service_bucket["doc_count"]

            for level_bucket in aggs.get("levels", {}).get("buckets", []):
                stats["levels"][level_bucket["key"]] = level_bucket["doc_count"]

            stats["anomaly_count"] = (
                aggs.get("anomalies", {})
                .get("aggs", {})
                .get("count", {})
                .get("value", 0)
            )
            stats["error_count"] = (
                aggs.get("errors", {})
                .get("aggs", {})
                .get("count", {})
                .get("value", 0)
            )

            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_logs": 0,
                "services": {},
                "levels": {},
                "anomaly_count": 0,
                "error_count": 0,
            }

    def close(self):
        """Close the Elasticsearch connection."""
        if hasattr(self, "es"):
            self.es.close()
            logger.info("Elasticsearch connection closed")
