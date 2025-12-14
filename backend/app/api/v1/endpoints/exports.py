"""
数据导出 API 端点
Data Export API Endpoints

提供数据导出功能的 RESTful API。
支持新闻、社交会话、社交消息的导出。
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.export_task import ExportTask, ExportFormat, ExportStatus
from app.services.export_service import DataSource, ExportService

logger = get_logger(__name__)

router = APIRouter(prefix="/exports", tags=["exports"])


# =============================================================
# 请求/响应模型
# =============================================================


class ExportRequest(BaseModel):
    """导出请求"""
    data_source: DataSource = Field(..., description="数据源类型")
    export_format: ExportFormat = Field(ExportFormat.CSV, description="导出格式")
    filters: Optional[dict] = Field(None, description="过滤条件")
    filename: Optional[str] = Field(None, description="自定义文件名")


class ExportTaskResponse(BaseModel):
    """导出任务响应"""
    id: int
    data_source: str
    export_format: str
    status: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    total_records: Optional[int] = None
    exported_records: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExportListResponse(BaseModel):
    """导出任务列表响应"""
    data: List[ExportTaskResponse]
    total: int


class ExportActionResponse(BaseModel):
    """导出操作响应"""
    success: bool
    message: str
    task: Optional[ExportTaskResponse] = None
    download_url: Optional[str] = None


# =============================================================
# 导出端点
# =============================================================


@router.get("", response_model=ExportListResponse)
async def list_export_tasks(
    status: Optional[str] = Query(None, description="按状态过滤"),
    data_source: Optional[str] = Query(None, description="按数据源过滤"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取导出任务列表

    支持按状态和数据源过滤。
    """
    stmt = select(ExportTask)

    if status:
        stmt = stmt.where(ExportTask.status == status)
    if data_source:
        stmt = stmt.where(ExportTask.data_source == data_source)

    stmt = stmt.order_by(ExportTask.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # 获取总数
    count_stmt = select(ExportTask)
    if status:
        count_stmt = count_stmt.where(ExportTask.status == status)
    if data_source:
        count_stmt = count_stmt.where(ExportTask.data_source == data_source)

    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return ExportListResponse(
        data=[ExportTaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.post("", response_model=ExportActionResponse)
async def create_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    创建导出任务

    任务将在后台异步执行。
    """
    export_service = ExportService(db)

    # 创建任务
    task = await export_service.create_export_task(
        data_source=request.data_source,
        export_format=request.export_format,
        filters=request.filters,
        filename=request.filename,
    )

    # 添加后台任务
    background_tasks.add_task(_execute_export_background, task.id)

    logger.info(f"创建导出任务: {task.id}, 数据源: {request.data_source.value}")

    return ExportActionResponse(
        success=True,
        message="导出任务已创建，正在后台处理",
        task=ExportTaskResponse.model_validate(task),
    )


@router.get("/{task_id}", response_model=ExportTaskResponse)
async def get_export_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取导出任务详情"""
    task = await _get_task_or_404(db, task_id)
    return ExportTaskResponse.model_validate(task)


@router.get("/{task_id}/download")
async def download_export(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    下载导出文件

    任务完成后可下载导出的文件。
    """
    task = await _get_task_or_404(db, task_id)

    if task.status.upper() != ExportStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"任务未完成: {task.status}",
        )

    if not task.file_path:
        raise HTTPException(status_code=404, detail="导出文件不存在")

    # 确定 MIME 类型 (case-insensitive)
    media_type_map = {
        ExportFormat.CSV.value: "text/csv",
        ExportFormat.JSON.value: "application/json",
        ExportFormat.EXCEL.value: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    media_type = media_type_map.get(task.export_format.upper(), "application/octet-stream")

    return FileResponse(
        path=task.file_path,
        filename=task.filename,
        media_type=media_type,
    )


@router.post("/{task_id}/retry", response_model=ExportActionResponse)
async def retry_export(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    重试失败的导出任务
    """
    task = await _get_task_or_404(db, task_id)

    if task.status.upper() != ExportStatus.FAILED.value:
        raise HTTPException(
            status_code=400,
            detail=f"只能重试失败的任务，当前状态: {task.status}",
        )

    # 重置状态
    task.status = ExportStatus.PENDING.value
    task.error_message = None
    await db.commit()
    await db.refresh(task)

    # 添加后台任务
    background_tasks.add_task(_execute_export_background, task.id)

    logger.info(f"重试导出任务: {task.id}")

    return ExportActionResponse(
        success=True,
        message="导出任务已重新提交",
        task=ExportTaskResponse.model_validate(task),
    )


@router.delete("/{task_id}", response_model=ExportActionResponse)
async def delete_export_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除导出任务及其文件"""
    task = await _get_task_or_404(db, task_id)

    # 删除文件
    if task.file_path:
        from pathlib import Path
        file_path = Path(task.file_path)
        if file_path.exists():
            file_path.unlink()

    await db.delete(task)
    await db.commit()

    logger.info(f"删除导出任务: {task_id}")

    return ExportActionResponse(
        success=True,
        message="导出任务已删除",
    )


@router.post("/cleanup", response_model=ExportActionResponse)
async def cleanup_old_exports(
    days: int = Query(7, ge=1, le=30, description="保留天数"),
    db: AsyncSession = Depends(get_db),
):
    """
    清理过期的导出任务

    删除指定天数之前的已完成任务及其文件。
    """
    export_service = ExportService(db)
    cleaned = await export_service.cleanup_old_exports(days)

    return ExportActionResponse(
        success=True,
        message=f"已清理 {cleaned} 个过期导出任务",
    )


# =============================================================
# 辅助函数
# =============================================================


async def _get_task_or_404(db: AsyncSession, task_id: int) -> ExportTask:
    """获取任务或抛出 404"""
    stmt = select(ExportTask).where(ExportTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"导出任务不存在: {task_id}")

    return task


async def _execute_export_background(task_id: int):
    """后台执行导出任务"""
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        export_service = ExportService(db)
        try:
            await export_service.execute_export(task_id)
        except Exception as e:
            logger.error(f"后台导出任务失败: {task_id}, 错误: {e}", exc_info=True)
