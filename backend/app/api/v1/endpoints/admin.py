"""
管理员 API 端点 - Admin API Endpoints
T113: Tenant admin endpoints
T163: Audit logs endpoint

提供系统管理功能：
- 租户管理 (CRUD)
- 审计日志查询
- 系统统计

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_super_admin
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["系统管理"])


# =============================================================
# 请求/响应模型
# =============================================================


class TenantCreateRequest(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=2, max_length=100, description="租户名称（唯一）")
    display_name: str | None = Field(None, max_length=200, description="显示名称")
    quota_config: dict | None = Field(
        default={"daily_limit": 1000, "concurrent_limit": 5},
        description="配额配置"
    )
    settings: dict | None = Field(default={}, description="租户设置")


class TenantUpdateRequest(BaseModel):
    """更新租户请求"""
    name: str | None = Field(None, min_length=2, max_length=100, description="租户名称")
    display_name: str | None = Field(None, max_length=200, description="显示名称")
    quota_config: dict | None = Field(None, description="配额配置")
    settings: dict | None = Field(None, description="租户设置")
    is_active: bool | None = Field(None, description="是否激活")


class TenantResponse(BaseModel):
    """租户响应"""
    id: int = Field(..., description="租户 ID")
    name: str = Field(..., description="租户名称")
    display_name: str | None = Field(None, description="显示名称")
    quota_config: dict = Field(..., description="配额配置")
    settings: dict = Field(..., description="租户设置")
    is_active: bool = Field(..., description="是否激活")
    user_count: int = Field(0, description="用户数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    """租户列表响应"""
    tenants: list[TenantResponse]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    """消息响应"""
    message: str


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    total_tenants: int = Field(..., description="租户总数")
    active_tenants: int = Field(..., description="活跃租户数")
    total_users: int = Field(..., description="用户总数")
    active_users: int = Field(..., description="活跃用户数")
    timestamp: datetime = Field(..., description="统计时间")


# =============================================================
# 租户管理端点
# =============================================================


@router.get(
    "/tenants",
    response_model=TenantListResponse,
    summary="获取租户列表",
    description="超级管理员获取所有租户列表"
)
async def list_tenants(
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, description="搜索关键词"),
    is_active: bool | None = Query(None, description="按激活状态筛选"),
) -> TenantListResponse:
    """
    获取租户列表

    权限要求：超级管理员
    """
    # 构建查询
    stmt = select(Tenant)

    # 搜索条件
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            Tenant.name.ilike(search_filter) |
            Tenant.display_name.ilike(search_filter)
        )

    # 激活状态筛选
    if is_active is not None:
        stmt = stmt.where(Tenant.is_active == is_active)

    # 统计总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Tenant.id.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    tenants = result.scalars().all()

    # 获取每个租户的用户数
    tenant_responses = []
    for tenant in tenants:
        user_count_stmt = select(func.count()).select_from(User).where(User.tenant_id == tenant.id)
        user_count_result = await db.execute(user_count_stmt)
        user_count = user_count_result.scalar() or 0

        tenant_dict = {
            "id": tenant.id,
            "name": tenant.name,
            "display_name": tenant.display_name,
            "quota_config": tenant.quota_config,
            "settings": tenant.settings,
            "is_active": tenant.is_active,
            "user_count": user_count,
            "created_at": tenant.created_at,
            "updated_at": tenant.updated_at,
        }
        tenant_responses.append(TenantResponse(**tenant_dict))

    return TenantListResponse(
        tenants=tenant_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建租户",
    description="超级管理员创建新租户"
)
async def create_tenant(
    request: TenantCreateRequest,
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    创建租户

    权限要求：超级管理员
    """
    # 检查租户名是否已存在
    existing_stmt = select(Tenant).where(Tenant.name == request.name)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="租户名称已存在"
        )

    # 创建租户
    tenant = Tenant(
        name=request.name,
        display_name=request.display_name,
        quota_config=request.quota_config or {"daily_limit": 1000, "concurrent_limit": 5},
        settings=request.settings or {},
        is_active=True,
    )

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    logger.info("Tenant created", extra={
        "admin_id": admin.id,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
    })

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        display_name=tenant.display_name,
        quota_config=tenant.quota_config,
        settings=tenant.settings,
        is_active=tenant.is_active,
        user_count=0,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="获取租户详情",
    description="超级管理员获取指定租户详情"
)
async def get_tenant(
    tenant_id: int,
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    获取租户详情

    权限要求：超级管理员
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="租户不存在"
        )

    # 获取用户数
    user_count_stmt = select(func.count()).select_from(User).where(User.tenant_id == tenant.id)
    user_count_result = await db.execute(user_count_stmt)
    user_count = user_count_result.scalar() or 0

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        display_name=tenant.display_name,
        quota_config=tenant.quota_config,
        settings=tenant.settings,
        is_active=tenant.is_active,
        user_count=user_count,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.put(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    summary="更新租户",
    description="超级管理员更新租户信息"
)
async def update_tenant(
    tenant_id: int,
    request: TenantUpdateRequest,
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    更新租户信息

    权限要求：超级管理员
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="租户不存在"
        )

    # 检查名称冲突
    if request.name and request.name != tenant.name:
        existing_stmt = select(Tenant).where(Tenant.name == request.name)
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="租户名称已存在"
            )
        tenant.name = request.name

    # 更新字段
    if request.display_name is not None:
        tenant.display_name = request.display_name
    if request.quota_config is not None:
        tenant.quota_config = request.quota_config
    if request.settings is not None:
        tenant.settings = request.settings
    if request.is_active is not None:
        tenant.is_active = request.is_active

    await db.commit()
    await db.refresh(tenant)

    # 获取用户数
    user_count_stmt = select(func.count()).select_from(User).where(User.tenant_id == tenant.id)
    user_count_result = await db.execute(user_count_stmt)
    user_count = user_count_result.scalar() or 0

    logger.info("Tenant updated", extra={
        "admin_id": admin.id,
        "tenant_id": tenant.id,
    })

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        display_name=tenant.display_name,
        quota_config=tenant.quota_config,
        settings=tenant.settings,
        is_active=tenant.is_active,
        user_count=user_count,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.delete(
    "/tenants/{tenant_id}",
    response_model=MessageResponse,
    summary="删除租户",
    description="超级管理员删除租户（会同时删除该租户下所有用户和数据）"
)
async def delete_tenant(
    tenant_id: int,
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
    force: bool = Query(False, description="强制删除（即使有用户）"),
) -> MessageResponse:
    """
    删除租户

    权限要求：超级管理员

    注意：删除租户会级联删除所有相关数据！
    """
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="租户不存在"
        )

    # 检查是否有用户
    user_count_stmt = select(func.count()).select_from(User).where(User.tenant_id == tenant.id)
    user_count_result = await db.execute(user_count_stmt)
    user_count = user_count_result.scalar() or 0

    if user_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"租户下有 {user_count} 个用户，请先删除用户或使用 force=true 强制删除"
        )

    tenant_name = tenant.name
    await db.delete(tenant)
    await db.commit()

    logger.warning("Tenant deleted", extra={
        "admin_id": admin.id,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "force": force,
        "deleted_users": user_count,
    })

    return MessageResponse(message=f"租户 '{tenant_name}' 已删除")


# =============================================================
# 系统统计端点
# =============================================================


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="获取系统统计",
    description="超级管理员获取系统整体统计数据"
)
async def get_system_stats(
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
) -> SystemStatsResponse:
    """
    获取系统统计

    权限要求：超级管理员
    """
    # 租户统计
    total_tenants_stmt = select(func.count()).select_from(Tenant)
    total_tenants_result = await db.execute(total_tenants_stmt)
    total_tenants = total_tenants_result.scalar() or 0

    active_tenants_stmt = select(func.count()).select_from(Tenant).where(Tenant.is_active == True)  # noqa: E712
    active_tenants_result = await db.execute(active_tenants_stmt)
    active_tenants = active_tenants_result.scalar() or 0

    # 用户统计
    total_users_stmt = select(func.count()).select_from(User)
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar() or 0

    active_users_stmt = select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
    active_users_result = await db.execute(active_users_stmt)
    active_users = active_users_result.scalar() or 0

    return SystemStatsResponse(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_users=total_users,
        active_users=active_users,
        timestamp=datetime.now(),
    )


# =============================================================
# 审计日志端点 (T163)
# =============================================================


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    user_id: str | None
    username: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="获取审计日志",
    description="超级管理员获取系统审计日志"
)
async def list_audit_logs(
    admin: Annotated[User, Depends(require_super_admin())],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    user_id: str | None = Query(None, description="按用户 ID 筛选"),
    action: str | None = Query(None, description="按操作类型筛选"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
) -> AuditLogListResponse:
    """
    获取审计日志

    权限要求：超级管理员
    """
    from app.models.audit import AuditLog

    # 构建查询
    stmt = select(AuditLog)

    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    # 统计总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    # 获取用户名
    log_responses = []
    for log in logs:
        username = None
        if log.user_id:
            user_stmt = select(User.username).where(User.id == log.user_id)
            user_result = await db.execute(user_stmt)
            username = user_result.scalar_one_or_none()

        log_responses.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        ))

    return AuditLogListResponse(
        logs=log_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================
# 系统指标端点 (T164)
# =============================================================


class TaskQueueMetricsResponse(BaseModel):
    """任务队列指标响应"""
    pending: int = Field(..., description="等待中的任务数")
    running: int = Field(..., description="运行中的任务数")
    completed: int = Field(..., description="已完成的任务数")
    failed: int = Field(..., description="失败的任务数")
    total: int = Field(..., description="总任务数")


class ProcessingRateMetricsResponse(BaseModel):
    """处理速率指标响应"""
    articles_per_minute: float = Field(..., description="每分钟采集文章数")
    articles_per_hour: float = Field(..., description="每小时采集文章数")
    tasks_per_minute: float = Field(..., description="每分钟完成任务数")
    tasks_per_hour: float = Field(..., description="每小时完成任务数")
    avg_task_duration_seconds: float = Field(..., description="平均任务时长（秒）")


class ResourceMetricsResponse(BaseModel):
    """资源使用指标响应"""
    active_scrapers: int = Field(..., description="活跃爬虫数")
    total_scrapers: int = Field(..., description="爬虫总数")
    active_connections: int = Field(..., description="活跃 WebSocket 连接数")
    db_connections: int = Field(..., description="数据库连接数")
    memory_usage_mb: float = Field(..., description="内存使用（MB）")


class SystemMetricsResponse(BaseModel):
    """系统指标响应"""
    timestamp: datetime = Field(..., description="时间戳")
    uptime_seconds: float = Field(..., description="系统运行时长（秒）")
    task_queue: TaskQueueMetricsResponse = Field(..., description="任务队列指标")
    processing_rate: ProcessingRateMetricsResponse = Field(..., description="处理速率指标")
    resources: ResourceMetricsResponse = Field(..., description="资源使用指标")


class HealthStatusResponse(BaseModel):
    """健康状态响应"""
    status: str = Field(..., description="健康状态: healthy, degraded, unhealthy")
    issues: list[str] = Field(default_factory=list, description="问题列表")
    counters: dict = Field(default_factory=dict, description="计数器")


@router.get(
    "/metrics",
    response_model=SystemMetricsResponse,
    summary="获取系统指标",
    description="超级管理员获取系统运行指标"
)
async def get_system_metrics(
    admin: Annotated[User, Depends(require_super_admin())],
) -> SystemMetricsResponse:
    """
    获取系统指标

    权限要求：超级管理员

    返回：
    - task_queue: 任务队列状态
    - processing_rate: 处理速率
    - resources: 资源使用情况
    """
    from app.services.metrics_service import metrics_service

    metrics = await metrics_service.get_metrics()

    return SystemMetricsResponse(
        timestamp=metrics.timestamp,
        uptime_seconds=metrics.uptime_seconds,
        task_queue=TaskQueueMetricsResponse(**metrics.task_queue.model_dump()),
        processing_rate=ProcessingRateMetricsResponse(**metrics.processing_rate.model_dump()),
        resources=ResourceMetricsResponse(**metrics.resources.model_dump()),
    )


@router.get(
    "/health",
    response_model=HealthStatusResponse,
    summary="获取系统健康状态",
    description="超级管理员获取系统健康状态"
)
async def get_system_health(
    admin: Annotated[User, Depends(require_super_admin())],
) -> HealthStatusResponse:
    """
    获取系统健康状态

    权限要求：超级管理员
    """
    from app.services.metrics_service import metrics_service

    health = metrics_service.get_health_status()

    return HealthStatusResponse(
        status=health["status"],
        issues=health["issues"],
        counters=health["counters"],
    )
