"""
用户管理 API 端点 - Users API Endpoints
User CRUD Operations (Admin Only)

提供用户管理功能：
- GET /users - 列出用户
- POST /users - 创建用户
- GET /users/{id} - 获取用户详情
- PUT /users/{id} - 更新用户
- DELETE /users/{id} - 删除用户
- POST /users/{id}/unlock - 解锁用户
- POST /users/{id}/reset-password - 重置密码

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserListResponse,
    UserResponse,
)
from app.services.permission_service import require_admin
from app.services.user_service import user_service

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["用户管理"])


# ============== Request/Response Schemas ==============


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., min_length=5, max_length=255, description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    role_id: int = Field(default=3, description="角色ID (1=超级管理员, 2=租户管理员, 3=普通用户)")
    tenant_id: int | None = Field(None, description="租户ID")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    email: str | None = Field(None, min_length=5, max_length=255, description="邮箱")
    role_id: int | None = Field(None, description="角色ID")
    is_active: bool | None = Field(None, description="是否激活")
    tenant_id: int | None = Field(None, description="租户ID")


class PasswordResetRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(..., description="消息内容")


# ============== API Endpoints ==============


@router.get(
    "",
    response_model=UserListResponse,
    summary="获取用户列表",
    description="管理员获取用户列表，支持分页和搜索"
)
async def list_users(
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, description="搜索关键词"),
) -> UserListResponse:
    """
    获取用户列表

    权限要求：管理员
    """
    users, total = await user_service.get_users(
        db=db,
        current_user=admin,
        page=page,
        page_size=page_size,
        search=search,
    )

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="管理员创建新用户"
)
async def create_user(
    request: UserCreateRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    创建用户

    权限要求：管理员

    注意：
    - 超级管理员可以创建任何角色的用户
    - 租户管理员只能创建普通用户
    """
    # 租户管理员权限检查
    if admin.is_tenant_admin:
        if request.role_id in (1, 2):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="租户管理员不能创建管理员账号"
            )
        # 强制设置为当前租户
        request.tenant_id = admin.tenant_id

    user, error_message = await user_service.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        role_id=request.role_id,
        tenant_id=request.tenant_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    logger.info("User created by admin", extra={
        "admin_id": admin.id,
        "new_user_id": user.id,
        "username": user.username
    })

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="获取用户详情",
    description="管理员获取指定用户的详细信息"
)
async def get_user(
    user_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    获取用户详情

    权限要求：管理员
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 租户管理员只能查看本租户用户
    if admin.is_tenant_admin and user.tenant_id != admin.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该用户"
        )

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新用户",
    description="管理员更新用户信息"
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    更新用户信息

    权限要求：管理员

    注意：
    - 不能修改超级管理员（除非是超级管理员自己）
    - 租户管理员只能修改本租户普通用户
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 权限检查
    if user.is_super_admin and admin.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能修改超级管理员"
        )

    if admin.is_tenant_admin:
        if user.tenant_id != admin.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改该用户"
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能修改管理员账号"
            )
        # 不允许修改角色为管理员
        if request.role_id in (1, 2):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能将用户设为管理员"
            )

    updated_user, error_message = await user_service.update_user(
        db=db,
        user=user,
        email=request.email,
        role_id=request.role_id,
        is_active=request.is_active,
        tenant_id=request.tenant_id,
    )

    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    logger.info("User updated by admin", extra={
        "admin_id": admin.id,
        "user_id": user.id
    })

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="删除用户",
    description="管理员删除用户"
)
async def delete_user(
    user_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    删除用户

    权限要求：管理员

    注意：
    - 不能删除自己
    - 不能删除超级管理员
    - 租户管理员只能删除本租户普通用户
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能删除自己
    if admin.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    # 不能删除超级管理员
    if user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能删除超级管理员"
        )

    # 租户管理员权限检查
    if admin.is_tenant_admin:
        if user.tenant_id != admin.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除该用户"
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能删除管理员账号"
            )

    success, message = await user_service.delete_user(db, user)

    logger.info("User deleted by admin", extra={
        "admin_id": admin.id,
        "deleted_user_id": user.id,
        "deleted_username": user.username
    })

    return MessageResponse(message=message)


@router.post(
    "/{user_id}/unlock",
    response_model=MessageResponse,
    summary="解锁用户",
    description="管理员解锁被锁定的用户账号"
)
async def unlock_user(
    user_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    解锁用户账号

    权限要求：管理员
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 租户管理员权限检查
    if admin.is_tenant_admin and user.tenant_id != admin.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该用户"
        )

    success, message = await user_service.unlock_user(db, user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    logger.info("User unlocked by admin", extra={
        "admin_id": admin.id,
        "user_id": user.id
    })

    return MessageResponse(message=message)


@router.post(
    "/{user_id}/reset-password",
    response_model=MessageResponse,
    summary="重置密码",
    description="管理员重置用户密码"
)
async def reset_password(
    user_id: str,
    request: PasswordResetRequest,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    重置用户密码

    权限要求：管理员

    注意：不能重置超级管理员密码（除非是自己）
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能重置超级管理员密码（除非是自己）
    if user.is_super_admin and admin.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能重置超级管理员密码"
        )

    # 租户管理员权限检查
    if admin.is_tenant_admin:
        if user.tenant_id != admin.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该用户"
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能重置管理员密码"
            )

    success, message = await user_service.reset_password(
        db=db,
        user=user,
        new_password=request.new_password,
    )

    logger.info("User password reset by admin", extra={
        "admin_id": admin.id,
        "user_id": user.id
    })

    return MessageResponse(message=message)


@router.post(
    "/{user_id}/toggle-active",
    response_model=MessageResponse,
    summary="切换激活状态",
    description="管理员切换用户激活/禁用状态"
)
async def toggle_user_active(
    user_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    切换用户激活状态

    权限要求：管理员
    """
    user = await user_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能禁用自己
    if admin.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    # 不能禁用超级管理员
    if user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能禁用超级管理员"
        )

    # 租户管理员权限检查
    if admin.is_tenant_admin:
        if user.tenant_id != admin.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该用户"
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能操作管理员账号"
            )

    new_status, message = await user_service.toggle_user_active(db, user)

    logger.info("User active status toggled", extra={
        "admin_id": admin.id,
        "user_id": user.id,
        "new_status": new_status
    })

    return MessageResponse(message=message)
