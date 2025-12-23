"""
告警服务 - Alerting Service
T165: Implement alerting service for threshold breach

提供系统告警功能：
1. 配额阈值告警
2. 爬虫失败告警
3. 系统健康告警

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """告警类型"""
    QUOTA_WARNING = "quota_warning"        # 配额即将用尽
    QUOTA_EXCEEDED = "quota_exceeded"      # 配额已超限
    SCRAPER_FAILED = "scraper_failed"      # 爬虫失败
    SCRAPER_TIMEOUT = "scraper_timeout"    # 爬虫超时
    SYSTEM_ERROR = "system_error"          # 系统错误
    LOGIN_ANOMALY = "login_anomaly"        # 登录异常
    RATE_LIMIT = "rate_limit"              # 触发限流


class Alert(BaseModel):
    """告警模型"""
    id: str = Field(..., description="告警 ID")
    type: AlertType = Field(..., description="告警类型")
    level: AlertLevel = Field(..., description="告警级别")
    title: str = Field(..., description="告警标题")
    message: str = Field(..., description="告警详情")
    source: str | None = Field(None, description="告警来源")
    user_id: str | None = Field(None, description="相关用户 ID")
    tenant_id: int | None = Field(None, description="相关租户 ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    acknowledged: bool = Field(False, description="是否已确认")
    acknowledged_at: datetime | None = Field(None, description="确认时间")
    acknowledged_by: str | None = Field(None, description="确认人")


class AlertThresholds(BaseModel):
    """告警阈值配置"""
    quota_warning_percent: int = Field(80, description="配额警告阈值（百分比）")
    quota_critical_percent: int = Field(95, description="配额严重阈值（百分比）")
    scraper_failure_threshold: int = Field(3, description="爬虫连续失败次数阈值")
    login_failure_threshold: int = Field(5, description="登录失败次数阈值")
    rate_limit_threshold: int = Field(100, description="限流触发次数阈值")


class AlertingService:
    """
    告警服务

    监控系统各项指标，在超过阈值时触发告警。
    支持多种告警通道（WebSocket、日志、未来可扩展邮件/短信）。
    """

    def __init__(self):
        self.thresholds = AlertThresholds()
        # 内存存储最近告警（可替换为 Redis）
        self._recent_alerts: list[Alert] = []
        self._max_alerts = 1000

    def update_thresholds(self, thresholds: AlertThresholds) -> None:
        """更新告警阈值配置"""
        self.thresholds = thresholds
        logger.info("Alert thresholds updated", extra={"thresholds": thresholds.model_dump()})

    async def check_quota(
        self,
        user_id: str,
        quota_used: int,
        quota_limit: int,
    ) -> Alert | None:
        """
        检查配额并触发告警

        Args:
            user_id: 用户 ID
            quota_used: 已使用配额
            quota_limit: 配额限制

        Returns:
            Alert 如果需要告警，否则 None
        """
        if quota_limit <= 0:
            return None

        usage_percent = (quota_used / quota_limit) * 100

        if usage_percent >= self.thresholds.quota_critical_percent:
            return await self._create_and_send_alert(
                alert_type=AlertType.QUOTA_EXCEEDED,
                level=AlertLevel.CRITICAL,
                title="配额即将用尽",
                message=f"配额使用已达 {usage_percent:.1f}%（{quota_used}/{quota_limit}），请尽快处理",
                user_id=user_id,
                metadata={
                    "quota_used": quota_used,
                    "quota_limit": quota_limit,
                    "usage_percent": usage_percent,
                },
            )
        elif usage_percent >= self.thresholds.quota_warning_percent:
            return await self._create_and_send_alert(
                alert_type=AlertType.QUOTA_WARNING,
                level=AlertLevel.WARNING,
                title="配额警告",
                message=f"配额使用已达 {usage_percent:.1f}%（{quota_used}/{quota_limit}）",
                user_id=user_id,
                metadata={
                    "quota_used": quota_used,
                    "quota_limit": quota_limit,
                    "usage_percent": usage_percent,
                },
            )

        return None

    async def alert_scraper_failure(
        self,
        source_key: str,
        error_message: str,
        consecutive_failures: int,
        user_id: str | None = None,
    ) -> Alert | None:
        """
        爬虫失败告警

        Args:
            source_key: 爬虫源标识
            error_message: 错误信息
            consecutive_failures: 连续失败次数
            user_id: 用户 ID

        Returns:
            Alert 如果达到阈值，否则 None
        """
        if consecutive_failures < self.thresholds.scraper_failure_threshold:
            return None

        level = AlertLevel.CRITICAL if consecutive_failures >= 5 else AlertLevel.ERROR

        return await self._create_and_send_alert(
            alert_type=AlertType.SCRAPER_FAILED,
            level=level,
            title=f"爬虫失败: {source_key}",
            message=f"爬虫 {source_key} 已连续失败 {consecutive_failures} 次: {error_message}",
            source=source_key,
            user_id=user_id,
            metadata={
                "source_key": source_key,
                "consecutive_failures": consecutive_failures,
                "error_message": error_message,
            },
        )

    async def alert_login_anomaly(
        self,
        ip_address: str,
        failure_count: int,
        user_email: str | None = None,
    ) -> Alert | None:
        """
        登录异常告警

        Args:
            ip_address: 来源 IP
            failure_count: 失败次数
            user_email: 尝试登录的邮箱

        Returns:
            Alert 如果达到阈值，否则 None
        """
        if failure_count < self.thresholds.login_failure_threshold:
            return None

        level = AlertLevel.CRITICAL if failure_count >= 10 else AlertLevel.WARNING

        return await self._create_and_send_alert(
            alert_type=AlertType.LOGIN_ANOMALY,
            level=level,
            title="登录异常检测",
            message=f"IP {ip_address} 在短时间内尝试登录失败 {failure_count} 次",
            source=ip_address,
            metadata={
                "ip_address": ip_address,
                "failure_count": failure_count,
                "user_email": user_email,
            },
        )

    async def alert_system_error(
        self,
        component: str,
        error_message: str,
        details: dict | None = None,
    ) -> Alert:
        """
        系统错误告警

        Args:
            component: 组件名称
            error_message: 错误信息
            details: 额外详情

        Returns:
            创建的 Alert
        """
        return await self._create_and_send_alert(
            alert_type=AlertType.SYSTEM_ERROR,
            level=AlertLevel.ERROR,
            title=f"系统错误: {component}",
            message=error_message,
            source=component,
            metadata=details or {},
        )

    async def _create_and_send_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        source: str | None = None,
        user_id: str | None = None,
        tenant_id: int | None = None,
        metadata: dict | None = None,
    ) -> Alert:
        """
        创建并发送告警

        Args:
            alert_type: 告警类型
            level: 告警级别
            title: 标题
            message: 消息
            source: 来源
            user_id: 用户 ID
            tenant_id: 租户 ID
            metadata: 元数据

        Returns:
            创建的 Alert
        """
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            type=alert_type,
            level=level,
            title=title,
            message=message,
            source=source,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )

        # 存储告警
        self._recent_alerts.append(alert)
        if len(self._recent_alerts) > self._max_alerts:
            self._recent_alerts = self._recent_alerts[-self._max_alerts:]

        # 记录日志
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }.get(level, logger.warning)

        log_method(
            f"Alert: {title}",
            extra={
                "alert_id": alert.id,
                "alert_type": alert_type.value,
                "level": level.value,
                "message": message,
                "source": source,
                "user_id": user_id,
            }
        )

        # 发送 WebSocket 通知（如果有连接）
        await self._send_websocket_alert(alert)

        return alert

    async def _send_websocket_alert(self, alert: Alert) -> None:
        """
        通过 WebSocket 发送告警

        Args:
            alert: 告警对象
        """
        try:
            from app.api.v1.endpoints.dashboard import push_alert

            if alert.user_id:
                await push_alert(
                    user_id=alert.user_id,
                    level=alert.level.value,
                    title=alert.title,
                    message=alert.message,
                )
        except Exception as e:
            logger.debug(f"Failed to send WebSocket alert: {e}")

    def get_recent_alerts(
        self,
        limit: int = 50,
        level: AlertLevel | None = None,
        alert_type: AlertType | None = None,
        acknowledged: bool | None = None,
    ) -> list[Alert]:
        """
        获取最近的告警

        Args:
            limit: 返回数量限制
            level: 按级别筛选
            alert_type: 按类型筛选
            acknowledged: 按确认状态筛选

        Returns:
            告警列表
        """
        alerts = self._recent_alerts.copy()

        if level is not None:
            alerts = [a for a in alerts if a.level == level]

        if alert_type is not None:
            alerts = [a for a in alerts if a.type == alert_type]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        # 按时间倒序
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        确认告警

        Args:
            alert_id: 告警 ID
            acknowledged_by: 确认人 ID

        Returns:
            是否成功
        """
        for alert in self._recent_alerts:
            if alert.id == alert_id and not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                logger.info(
                    "Alert acknowledged",
                    extra={
                        "alert_id": alert_id,
                        "acknowledged_by": acknowledged_by,
                    }
                )
                return True
        return False

    def get_alert_stats(self) -> dict[str, Any]:
        """
        获取告警统计

        Returns:
            统计信息字典
        """
        alerts = self._recent_alerts

        return {
            "total": len(alerts),
            "unacknowledged": sum(1 for a in alerts if not a.acknowledged),
            "by_level": {
                level.value: sum(1 for a in alerts if a.level == level)
                for level in AlertLevel
            },
            "by_type": {
                alert_type.value: sum(1 for a in alerts if a.type == alert_type)
                for alert_type in AlertType
            },
        }


# 全局服务实例
alerting_service = AlertingService()
