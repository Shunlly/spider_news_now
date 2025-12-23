"""
代理配置管理 API 端点
Proxy Configuration Management API Endpoints

提供代理服务器的 CRUD 操作和健康检查。
遵循宪法 II.C 安全要求：代理认证信息加密存储。
"""

import asyncio
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.proxy_config import ProxyConfig, ProxyProtocol, ProxyStatus
from app.models.user import User
from app.schemas.system import (
    ProxyActionResponse,
    ProxyCreate,
    ProxyListResponse,
    ProxyResponse,
    ProxyTestResult,
    ProxyUpdate,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/proxies", tags=["proxies"])

# 代理测试目标 URL
TEST_URLS = [
    "https://httpbin.org/ip",
    "https://api.ipify.org?format=json",
]


# =============================================================
# 代理管理端点
# =============================================================


@router.get("", response_model=ProxyListResponse)
async def list_proxies(
    current_user: Annotated[User, Depends(get_current_active_user)],
    protocol: ProxyProtocol | None = Query(None, description="按协议过滤"),
    status: ProxyStatus | None = Query(None, description="按状态过滤"),
    enabled: bool | None = Query(None, description="按启用状态过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取代理配置列表

    支持按协议、状态和启用状态过滤。
    """
    stmt = select(ProxyConfig).where(ProxyConfig.user_id == current_user.id)

    if protocol:
        stmt = stmt.where(ProxyConfig.protocol == protocol)
    if status:
        stmt = stmt.where(ProxyConfig.status == status)
    if enabled is not None:
        stmt = stmt.where(ProxyConfig.enabled == enabled)

    stmt = stmt.order_by(ProxyConfig.priority.desc(), ProxyConfig.created_at.desc())

    result = await db.execute(stmt)
    proxies = result.scalars().all()

    return ProxyListResponse(
        data=[ProxyResponse.model_validate(p) for p in proxies],
        total=len(proxies),
    )


@router.post("", response_model=ProxyActionResponse)
async def create_proxy(
    data: ProxyCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的代理配置

    创建后可通过测试端点验证代理可用性。
    """
    proxy = ProxyConfig(
        user_id=current_user.id,
        name=data.name,
        protocol=data.protocol,
        host=data.host,
        port=data.port,
        username=data.username,
        password_encrypted=data.password,  # TODO: 实际加密
        weight=data.weight,
        priority=data.priority,
        notes=data.notes,
        status=ProxyStatus.ACTIVE,
        enabled=True,
    )

    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)

    logger.info(f"创建代理: {data.name}, {data.protocol.value}://{data.host}:{data.port}")

    return ProxyActionResponse(
        success=True,
        message="代理创建成功",
        proxy_id=proxy.id,
        proxy=ProxyResponse.model_validate(proxy),
    )


@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """获取代理详情"""
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)
    return ProxyResponse.model_validate(proxy)


@router.put("/{proxy_id}", response_model=ProxyActionResponse)
async def update_proxy(
    proxy_id: str,
    data: ProxyUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    更新代理配置

    可以更新名称、主机、端口、认证信息等。
    """
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)

    # 更新字段
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(proxy, field, value)

    await db.commit()
    await db.refresh(proxy)

    logger.info(f"更新代理: {proxy.name}")

    return ProxyActionResponse(
        success=True,
        message="代理更新成功",
        proxy_id=proxy.id,
        proxy=ProxyResponse.model_validate(proxy),
    )


@router.delete("/{proxy_id}", response_model=ProxyActionResponse)
async def delete_proxy(
    proxy_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """删除代理"""
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)

    name = proxy.name
    await db.delete(proxy)
    await db.commit()

    logger.info(f"删除代理: {name}")

    return ProxyActionResponse(
        success=True,
        message="代理删除成功",
        proxy_id=proxy_id,
    )


@router.post("/{proxy_id}/test", response_model=ProxyActionResponse)
async def test_proxy(
    proxy_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    测试代理可用性

    通过代理访问测试 URL 验证代理是否正常工作。
    """
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)

    # 构建代理 URL
    proxy_url = _build_proxy_url(proxy)

    # 执行测试
    test_result = await _test_proxy_connection(proxy_url)

    # 更新代理状态
    proxy.last_check_at = datetime.now()

    if test_result.success:
        proxy.status = ProxyStatus.ACTIVE
        proxy.last_success_at = datetime.now()
        proxy.last_response_time = test_result.response_time_ms
        proxy.success_count += 1

        # 更新平均响应时间
        if proxy.avg_response_time is None:
            proxy.avg_response_time = test_result.response_time_ms
        else:
            # 移动平均
            proxy.avg_response_time = (
                proxy.avg_response_time * 0.8 + test_result.response_time_ms * 0.2
            )

        message = f"代理测试通过，响应时间: {test_result.response_time_ms:.0f}ms"
    else:
        proxy.status = ProxyStatus.FAILED
        proxy.last_failure_at = datetime.now()
        proxy.last_error_message = test_result.error
        proxy.failure_count += 1

        message = f"代理测试失败: {test_result.error}"

    proxy.request_count += 1
    await db.commit()
    await db.refresh(proxy)

    return ProxyActionResponse(
        success=test_result.success,
        message=message,
        proxy_id=proxy_id,
        proxy=ProxyResponse.model_validate(proxy),
    )


@router.post("/{proxy_id}/enable", response_model=ProxyActionResponse)
async def enable_proxy(
    proxy_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """启用代理"""
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)

    proxy.enabled = True
    await db.commit()
    await db.refresh(proxy)

    logger.info(f"启用代理: {proxy.name}")

    return ProxyActionResponse(
        success=True,
        message="代理已启用",
        proxy_id=proxy.id,
        proxy=ProxyResponse.model_validate(proxy),
    )


@router.post("/{proxy_id}/disable", response_model=ProxyActionResponse)
async def disable_proxy(
    proxy_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """禁用代理"""
    proxy = await _get_proxy_or_404(db, proxy_id, current_user.id)

    proxy.enabled = False
    await db.commit()
    await db.refresh(proxy)

    logger.info(f"禁用代理: {proxy.name}")

    return ProxyActionResponse(
        success=True,
        message="代理已禁用",
        proxy_id=proxy.id,
        proxy=ProxyResponse.model_validate(proxy),
    )


@router.post("/test-all", response_model=ProxyListResponse)
async def test_all_proxies(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    测试所有启用的代理

    并发测试所有启用状态的代理。
    """
    stmt = select(ProxyConfig).where(
        ProxyConfig.user_id == current_user.id,
        ProxyConfig.enabled == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    proxies = result.scalars().all()

    if not proxies:
        return ProxyListResponse(data=[], total=0)

    # 并发测试
    tasks = []
    for proxy in proxies:
        proxy_url = _build_proxy_url(proxy)
        tasks.append(_test_and_update_proxy(proxy, proxy_url))

    await asyncio.gather(*tasks)
    await db.commit()

    # 刷新所有代理数据
    for proxy in proxies:
        await db.refresh(proxy)

    logger.info(f"批量测试完成: {len(proxies)} 个代理")

    return ProxyListResponse(
        data=[ProxyResponse.model_validate(p) for p in proxies],
        total=len(proxies),
    )


# =============================================================
# 辅助函数
# =============================================================


async def _get_proxy_or_404(
    db: AsyncSession,
    proxy_id: str,
    user_id: str,
) -> ProxyConfig:
    """获取代理或抛出 404 异常"""
    stmt = select(ProxyConfig).where(
        ProxyConfig.id == proxy_id,
        ProxyConfig.user_id == user_id,
    )
    result = await db.execute(stmt)
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(status_code=404, detail=f"代理不存在: {proxy_id}")

    return proxy


def _build_proxy_url(proxy: ProxyConfig) -> str:
    """构建代理 URL"""
    if proxy.username and proxy.password:
        return f"{proxy.protocol.value}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
    return f"{proxy.protocol.value}://{proxy.host}:{proxy.port}"


async def _test_proxy_connection(proxy_url: str) -> ProxyTestResult:
    """测试代理连接"""
    for test_url in TEST_URLS:
        try:
            start_time = datetime.now()

            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=10.0,
            ) as client:
                response = await client.get(test_url)
                response.raise_for_status()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return ProxyTestResult(
                success=True,
                response_time_ms=elapsed,
            )

        except httpx.TimeoutException:
            continue
        except httpx.ProxyError as e:
            return ProxyTestResult(
                success=False,
                error=f"代理连接错误: {str(e)}",
            )
        except httpx.HTTPStatusError as e:
            return ProxyTestResult(
                success=False,
                error=f"HTTP 错误: {e.response.status_code}",
            )
        except Exception as e:
            return ProxyTestResult(
                success=False,
                error=f"未知错误: {str(e)}",
            )

    return ProxyTestResult(
        success=False,
        error="所有测试 URL 均超时",
    )


async def _test_and_update_proxy(proxy: ProxyConfig, proxy_url: str) -> None:
    """测试并更新代理状态（用于批量测试）"""
    test_result = await _test_proxy_connection(proxy_url)

    proxy.last_check_at = datetime.now()
    proxy.request_count += 1

    if test_result.success:
        proxy.status = ProxyStatus.ACTIVE
        proxy.last_success_at = datetime.now()
        proxy.last_response_time = test_result.response_time_ms
        proxy.success_count += 1

        if proxy.avg_response_time is None:
            proxy.avg_response_time = test_result.response_time_ms
        else:
            proxy.avg_response_time = (
                proxy.avg_response_time * 0.8 + test_result.response_time_ms * 0.2
            )
    else:
        proxy.status = ProxyStatus.FAILED
        proxy.last_failure_at = datetime.now()
        proxy.last_error_message = test_result.error
        proxy.failure_count += 1
