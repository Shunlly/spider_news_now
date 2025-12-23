"""
配额模型 - Quota SQLAlchemy Model
Quota Model for Usage Tracking and Limits

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

配额追踪用户的资源使用情况，支持：
- 每日采集配额限制
- 并发任务数限制
- 配额自动重置
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class QuotaTier(str, Enum):
    """
    配额等级枚举

    不同等级对应不同的配额限制：
    - FREE: 免费版，100条/日，1并发
    - BASIC: 基础版，1000条/日，3并发
    - PRO: 专业版，10000条/日，10并发
    """
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


# 配额等级配置映射
TIER_CONFIG = {
    QuotaTier.FREE: {"daily_limit": 100, "concurrent_limit": 1},
    QuotaTier.BASIC: {"daily_limit": 1000, "concurrent_limit": 3},
    QuotaTier.PRO: {"daily_limit": 10000, "concurrent_limit": 10},
}


class Quota(Base):
    """
    配额实体 - 追踪用户的配额使用情况

    每个用户有一个配额记录，记录其配额限制和使用量。
    配额在每日 UTC 00:00 自动重置。
    """

    __tablename__ = "quotas"

    # 主键 - 自增整数
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="配额ID"
    )

    # 用户外键 - 一对一关系
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
        comment="用户ID"
    )

    # 配额等级
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default=QuotaTier.FREE.value,
        comment="配额等级: free, basic, pro"
    )

    # 每日采集限额
    daily_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100,
        comment="每日采集限额"
    )

    # 今日已使用量
    daily_used: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="今日已使用量"
    )

    # 并发任务限额
    concurrent_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="并发任务限额"
    )

    # 当前并发使用数
    concurrent_used: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="当前并发使用数"
    )

    # 配额重置时间 (UTC)
    reset_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1),
        comment="配额重置时间 (UTC)"
    )

    # 是否显示警告 - 当配额剩余不足10%时为True
    warning_shown: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否已显示配额警告"
    )

    # 时间戳
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now(),
        comment="更新时间"
    )

    # 关联关系
    user: Mapped["User"] = relationship(
        "User", back_populates="quota"
    )

    def __repr__(self) -> str:
        return (
            f"<Quota(user_id={self.user_id}, tier='{self.tier}', "
            f"daily={self.daily_used}/{self.daily_limit}, "
            f"concurrent={self.concurrent_used}/{self.concurrent_limit})>"
        )

    @property
    def daily_remaining(self) -> int:
        """获取今日剩余配额"""
        return max(0, self.daily_limit - self.daily_used)

    @property
    def concurrent_remaining(self) -> int:
        """获取剩余可用并发数"""
        return max(0, self.concurrent_limit - self.concurrent_used)

    @property
    def is_daily_exhausted(self) -> bool:
        """检查每日配额是否已用尽"""
        return self.daily_used >= self.daily_limit

    @property
    def is_concurrent_exhausted(self) -> bool:
        """检查并发配额是否已用尽"""
        return self.concurrent_used >= self.concurrent_limit

    @property
    def should_warn(self) -> bool:
        """
        检查是否应显示配额警告

        当每日配额剩余不足10%时返回True
        """
        if self.daily_limit == 0:
            return True
        return (self.daily_remaining / self.daily_limit) < 0.1

    def consume_daily(self, amount: int = 1) -> bool:
        """
        消耗每日配额

        Args:
            amount: 要消耗的数量

        Returns:
            True if 消耗成功, False if 配额不足
        """
        if self.daily_used + amount > self.daily_limit:
            return False
        self.daily_used += amount
        return True

    def acquire_concurrent(self) -> bool:
        """
        获取一个并发槽位

        Returns:
            True if 获取成功, False if 并发槽位已满
        """
        if self.concurrent_used >= self.concurrent_limit:
            return False
        self.concurrent_used += 1
        return True

    def release_concurrent(self) -> None:
        """释放一个并发槽位"""
        if self.concurrent_used > 0:
            self.concurrent_used -= 1

    def reset_daily(self) -> None:
        """
        重置每日配额

        在 UTC 00:00 调用此方法重置配额
        """
        self.daily_used = 0
        self.warning_shown = False
        self.reset_at = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

    def update_tier(self, tier: QuotaTier) -> None:
        """
        更新配额等级

        Args:
            tier: 新的配额等级
        """
        config = TIER_CONFIG.get(tier, TIER_CONFIG[QuotaTier.FREE])
        self.tier = tier.value
        self.daily_limit = config["daily_limit"]
        self.concurrent_limit = config["concurrent_limit"]

    @classmethod
    def create_for_tier(cls, user_id: str, tier: QuotaTier = QuotaTier.FREE) -> "Quota":
        """
        根据配额等级创建配额记录

        Args:
            user_id: 用户ID
            tier: 配额等级

        Returns:
            新创建的 Quota 实例
        """
        config = TIER_CONFIG.get(tier, TIER_CONFIG[QuotaTier.FREE])
        return cls(
            user_id=user_id,
            tier=tier.value,
            daily_limit=config["daily_limit"],
            daily_used=0,
            concurrent_limit=config["concurrent_limit"],
            concurrent_used=0,
            warning_shown=False,
        )
