"""
死信队列处理器 - Dead Letter Queue Handler
处理失败的任务，支持重试和告警

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑
"""

import json
from datetime import datetime
from typing import Any

from celery import Task

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


class DLQTask(Task):
    """
    死信队列任务基类

    当任务失败超过最大重试次数时，会被移入死信队列。
    死信队列中的任务可以：
    - 手动重试
    - 发送告警
    - 记录到数据库供后续分析
    """

    # 最大重试次数
    max_retries = 3
    # 重试延迟（秒）
    default_retry_delay = 60

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """
        任务失败回调

        当任务失败且超过最大重试次数时，将任务移入死信队列。

        Args:
            exc: 异常对象
            task_id: 任务ID
            args: 任务位置参数
            kwargs: 任务关键字参数
            einfo: 异常信息
        """
        logger.error(
            f"任务失败，移入死信队列: task_id={task_id}, "
            f"task_name={self.name}, error={str(exc)}"
        )

        # 发送到死信队列处理
        handle_dead_letter.delay(
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            error=str(exc),
            traceback=str(einfo) if einfo else None,
        )


@celery_app.task(name="app.tasks.dlq.handle_dead_letter", queue="dlq")
def handle_dead_letter(
    task_name: str,
    task_id: str,
    args: tuple,
    kwargs: dict,
    error: str,
    traceback: str | None = None,
) -> dict:
    """
    处理死信

    记录失败的任务信息，便于后续分析和手动处理。

    Args:
        task_name: 原始任务名称
        task_id: 原始任务ID
        args: 原始任务参数
        kwargs: 原始任务关键字参数
        error: 错误信息
        traceback: 堆栈跟踪

    Returns:
        处理结果字典
    """
    dead_letter = {
        "task_name": task_name,
        "task_id": task_id,
        "args": args,
        "kwargs": kwargs,
        "error": error,
        "traceback": traceback,
        "received_at": datetime.utcnow().isoformat(),
    }

    # 记录到日志
    logger.warning(f"死信入队: {json.dumps(dead_letter, ensure_ascii=False)}")

    # TODO: 可扩展 - 发送告警（邮件、Slack等）
    # TODO: 可扩展 - 写入数据库

    return {
        "status": "recorded",
        "task_id": task_id,
        "task_name": task_name,
    }


@celery_app.task(name="app.tasks.dlq.retry_dead_letter", queue="dlq")
def retry_dead_letter(
    task_name: str,
    args: tuple,
    kwargs: dict,
) -> dict:
    """
    重试死信任务

    手动重试之前失败的任务。

    Args:
        task_name: 任务名称
        args: 任务参数
        kwargs: 任务关键字参数

    Returns:
        重试结果
    """
    logger.info(f"重试死信任务: {task_name}")

    try:
        # 获取原始任务并重新执行
        task = celery_app.tasks.get(task_name)
        if task is None:
            return {
                "status": "failed",
                "error": f"任务 {task_name} 不存在",
            }

        # 重新调度任务
        result = task.apply_async(args=args, kwargs=kwargs)
        return {
            "status": "retried",
            "new_task_id": result.id,
        }
    except Exception as e:
        logger.error(f"重试死信任务失败: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }
