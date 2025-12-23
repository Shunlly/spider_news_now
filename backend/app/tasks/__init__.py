# Tasks package
"""
任务模块 - Celery 异步任务
Task Module - Celery Async Tasks

包含：
- celery_app: Celery 应用配置
- scheduler: APScheduler 调度器
- scraper_tasks: 爬虫任务
- social_tasks: 社交数据采集任务
- quota_tasks: 配额管理任务
- maintenance_tasks: 系统维护任务
- dlq: 死信队列处理
"""

from app.tasks.celery_app import celery_app, get_celery_app

__all__ = [
    "celery_app",
    "get_celery_app",
]
