"""
Health check router.
"""
import logging
import time
from fastapi import APIRouter, HTTPException

from models.schemas import HealthResponse
from services.elastic_service import ElasticService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Check the health of the API and its dependencies.

    Returns:
        HealthResponse with status and component health.
    """
    try:
        elasticsearch_status = "healthy" if ElasticService.health_check() else "unhealthy"

        overall_status = "healthy" if elasticsearch_status == "healthy" else "degraded"

        return HealthResponse(
            status=overall_status,
            elasticsearch=elasticsearch_status,
            timestamp=int(time.time() * 1000),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
