"""
用户相关 Pydantic Schema
User Pydantic Schemas for Request/Response validation

定义用户相关的请求和响应模型。
"""

from datetime import datetime

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
    email: EmailStr | None = Field(
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
    email: EmailStr | None = Field(
        None,
        description="邮箱"
    )
    role: UserRole | None = Field(
        None,
        description="用户角色"
    )
    is_active: bool | None = Field(
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


class RoleResponse(BaseModel):
    """角色响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色标识")
    display_name: str | None = Field(None, description="显示名称")
    permissions: list[str] = Field(..., description="权限列表")


class UserResponse(BaseModel):
    """用户响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str | None = Field(None, description="邮箱")
    role_id: int = Field(..., description="角色ID")
    tenant_id: int | None = Field(None, description="租户ID")
    quota_tier: str = Field(default="free", description="配额等级")
    is_verified: bool = Field(default=False, description="邮箱是否已验证")
    is_active: bool = Field(..., description="是否激活")
    last_login_at: datetime | None = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")

    # 兼容旧版 role 字段（从 role_id 推断）
    @property
    def role(self) -> UserRole:
        """向后兼容：从 role_id 获取 UserRole"""
        if self.role_id in (1, 2):
            return UserRole.ADMIN
        return UserRole.USER


class UserWithRoleResponse(UserResponse):
    """包含角色详情的用户响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    role: RoleResponse | None = Field(None, description="角色详情")


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
    locked_until: datetime | None
