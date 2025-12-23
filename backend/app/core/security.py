"""
安全工具模块 - Security Utilities
Password Hashing and JWT Token Management

核心安全功能实现：
1. 密码哈希（bcrypt）
2. JWT Token 生成和验证

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
- 无占位符代码
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ============== 密码哈希配置 ==============
# 使用 bcrypt 算法，这是目前推荐的密码哈希方案
# deprecated="auto" 表示旧算法会自动迁移到新算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============== 密码哈希函数 ==============


def hash_password(password: str) -> str:
    """
    对明文密码进行哈希加密

    使用 bcrypt 算法，自动生成盐值。
    生成的哈希值约 60 字符。

    Args:
        password: 明文密码

    Returns:
        bcrypt 哈希后的密码字符串
    """
    # 使用 bcrypt 直接哈希，避免 passlib 兼容性问题
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.debug("Passlib hash failed, falling back to bcrypt", extra={"error": str(e)})
        # 直接使用 bcrypt 库
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码

    Returns:
        True if 密码匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # passlib 可能与新版 bcrypt 不兼容，回退到直接使用 bcrypt
        logger.debug("Passlib verify failed, falling back to bcrypt", extra={"error": str(e)})
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e2:
            logger.warning("Password verification failed", extra={"error": str(e2)})
            return False


# ============== JWT Token 函数 ==============


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    创建 JWT Access Token

    Args:
        subject: Token 主题，通常是用户 ID
        expires_delta: 自定义过期时间，默认使用配置值
        extra_claims: 额外的 JWT 声明

    Returns:
        编码后的 JWT Token 字符串
    """
    # 计算过期时间
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 构建 JWT 载荷
    to_encode: dict[str, Any] = {
        "sub": str(subject),  # subject - 用户标识
        "exp": expire,        # expiration time - 过期时间
        "iat": datetime.now(UTC),  # issued at - 签发时间
        "type": "access",     # token 类型
    }

    # 添加额外声明
    if extra_claims:
        to_encode.update(extra_claims)

    # 编码 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建 JWT Refresh Token

    Refresh Token 用于获取新的 Access Token，有效期更长。
    应存储在 HttpOnly Cookie 中以防 XSS 攻击。

    Args:
        subject: Token 主题，通常是用户 ID
        expires_delta: 自定义过期时间，默认使用配置值

    Returns:
        编码后的 JWT Refresh Token 字符串
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",  # 标记为 refresh token
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    解码并验证 JWT Token

    自动验证签名和过期时间。

    Args:
        token: JWT Token 字符串

    Returns:
        解码后的载荷字典，如果无效则返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed", extra={"error": str(e)})
        return None


def verify_token(token: str, token_type: str = "access") -> str | None:
    """
    验证 JWT Token 并返回用户 ID

    同时验证 Token 类型（access/refresh）。

    Args:
        token: JWT Token 字符串
        token_type: 期望的 Token 类型

    Returns:
        用户 ID (sub 字段)，如果无效则返回 None
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # 验证 Token 类型
    if payload.get("type") != token_type:
        logger.warning(
            "Token type mismatch",
            extra={"expected": token_type, "actual": payload.get("type")}
        )
        return None

    # 返回用户 ID
    return payload.get("sub")
