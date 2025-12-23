"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import TenantMiddleware
from app.core.rate_limit import RateLimitMiddleware

logger = get_logger(__name__)

# OpenAPI Tags for API Documentation
tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints for monitoring service status.",
    },
    {
        "name": "auth",
        "description": "Authentication endpoints for user login, logout, and token management.",
    },
    {
        "name": "news",
        "description": "News article management. List, filter, and retrieve scraped news articles.",
    },
    {
        "name": "search",
        "description": "Full-text search powered by Meilisearch. SLA: < 500ms response time.",
    },
    {
        "name": "scrapers",
        "description": "Scraper configuration and execution management.",
    },
    {
        "name": "social",
        "description": "Social media session and message management for Telegram and Twitter.",
    },
    {
        "name": "telegram",
        "description": "Telegram-specific operations and session management.",
    },
    {
        "name": "twitter",
        "description": "Twitter/X-specific operations and cookie-based session management.",
    },
    {
        "name": "credentials",
        "description": "Credential management for social media platforms with encryption.",
    },
    {
        "name": "proxies",
        "description": "Proxy server configuration for scraping operations.",
    },
    {
        "name": "exports",
        "description": "Data export operations. Export news and social data to CSV/JSON.",
    },
    {
        "name": "quota",
        "description": "API quota management and usage tracking.",
    },
    {
        "name": "Dashboard",
        "description": "Real-time dashboard statistics and WebSocket updates.",
    },
    {
        "name": "系统管理",
        "description": "System administration: tenant management, audit logs, system stats.",
    },
]


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
    from app.tasks.scraper_tasks import register_content_parser_job, register_scraper_jobs
    from app.tasks.social_tasks import register_social_fetch_job

    scheduler = await get_scheduler()

    try:
        async with scheduler:
            await scheduler.start_in_background()
            logger.info("APScheduler started")

            # Register scraper jobs
            await register_scraper_jobs()
            logger.info("Scraper scheduler initialized")

            # Register content parser job (every 5 minutes)
            await register_content_parser_job(interval_seconds=300)
            logger.info("Content parser scheduler initialized")

            # Register social data fetch job (every 10 minutes)
            await register_social_fetch_job(interval_seconds=600)
            logger.info("Social fetch scheduler initialized")

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
    description="""
## News Scraper SaaS Platform API

A comprehensive news scraping and social media monitoring platform.

### Features
- **News Scraping**: Automated scraping from multiple news sources
- **Full-text Search**: Meilisearch-powered search with < 500ms SLA
- **Social Monitoring**: Telegram and Twitter/X integration
- **Data Export**: Export to CSV/JSON formats
- **Proxy Management**: Built-in proxy rotation support

### Authentication
All endpoints (except health checks) require JWT authentication.
Use `/auth/login` to obtain tokens.

### Rate Limits
API endpoints are rate-limited. Check response headers for limits.
    """,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    contact={
        "name": "Spider News Now",
        "url": "https://github.com/shunlly/spider_news_now",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add tenant context middleware (multi-tenancy support)
app.add_middleware(TenantMiddleware)

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
