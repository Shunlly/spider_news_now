"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import scrapers, news

# Create main API router
api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(scrapers.router)
api_router.include_router(news.router)
