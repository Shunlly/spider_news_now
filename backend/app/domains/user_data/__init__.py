"""
User Data Domain - 用户数据关系域

管理用户与数据之间的关系：
- 收藏/书签
- 用户标签
- 用户笔记
"""

from app.domains.user_data.models import UserDataRelation
from app.domains.user_data.service import (
    UserDataService,
    get_user_data_service,
)

__all__ = [
    "UserDataRelation",
    "UserDataService",
    "get_user_data_service",
]
