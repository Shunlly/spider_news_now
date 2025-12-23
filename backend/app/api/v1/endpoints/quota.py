"""
配额 API 端点 - Quota API Endpoints
User Quota Management

提供配额管理接口：
- GET /quota - 获取当前用户配额信息
- GET /quota/usage - 获取配额使用统计

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.services.quota_service import quota_service

logger = get_logger(__name__)

router = APIRouter(prefix="/quota", tags=["配额管理"])


class QuotaResponse(BaseModel):
    """配额响应 Schema"""
    tier: str = Field(..., description="配额等级")
    daily_limit: int = Field(..., description="每日限额")
    daily_used: int = Field(..., description="今日已用")
    daily_remaining: int = Field(..., description="今日剩余")
    concurrent_limit: int = Field(..., description="并发限额")
    concurrent_used: int = Field(..., description="当前并发")
    concurrent_remaining: int = Field(..., description="剩余并发")
    reset_at: str | None = Field(None, description="重置时间")
    warning: bool = Field(False, description="是否显示配额警告")


@router.get(
    "",
    response_model=QuotaResponse,
    summary="获取配额信息",
    description="获取当前用户的配额使用情况"
)
async def get_quota(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> QuotaResponse:
    """
    获取当前用户配额信息

    返回：
    - tier: 配额等级（free, basic, pro）
    - daily_limit: 每日采集限额
    - daily_used: 今日已使用量
    - daily_remaining: 今日剩余配额
    - concurrent_limit: 并发任务限额
    - concurrent_used: 当前并发使用数
    - concurrent_remaining: 剩余可用并发数
    - reset_at: 配额重置时间
    - warning: 是否应显示配额警告（剩余<10%）
    """
    quota_info = await quota_service.get_quota_info(db, current_user.id)

    return QuotaResponse(
        tier=quota_info["tier"],
        daily_limit=quota_info["daily_limit"],
        daily_used=quota_info["daily_used"],
        daily_remaining=quota_info["daily_remaining"],
        concurrent_limit=quota_info["concurrent_limit"],
        concurrent_used=quota_info["concurrent_used"],
        concurrent_remaining=quota_info["concurrent_remaining"],
        reset_at=quota_info["reset_at"],
        warning=quota_info["warning"],
    )
