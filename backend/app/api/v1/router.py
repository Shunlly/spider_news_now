"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    credentials,
    dashboard,
    data_pool,
    exports,
    health,
    news,
    proxies,
    quota,
    scrapers,
    search,
    social,
    telegram,
    twitter,
    users,
)

# Create main API router
api_router = APIRouter()

# 健康检查路由（优先注册，不需要认证）
api_router.include_router(health.router)

# 认证路由
api_router.include_router(auth.router)

# 用户管理路由（管理员）
api_router.include_router(users.router)

# 系统管理路由（超级管理员）
api_router.include_router(admin.router)

# Dashboard 路由
api_router.include_router(dashboard.router)

# 业务路由
api_router.include_router(scrapers.router)
api_router.include_router(news.router)
api_router.include_router(social.router)
api_router.include_router(search.router)
api_router.include_router(credentials.router)
api_router.include_router(proxies.router)
api_router.include_router(exports.router)
api_router.include_router(telegram.router)
api_router.include_router(twitter.router)
api_router.include_router(quota.router)
api_router.include_router(data_pool.router)
