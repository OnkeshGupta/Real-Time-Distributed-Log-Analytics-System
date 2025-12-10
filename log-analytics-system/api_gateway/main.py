"""
FastAPI main application.
Serves as the API gateway for the log analytics system.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import health, logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Log Analytics API",
    description="Real-time distributed log analytics system API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(logs.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Log Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "logs": "/logs",
            "stats": "/logs/stats",
            "anomalies": "/logs/anomalies",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("API Gateway starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("API Gateway shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
