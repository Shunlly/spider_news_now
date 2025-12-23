"""
系统指标服务 - System Metrics Service
T164: Add system metrics collection (task queue, processing rate)

提供系统运行指标收集功能：
1. 任务队列状态
2. 处理速率统计
3. 资源使用情况

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskQueueMetrics(BaseModel):
    """任务队列指标"""
    pending: int = Field(0, description="等待中的任务数")
    running: int = Field(0, description="运行中的任务数")
    completed: int = Field(0, description="已完成的任务数")
    failed: int = Field(0, description="失败的任务数")
    total: int = Field(0, description="总任务数")


class ProcessingRateMetrics(BaseModel):
    """处理速率指标"""
    articles_per_minute: float = Field(0.0, description="每分钟采集文章数")
    articles_per_hour: float = Field(0.0, description="每小时采集文章数")
    tasks_per_minute: float = Field(0.0, description="每分钟完成任务数")
    tasks_per_hour: float = Field(0.0, description="每小时完成任务数")
    avg_task_duration_seconds: float = Field(0.0, description="平均任务时长（秒）")


class ResourceMetrics(BaseModel):
    """资源使用指标"""
    active_scrapers: int = Field(0, description="活跃爬虫数")
    total_scrapers: int = Field(0, description="爬虫总数")
    active_connections: int = Field(0, description="活跃连接数")
    db_connections: int = Field(0, description="数据库连接数")
    memory_usage_mb: float = Field(0.0, description="内存使用（MB）")


class SystemMetrics(BaseModel):
    """系统综合指标"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    task_queue: TaskQueueMetrics = Field(default_factory=TaskQueueMetrics)
    processing_rate: ProcessingRateMetrics = Field(default_factory=ProcessingRateMetrics)
    resources: ResourceMetrics = Field(default_factory=ResourceMetrics)
    uptime_seconds: float = Field(0.0, description="系统运行时长（秒）")


@dataclass
class MetricsSample:
    """指标样本"""
    timestamp: datetime
    value: float
    labels: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器

    收集和存储时序指标数据。
    使用内存存储，可扩展为 Prometheus/InfluxDB。
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self._samples: dict[str, list[MetricsSample]] = {}
        self._start_time = datetime.now(UTC)

    def record(
        self,
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        记录指标值

        Args:
            metric_name: 指标名称
            value: 指标值
            labels: 标签
        """
        if metric_name not in self._samples:
            self._samples[metric_name] = []

        sample = MetricsSample(
            timestamp=datetime.now(UTC),
            value=value,
            labels=labels or {},
        )
        self._samples[metric_name].append(sample)

        # 清理过期数据
        self._cleanup(metric_name)

    def _cleanup(self, metric_name: str) -> None:
        """清理过期样本"""
        cutoff = datetime.now(UTC) - timedelta(hours=self.retention_hours)
        self._samples[metric_name] = [
            s for s in self._samples[metric_name]
            if s.timestamp >= cutoff
        ]

    def get_latest(self, metric_name: str) -> float | None:
        """获取最新值"""
        samples = self._samples.get(metric_name, [])
        if not samples:
            return None
        return samples[-1].value

    def get_rate(
        self,
        metric_name: str,
        window_minutes: int = 1,
    ) -> float:
        """
        计算速率（增量/时间窗口）

        Args:
            metric_name: 指标名称
            window_minutes: 时间窗口（分钟）

        Returns:
            速率值
        """
        samples = self._samples.get(metric_name, [])
        if len(samples) < 2:
            return 0.0

        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        window_samples = [s for s in samples if s.timestamp >= cutoff]

        if len(window_samples) < 2:
            return 0.0

        value_diff = window_samples[-1].value - window_samples[0].value
        time_diff = (window_samples[-1].timestamp - window_samples[0].timestamp).total_seconds()

        if time_diff <= 0:
            return 0.0

        return (value_diff / time_diff) * 60  # 转换为每分钟

    def get_average(
        self,
        metric_name: str,
        window_minutes: int = 60,
    ) -> float:
        """
        计算平均值

        Args:
            metric_name: 指标名称
            window_minutes: 时间窗口（分钟）

        Returns:
            平均值
        """
        samples = self._samples.get(metric_name, [])
        if not samples:
            return 0.0

        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        window_samples = [s for s in samples if s.timestamp >= cutoff]

        if not window_samples:
            return 0.0

        return sum(s.value for s in window_samples) / len(window_samples)

    def get_uptime_seconds(self) -> float:
        """获取系统运行时长"""
        return (datetime.now(UTC) - self._start_time).total_seconds()


class SystemMetricsService:
    """
    系统指标服务

    提供系统运行指标的收集、存储和查询功能。
    """

    def __init__(self):
        self.collector = MetricsCollector()
        self._task_counters = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }
        self._article_count = 0

    def record_task_started(self, task_id: str) -> None:
        """记录任务开始"""
        self._task_counters["pending"] = max(0, self._task_counters["pending"] - 1)
        self._task_counters["running"] += 1
        self.collector.record("tasks_running", self._task_counters["running"])
        logger.debug(f"Task started: {task_id}")

    def record_task_queued(self, task_id: str) -> None:
        """记录任务入队"""
        self._task_counters["pending"] += 1
        self.collector.record("tasks_pending", self._task_counters["pending"])
        logger.debug(f"Task queued: {task_id}")

    def record_task_completed(
        self,
        task_id: str,
        duration_seconds: float,
        articles_scraped: int = 0,
    ) -> None:
        """
        记录任务完成

        Args:
            task_id: 任务 ID
            duration_seconds: 执行时长
            articles_scraped: 采集的文章数
        """
        self._task_counters["running"] = max(0, self._task_counters["running"] - 1)
        self._task_counters["completed"] += 1

        self.collector.record("tasks_completed", self._task_counters["completed"])
        self.collector.record("task_duration", duration_seconds)

        if articles_scraped > 0:
            self._article_count += articles_scraped
            self.collector.record("articles_total", self._article_count)

        logger.debug(
            f"Task completed: {task_id}",
            extra={"duration": duration_seconds, "articles": articles_scraped}
        )

    def record_task_failed(self, task_id: str, error: str) -> None:
        """记录任务失败"""
        self._task_counters["running"] = max(0, self._task_counters["running"] - 1)
        self._task_counters["failed"] += 1
        self.collector.record("tasks_failed", self._task_counters["failed"])
        logger.debug(f"Task failed: {task_id}, error: {error}")

    def record_scraper_active(self, source_key: str, active: bool) -> None:
        """记录爬虫活跃状态"""
        current = self.collector.get_latest("scrapers_active") or 0
        new_value = current + (1 if active else -1)
        self.collector.record("scrapers_active", max(0, new_value))

    def record_articles_scraped(self, count: int, source_key: str) -> None:
        """记录采集的文章数"""
        self._article_count += count
        self.collector.record("articles_total", self._article_count)
        self.collector.record(
            f"articles_{source_key}",
            count,
            labels={"source": source_key}
        )

    async def get_metrics(self) -> SystemMetrics:
        """
        获取系统综合指标

        Returns:
            SystemMetrics 对象
        """
        # 任务队列指标
        task_queue = TaskQueueMetrics(
            pending=self._task_counters["pending"],
            running=self._task_counters["running"],
            completed=self._task_counters["completed"],
            failed=self._task_counters["failed"],
            total=sum(self._task_counters.values()),
        )

        # 处理速率指标
        processing_rate = ProcessingRateMetrics(
            articles_per_minute=self.collector.get_rate("articles_total", 1),
            articles_per_hour=self.collector.get_rate("articles_total", 60),
            tasks_per_minute=self.collector.get_rate("tasks_completed", 1),
            tasks_per_hour=self.collector.get_rate("tasks_completed", 60),
            avg_task_duration_seconds=self.collector.get_average("task_duration", 60),
        )

        # 资源指标
        resources = await self._get_resource_metrics()

        return SystemMetrics(
            task_queue=task_queue,
            processing_rate=processing_rate,
            resources=resources,
            uptime_seconds=self.collector.get_uptime_seconds(),
        )

    async def _get_resource_metrics(self) -> ResourceMetrics:
        """获取资源使用指标"""
        import gc

        # 获取活跃爬虫数（从数据库）
        active_scrapers = 0
        total_scrapers = 0
        try:
            from sqlalchemy import func, select

            from app.db.session import async_session_maker
            from app.models.news_source import NewsSource

            async with async_session_maker() as db:
                total_stmt = select(func.count()).select_from(NewsSource)
                total_result = await db.execute(total_stmt)
                total_scrapers = total_result.scalar() or 0

                active_stmt = (
                    select(func.count())
                    .select_from(NewsSource)
                    .where(NewsSource.enabled == True)  # noqa: E712
                )
                active_result = await db.execute(active_stmt)
                active_scrapers = active_result.scalar() or 0
        except Exception as e:
            logger.debug(f"Failed to get scraper counts: {e}")

        # 获取活跃 WebSocket 连接数
        active_connections = 0
        try:
            from app.api.v1.endpoints.dashboard import manager
            active_connections = manager.get_connection_count()
        except Exception:
            pass

        # 获取内存使用
        memory_usage_mb = 0.0
        try:
            import psutil
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # psutil 未安装，使用 gc 估算
            gc.collect()
            # 无法精确获取内存使用

        return ResourceMetrics(
            active_scrapers=active_scrapers,
            total_scrapers=total_scrapers,
            active_connections=active_connections,
            db_connections=0,  # 需要数据库连接池支持
            memory_usage_mb=memory_usage_mb,
        )

    async def get_metrics_summary(self) -> dict[str, Any]:
        """
        获取指标摘要（用于 API 响应）

        Returns:
            指标摘要字典
        """
        metrics = await self.get_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "uptime_seconds": metrics.uptime_seconds,
            "task_queue": metrics.task_queue.model_dump(),
            "processing_rate": metrics.processing_rate.model_dump(),
            "resources": metrics.resources.model_dump(),
        }

    def get_health_status(self) -> dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态字典
        """
        # 检查是否有任务积压
        task_backlog = self._task_counters["pending"] > 100
        high_failure_rate = (
            self._task_counters["failed"] > 0
            and self._task_counters["completed"] > 0
            and (self._task_counters["failed"] / self._task_counters["completed"]) > 0.1
        )

        status = "healthy"
        issues = []

        if task_backlog:
            status = "degraded"
            issues.append("Task backlog detected")

        if high_failure_rate:
            status = "degraded"
            issues.append("High task failure rate")

        return {
            "status": status,
            "issues": issues,
            "counters": self._task_counters.copy(),
        }


# 全局服务实例
metrics_service = SystemMetricsService()
