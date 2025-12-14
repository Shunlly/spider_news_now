"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    credentials,
    exports,
    news,
    proxies,
    scrapers,
    search,
    social,
)

# Create main API router
api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(scrapers.router)
api_router.include_router(news.router)
api_router.include_router(social.router)
api_router.include_router(search.router)
api_router.include_router(credentials.router)
api_router.include_router(proxies.router)
api_router.include_router(exports.router)
