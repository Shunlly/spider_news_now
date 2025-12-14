"""
代理配置模型 - 代理池管理
Proxy Configuration Model - Proxy Pool Management

遵循宪法 II.C 代理池要求：
- 支持多代理轮换
- 健康检查和故障转移
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProxyProtocol(str, Enum):
    """代理协议枚举"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyStatus(str, Enum):
    """代理状态枚举"""
    ACTIVE = "active"      # 可用
    TESTING = "testing"    # 测试中
    FAILED = "failed"      # 失败
    DISABLED = "disabled"  # 已禁用


class ProxyConfig(Base):
    """
    代理配置实体

    管理代理池中的代理节点。
    支持健康检查、权重分配和自动故障转移。
    """

    __tablename__ = "proxy_configs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 代理标识
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="代理名称（用于识别）"
    )

    # 代理地址
    protocol: Mapped[ProxyProtocol] = mapped_column(
        SQLEnum(ProxyProtocol), nullable=False, default=ProxyProtocol.HTTP,
        comment="代理协议"
    )
    host: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="代理主机地址"
    )
    port: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="代理端口"
    )

    # 认证信息（可选）
    username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="认证用户名"
    )
    password_encrypted: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="加密的认证密码"
    )

    # 状态
    status: Mapped[ProxyStatus] = mapped_column(
        SQLEnum(ProxyStatus),
        nullable=False,
        default=ProxyStatus.ACTIVE,
        index=True,
        comment="代理状态"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="是否启用"
    )

    # 权重和优先级
    weight: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="权重（用于负载均衡）"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="优先级（值越大优先级越高）"
    )

    # 使用统计
    request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="请求次数"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="成功次数"
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="失败次数"
    )

    # 性能指标
    avg_response_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="平均响应时间（毫秒）"
    )
    last_response_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="最后响应时间（毫秒）"
    )

    # 健康检查
    last_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后健康检查时间"
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后成功时间"
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="最后失败时间"
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="最后错误信息"
    )

    # 备注
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="备注信息"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # 索引定义
    __table_args__ = (
        Index("idx_status_enabled", "status", "enabled"),
        Index("idx_priority_weight", "priority", "weight"),
        {"comment": "代理配置表"},
    )

    @property
    def proxy_url(self) -> str:
        """获取完整的代理 URL"""
        if self.username and self.password_encrypted:
            # 注意：实际使用时需要解密密码
            return f"{self.protocol.value}://{self.username}:***@{self.host}:{self.port}"
        return f"{self.protocol.value}://{self.host}:{self.port}"

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    def __repr__(self) -> str:
        return (
            f"<ProxyConfig(id={self.id}, "
            f"name='{self.name}', "
            f"url='{self.proxy_url}', "
            f"status='{self.status.value}')>"
        )
