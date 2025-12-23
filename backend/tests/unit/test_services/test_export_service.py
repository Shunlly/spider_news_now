"""
导出服务单元测试 - Export Service Unit Tests
T147: Unit test for export service

测试导出服务功能，使用 Mock 避免依赖数据库和存储服务。
"""

import csv
import io
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.export_task import ExportFormat, ExportStatus
from app.services.export_service import DataSource, ExportService


class TestDataSourceEnum:
    """DataSource 枚举测试"""

    def test_data_source_values(self):
        """测试数据源枚举值"""
        assert DataSource.NEWS.value == "news"
        assert DataSource.SOCIAL_SESSIONS.value == "social_sessions"
        assert DataSource.SOCIAL_MESSAGES.value == "social_messages"

    def test_data_source_from_string(self):
        """测试从字符串创建数据源"""
        assert DataSource("news") == DataSource.NEWS
        assert DataSource("social_sessions") == DataSource.SOCIAL_SESSIONS
        assert DataSource("social_messages") == DataSource.SOCIAL_MESSAGES


class TestExportServiceCSV:
    """CSV 导出测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    @pytest.mark.asyncio
    async def test_export_to_csv_basic(self, export_service):
        """测试基本 CSV 导出"""
        data = [
            {"id": 1, "title": "Article 1", "url": "https://example.com/1"},
            {"id": 2, "title": "Article 2", "url": "https://example.com/2"},
        ]

        result = await export_service._export_to_csv(data, DataSource.NEWS)

        assert result is not None
        assert isinstance(result, str)
        assert "id,title,url" in result
        assert "Article 1" in result
        assert "Article 2" in result

    @pytest.mark.asyncio
    async def test_export_to_csv_empty_data(self, export_service):
        """测试空数据 CSV 导出"""
        result = await export_service._export_to_csv([], DataSource.NEWS)

        assert result == ""

    @pytest.mark.asyncio
    async def test_export_to_csv_unicode(self, export_service):
        """测试 Unicode 内容 CSV 导出"""
        data = [
            {"id": 1, "title": "中文标题", "content": "这是中文内容"},
            {"id": 2, "title": "日本語タイトル", "content": "日本語コンテンツ"},
        ]

        result = await export_service._export_to_csv(data, DataSource.NEWS)

        assert "中文标题" in result
        assert "日本語タイトル" in result

    @pytest.mark.asyncio
    async def test_export_to_csv_special_chars(self, export_service):
        """测试特殊字符 CSV 导出"""
        data = [
            {"id": 1, "title": "Title with, comma", "content": 'Quote "test"'},
        ]

        result = await export_service._export_to_csv(data, DataSource.NEWS)

        # CSV 应该正确处理逗号和引号
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["title"] == "Title with, comma"

    @pytest.mark.asyncio
    async def test_export_to_csv_preserves_field_order(self, export_service):
        """测试 CSV 保持字段顺序"""
        data = [
            {"a": 1, "b": 2, "c": 3},
        ]

        result = await export_service._export_to_csv(data, DataSource.NEWS)

        first_line = result.split("\n")[0].strip()
        assert first_line == "a,b,c"


class TestExportServiceJSON:
    """JSON 导出测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    @pytest.mark.asyncio
    async def test_export_to_json_basic(self, export_service):
        """测试基本 JSON 导出"""
        data = [
            {"id": 1, "title": "Article 1"},
            {"id": 2, "title": "Article 2"},
        ]

        result = await export_service._export_to_json(data)

        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_export_to_json_empty_data(self, export_service):
        """测试空数据 JSON 导出"""
        result = await export_service._export_to_json([])

        assert result == "[]"

    @pytest.mark.asyncio
    async def test_export_to_json_unicode(self, export_service):
        """测试 Unicode 内容 JSON 导出"""
        data = [
            {"title": "中文标题", "content": "这是中文内容"},
        ]

        result = await export_service._export_to_json(data)

        # ensure_ascii=False 应保留原始 Unicode
        assert "中文标题" in result
        parsed = json.loads(result)
        assert parsed[0]["title"] == "中文标题"

    @pytest.mark.asyncio
    async def test_export_to_json_formatted(self, export_service):
        """测试 JSON 格式化输出"""
        data = [{"id": 1}]

        result = await export_service._export_to_json(data)

        # 应该有缩进
        assert "\n" in result
        assert "  " in result

    @pytest.mark.asyncio
    async def test_export_to_json_nested_data(self, export_service):
        """测试嵌套数据 JSON 导出"""
        data = [
            {
                "id": 1,
                "metadata": {
                    "source": "twitter",
                    "tags": ["news", "tech"],
                },
            },
        ]

        result = await export_service._export_to_json(data)

        parsed = json.loads(result)
        assert parsed[0]["metadata"]["source"] == "twitter"
        assert "tech" in parsed[0]["metadata"]["tags"]


class TestExportServiceExcel:
    """Excel 导出测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    @pytest.mark.asyncio
    async def test_export_to_excel_basic(self, export_service):
        """测试基本 Excel 导出"""
        data = [
            {"id": 1, "title": "Article 1"},
            {"id": 2, "title": "Article 2"},
        ]

        result = await export_service._export_to_excel(data, DataSource.NEWS)

        assert result is not None
        assert isinstance(result, bytes)
        # Excel 文件的魔数
        assert result[:4] == b"PK\x03\x04"  # ZIP (xlsx is a zip file)

    @pytest.mark.asyncio
    async def test_export_to_excel_empty_data(self, export_service):
        """测试空数据 Excel 导出"""
        result = await export_service._export_to_excel([], DataSource.NEWS)

        assert result is not None
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_to_excel_unicode(self, export_service):
        """测试 Unicode 内容 Excel 导出"""
        data = [
            {"title": "中文标题", "content": "这是中文内容"},
        ]

        result = await export_service._export_to_excel(data, DataSource.NEWS)

        assert result is not None
        assert isinstance(result, bytes)


class TestExportServiceFilename:
    """文件名生成测试"""

    @pytest.fixture
    def mock_db(self):
        """Mock 数据库会话"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_generate_filename_csv(self, mock_db):
        """测试生成 CSV 文件名"""
        service = ExportService(db=mock_db)

        with patch.object(service, "db") as db:
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", "test-id"))

            task = await service.create_export_task(
                user_id="user-1",
                data_source=DataSource.NEWS,
                export_format=ExportFormat.CSV,
            )

            assert task.filename.endswith(".csv")
            assert "news" in task.filename

    @pytest.mark.asyncio
    async def test_generate_filename_json(self, mock_db):
        """测试生成 JSON 文件名"""
        service = ExportService(db=mock_db)

        with patch.object(service, "db") as db:
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", "test-id"))

            task = await service.create_export_task(
                user_id="user-1",
                data_source=DataSource.SOCIAL_MESSAGES,
                export_format=ExportFormat.JSON,
            )

            assert task.filename.endswith(".json")
            assert "social_messages" in task.filename

    @pytest.mark.asyncio
    async def test_custom_filename(self, mock_db):
        """测试自定义文件名"""
        service = ExportService(db=mock_db)

        with patch.object(service, "db") as db:
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", "test-id"))

            task = await service.create_export_task(
                user_id="user-1",
                data_source=DataSource.NEWS,
                export_format=ExportFormat.CSV,
                filename="custom_export.csv",
            )

            assert task.filename == "custom_export.csv"


class TestExportServiceFilters:
    """过滤条件测试"""

    def test_filters_serialization(self):
        """测试过滤条件序列化"""
        filters = {
            "source_key": "sina",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

        serialized = json.dumps(filters)
        deserialized = json.loads(serialized)

        assert deserialized == filters

    def test_filters_empty(self):
        """测试空过滤条件"""
        filters = {}
        serialized = json.dumps(filters)

        assert serialized == "{}"


class TestExportServiceFileStorage:
    """文件存储测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    @pytest.mark.asyncio
    async def test_save_export_file_local(self, export_service, tmp_path):
        """测试本地文件存储"""
        with patch("app.services.export_service.settings") as mock_settings:
            mock_settings.DATA_DIR = str(tmp_path)

            file_path = await export_service._save_export_file(
                content="test content",
                filename="test.csv",
                content_type="text/csv",
            )

            assert file_path is not None
            assert "test.csv" in file_path

    @pytest.mark.asyncio
    async def test_save_export_file_bytes(self, export_service, tmp_path):
        """测试字节内容存储"""
        with patch("app.services.export_service.settings") as mock_settings:
            mock_settings.DATA_DIR = str(tmp_path)

            file_path = await export_service._save_export_file(
                content=b"binary content",
                filename="test.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            assert file_path is not None

    @pytest.mark.asyncio
    async def test_save_export_file_with_storage_service(self):
        """测试使用存储服务"""
        mock_db = AsyncMock()
        mock_storage = AsyncMock()
        mock_storage.upload = AsyncMock()

        service = ExportService(db=mock_db, storage_service=mock_storage)

        file_path = await service._save_export_file(
            content="test content",
            filename="test.csv",
            content_type="text/csv",
        )

        mock_storage.upload.assert_called_once()
        assert "exports/test.csv" in file_path


class TestExportTaskStatus:
    """导出任务状态测试"""

    def test_export_status_values(self):
        """测试导出状态枚举值"""
        assert ExportStatus.PENDING.value == "PENDING"
        assert ExportStatus.PROCESSING.value == "PROCESSING"
        assert ExportStatus.COMPLETED.value == "COMPLETED"
        assert ExportStatus.FAILED.value == "FAILED"

    def test_export_format_values(self):
        """测试导出格式枚举值"""
        assert ExportFormat.CSV.value == "CSV"
        assert ExportFormat.JSON.value == "JSON"
        assert ExportFormat.EXCEL.value == "EXCEL"


class TestExportServiceCleanup:
    """导出清理测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    @pytest.mark.asyncio
    async def test_cleanup_old_exports(self, export_service):
        """测试清理过期导出"""
        # Mock 查询结果
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.file_path = "/tmp/test.csv"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]

        export_service.db.execute = AsyncMock(return_value=mock_result)
        export_service.db.delete = AsyncMock()
        export_service.db.commit = AsyncMock()

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.unlink"):
                cleaned = await export_service.cleanup_old_exports(days=7)

        # 验证调用
        assert export_service.db.delete.called

    @pytest.mark.asyncio
    async def test_cleanup_with_storage_service(self):
        """测试使用存储服务清理"""
        mock_db = AsyncMock()
        mock_storage = AsyncMock()
        mock_storage.delete = AsyncMock()

        service = ExportService(db=mock_db, storage_service=mock_storage)

        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.file_path = "exports/test.csv"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_task]

        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.delete = AsyncMock()
        service.db.commit = AsyncMock()

        await service.cleanup_old_exports(days=7)

        mock_storage.delete.assert_called_once_with("exports/test.csv")


class TestExportServiceWorkbookHelper:
    """Workbook 辅助方法测试"""

    @pytest.fixture
    def export_service(self):
        """创建导出服务实例"""
        mock_db = AsyncMock()
        return ExportService(db=mock_db)

    def test_workbook_to_bytes(self, export_service):
        """测试 Workbook 转换为字节"""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Test"

        result = export_service._workbook_to_bytes(wb)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Excel 文件的魔数
        assert result[:4] == b"PK\x03\x04"
