"""News Now 配置"""
from typing import Dict, Optional

from pydantic import Field

from src.app.data_sources.config_base import BaseDataSourceConfig, load_data_source_configs


class NewsNowConfig(BaseDataSourceConfig):
    config_name: str = Field("sync_news_now", description="配置名称")
    base_url: str = Field("https://newsnow.busiyi.world/api", description="API基础URL")

    message_type_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "text": "TEXT",
            "image": "IMAGE",
            "file": "FILE",
            "audio": "AUDIO",
            "video": "VIDEO",
            "system": "SYSTEM"
        },
        description="消息类型映射"
    )

    role_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "user": "USER",
            "bot": "BOT",
            "system": "SYSTEM",
            "admin": "ADMIN"
        },
        description="角色映射"
    )


def _build_news_now_config(record) -> Dict[str, Optional[str]]:
    cfg = getattr(record, 'config', {}) or {}
    base_url = cfg.get('apiUrl')
    return {
        'base_url': base_url.rstrip('/') if isinstance(base_url, str) else None,
        'app_secret': cfg.get('token')
    }


def get_config(source_type: str) -> list[NewsNowConfig]:
    """获取 News Now 配置"""
    return load_data_source_configs(
        source_type=source_type,
        config_cls=NewsNowConfig,
        builder=_build_news_now_config,
        log_name="News Now"
    )
