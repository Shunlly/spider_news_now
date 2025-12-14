"""
系统管理 Pydantic Schema
System Management Pydantic Schemas

定义账号凭证和代理配置的请求/响应模型。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.social_session import Platform
from app.models.account_credential import CredentialStatus
from app.models.proxy_config import ProxyProtocol, ProxyStatus


# =============================================================
# 账号凭证 Schema
# =============================================================

class CredentialBase(BaseModel):
    """账号凭证基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="凭证名称")
    platform: Platform = Field(..., description="平台类型")


class CredentialCreate(CredentialBase):
    """创建账号凭证请求"""
    credentials: Dict[str, Any] = Field(..., description="凭证数据（JSON 格式）")
    is_default: bool = Field(False, description="是否为默认凭证")


class CredentialUpdate(BaseModel):
    """更新账号凭证请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credentials: Optional[Dict[str, Any]] = Field(None, description="新的凭证数据")
    status: Optional[CredentialStatus] = Field(None, description="凭证状态")
    is_default: Optional[bool] = Field(None, description="是否为默认凭证")


class CredentialResponse(BaseModel):
    """账号凭证响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    platform: Platform
    status: CredentialStatus
    is_default: bool
    request_count: int
    error_count: int
    last_used_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    rate_limit_reset_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CredentialListResponse(BaseModel):
    """账号凭证列表响应"""
    data: List[CredentialResponse]
    total: int


class CredentialActionResponse(BaseModel):
    """凭证操作响应"""
    success: bool
    message: str
    credential_id: Optional[int] = None
    credential: Optional[CredentialResponse] = None


# =============================================================
# 代理配置 Schema
# =============================================================

class ProxyBase(BaseModel):
    """代理配置基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="代理名称")
    protocol: ProxyProtocol = Field(ProxyProtocol.HTTP, description="代理协议")
    host: str = Field(..., min_length=1, max_length=255, description="代理主机")
    port: int = Field(..., ge=1, le=65535, description="代理端口")


class ProxyCreate(ProxyBase):
    """创建代理配置请求"""
    username: Optional[str] = Field(None, max_length=100, description="认证用户名")
    password: Optional[str] = Field(None, max_length=255, description="认证密码")
    weight: int = Field(1, ge=1, le=100, description="权重")
    priority: int = Field(0, ge=0, le=100, description="优先级")
    notes: Optional[str] = Field(None, description="备注")


class ProxyUpdate(BaseModel):
    """更新代理配置请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    protocol: Optional[ProxyProtocol] = None
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=255)
    status: Optional[ProxyStatus] = None
    enabled: Optional[bool] = None
    weight: Optional[int] = Field(None, ge=1, le=100)
    priority: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class ProxyResponse(BaseModel):
    """代理配置响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    protocol: ProxyProtocol
    host: str
    port: int
    username: Optional[str] = None
    status: ProxyStatus
    enabled: bool
    weight: int
    priority: int
    request_count: int
    success_count: int
    failure_count: int
    avg_response_time: Optional[float] = None
    last_response_time: Optional[float] = None
    last_check_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count


class ProxyListResponse(BaseModel):
    """代理配置列表响应"""
    data: List[ProxyResponse]
    total: int


class ProxyActionResponse(BaseModel):
    """代理操作响应"""
    success: bool
    message: str
    proxy_id: Optional[int] = None
    proxy: Optional[ProxyResponse] = None


class ProxyTestResult(BaseModel):
    """代理测试结果"""
    success: bool
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
