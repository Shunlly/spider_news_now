"""
用户相关 Pydantic Schema
User Pydantic Schemas for Request/Response validation

定义用户相关的请求和响应模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


# ============== Base Schemas ==============


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="用户名（3-50字符，仅字母/数字/下划线）"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱（可选）"
    )


# ============== Request Schemas ==============


class UserCreate(UserBase):
    """创建用户请求 Schema"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="密码（至少8字符）"
    )
    role: UserRole = Field(
        default=UserRole.USER,
        description="用户角色"
    )


class UserUpdate(BaseModel):
    """更新用户请求 Schema"""
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱"
    )
    role: Optional[UserRole] = Field(
        None,
        description="用户角色"
    )
    is_active: Optional[bool] = Field(
        None,
        description="是否激活"
    )


class UserPasswordUpdate(BaseModel):
    """更新密码请求 Schema"""
    current_password: str = Field(
        ...,
        description="当前密码"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="新密码（至少8字符）"
    )


# ============== Response Schemas ==============


class UserResponse(BaseModel):
    """用户响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")


class UserListResponse(BaseModel):
    """用户列表响应 Schema"""
    users: list[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")


class UserInDB(UserResponse):
    """数据库中的用户 Schema（内部使用）"""
    model_config = ConfigDict(from_attributes=True)

    password_hash: str
    login_attempts: int
    locked_until: Optional[datetime]
