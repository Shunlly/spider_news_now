"""
验证码尝试模型 - CaptchaAttempt SQLAlchemy Model
Captcha Attempt Model for Rate Limiting

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

记录滑块验证码的尝试情况，用于：
- 追踪失败次数
- 实现冷却期机制（连续失败3次后60秒冷却）
- 防止机器人攻击
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaptchaAttempt(Base):
    """
    验证码尝试记录实体

    用于追踪滑块验证码的失败次数和实现冷却期机制。
    记录保留24小时后自动清理。
    """

    __tablename__ = "captcha_attempts"

    # 主键 - 自增整数
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="记录ID"
    )

    # 标识符 - IP地址或邮箱，用于识别同一用户/设备
    identifier: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="标识符（IP或邮箱）"
    )

    # 验证码ID - 用于关联验证码会话
    captcha_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="验证码会话ID"
    )

    # 是否验证成功
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="验证是否成功"
    )

    # 来源IP地址
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False,
        comment="来源IP地址"
    )

    # 用户代理
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="用户代理字符串"
    )

    # 尝试时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), index=True,
        comment="尝试时间"
    )

    def __repr__(self) -> str:
        status = "成功" if self.success else "失败"
        return f"<CaptchaAttempt(id={self.id}, identifier='{self.identifier}', status={status})>"


# 验证码配置常量
CAPTCHA_CONFIG = {
    # 连续失败多少次后触发冷却
    "max_attempts": 3,
    # 冷却时间（秒）
    "cooldown_seconds": 60,
    # 验证码有效期（秒）
    "captcha_expire_seconds": 300,  # 5分钟
    # 记录保留时间（秒）
    "record_retention_seconds": 86400,  # 24小时
    # 验证容差（百分比）
    "position_tolerance": 3,  # 允许3%的误差
}
