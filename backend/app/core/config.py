"""Application configuration using Pydantic Settings."""

from typing import List

from pydantic import MySQLDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "News Scraper API"
    VERSION: str = "1.0.0"

    # Database Configuration
    DATABASE_URL: MySQLDsn

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

    # APScheduler Configuration
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    SCHEDULER_JOBSTORE_URL: str

    # Scraper Configuration
    SCRAPER_TIMEOUT: int = 60
    SCRAPER_MAX_CONCURRENT: int = 6
    SCRAPER_DEFAULT_INTERVAL: int = 1800  # 30 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
