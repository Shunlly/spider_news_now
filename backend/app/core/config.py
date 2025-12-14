"""
应用配置 - 使用 Pydantic Settings 管理环境变量
Application configuration using Pydantic Settings.
"""

from typing import List, Literal, Optional

from pydantic import MySQLDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类 - 从环境变量加载配置
    Application settings loaded from environment variables.
    """

    # ========== API 配置 ==========
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "News Scraper API"
    VERSION: str = "2.0.0"

    # ========== 数据库配置 ==========
    DATABASE_URL: MySQLDsn

    # ========== CORS 配置 ==========
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """解析逗号分隔的 CORS 来源列表"""
        return [origin.strip() for origin in v.split(",")]

    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"

    # ========== APScheduler 配置 ==========
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    SCHEDULER_JOBSTORE_URL: str = ""

    # ========== 爬虫配置 ==========
    SCRAPER_TIMEOUT: int = 60
    SCRAPER_MAX_CONCURRENT: int = 6
    SCRAPER_DEFAULT_INTERVAL: int = 1800  # 30 分钟

    # ========== Redis 配置 (去重和缓存) ==========
    REDIS_URL: str = "redis://localhost:6379/0"
    # Bloom Filter 配置 - 预期容量 1000 万，误判率 0.1%
    BLOOM_FILTER_CAPACITY: int = 10_000_000
    BLOOM_FILTER_ERROR_RATE: float = 0.001

    # ========== Meilisearch 配置 (全文检索) ==========
    MEILISEARCH_URL: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str = ""

    # ========== 存储配置 (对象存储) ==========
    # 存储后端类型: minio, s3, oss, local
    STORAGE_BACKEND: Literal["minio", "s3", "oss", "local"] = "local"

    # MinIO / S3 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "news-scraper"
    MINIO_SECURE: bool = False

    # 阿里云 OSS 配置 (可选)
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = ""

    # 本地存储配置
    LOCAL_STORAGE_PATH: str = "./storage"

    # ========== Twitter API 配置 (可选) ==========
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None

    # ========== Telegram 配置 (可选) ==========
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None

    # ========== 安全配置 ==========
    # 用于凭证加密的密钥 (生产环境必须设置)
    SECRET_KEY: str = "development_secret_key_change_in_production"
    # Fernet 加密密钥 (用于敏感数据加密)
    FERNET_KEY: Optional[str] = None

    # ========== 导出配置 ==========
    EXPORT_DIR: str = "./exports"
    EXPORT_MAX_ROWS: int = 100000
    EXPORT_CLEANUP_DAYS: int = 7

    # ========== 数据目录配置 ==========
    DATA_DIR: str = "./data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# 全局配置实例
settings = Settings()
