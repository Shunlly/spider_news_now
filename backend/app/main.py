"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting News Scraper API", extra={"version": settings.VERSION})
    setup_logging()

    # Start APScheduler with async context manager
    from app.tasks.scheduler import get_scheduler
    from app.tasks.scraper_tasks import register_scraper_jobs

    scheduler = await get_scheduler()

    try:
        async with scheduler:
            await scheduler.start_in_background()
            logger.info("APScheduler started")

            # Register scraper jobs
            await register_scraper_jobs()
            logger.info("Scraper scheduler initialized")

            yield

            # Shutdown happens automatically when exiting context manager
            logger.info("Shutting down News Scraper API")
    except* Exception as eg:
        # Handle ExceptionGroup from APScheduler shutdown gracefully
        for exc in eg.exceptions:
            logger.warning(f"Scheduler shutdown exception: {exc}")
        logger.info("Scheduler shutdown completed with warnings")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "News Scraper API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns service health status.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "components": {
            "api": "up",
            # Database health check will be added in Phase 2
            # Scheduler health check will be added in Phase 3
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
