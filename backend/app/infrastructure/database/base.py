"""
SQLAlchemy Declarative Base - 数据模型声明式基类

所有数据库模型都应继承此基类。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    数据库模型声明式基类

    所有 ORM 模型应继承此类。提供：
    - 自动表名生成（可选）
    - 统一的元数据配置
    - 公共列定义（可扩展）
    """
    pass
