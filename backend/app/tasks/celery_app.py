"""
Celery 应用配置 - Celery Application Configuration
用于异步任务队列处理

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑
"""

from celery import Celery

from app.core.config import settings

# 创建 Celery 应用实例
celery_app = Celery(
    "spider_news",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化格式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区配置
    timezone=settings.SCHEDULER_TIMEZONE,
    enable_utc=True,

    # 任务执行配置
    task_track_started=True,
    task_time_limit=3600,  # 1小时硬超时
    task_soft_time_limit=3300,  # 55分钟软超时

    # 重试配置
    task_acks_late=True,  # 任务完成后才确认
    task_reject_on_worker_lost=True,  # Worker 丢失时拒绝任务

    # 结果配置
    result_expires=86400,  # 结果保留24小时

    # 并发配置
    worker_prefetch_multiplier=1,  # 每次只预取1个任务
    worker_concurrency=settings.SCRAPER_MAX_CONCURRENT,

    # 队列配置
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "scraper": {"exchange": "scraper", "routing_key": "scraper"},
        "social": {"exchange": "social", "routing_key": "social"},
        "export": {"exchange": "export", "routing_key": "export"},
        "search": {"exchange": "search", "routing_key": "search"},  # 搜索索引队列
        "dlq": {"exchange": "dlq", "routing_key": "dlq"},  # 死信队列
    },

    # 任务路由
    task_routes={
        "app.tasks.scraper_tasks.*": {"queue": "scraper"},
        "app.tasks.social_tasks.*": {"queue": "social"},
        "app.tasks.export_tasks.*": {"queue": "export"},
        "app.tasks.search_tasks.*": {"queue": "search"},
        "app.tasks.dlq.*": {"queue": "dlq"},
    },

    # Beat 调度配置（定时任务）
    beat_schedule={
        # 每日 UTC 00:00 重置配额
        "reset-daily-quotas": {
            "task": "app.tasks.quota_tasks.reset_daily_quotas",
            "schedule": {"hour": 0, "minute": 0},  # crontab
        },
        # 每小时清理过期验证码记录
        "cleanup-captcha-attempts": {
            "task": "app.tasks.maintenance_tasks.cleanup_captcha_attempts",
            "schedule": 3600,  # 每小时
        },
        # 每天清理过期导出文件
        "cleanup-expired-exports": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_exports",
            "schedule": 86400,  # 每天
        },
    },
)

# 自动发现任务模块
celery_app.autodiscover_tasks([
    "app.tasks",
])


def get_celery_app() -> Celery:
    """获取 Celery 应用实例"""
    return celery_app
