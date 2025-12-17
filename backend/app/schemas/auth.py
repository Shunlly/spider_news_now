"""
认证相关 Pydantic Schema
Auth Pydantic Schemas for Login/Captcha Request/Response

定义登录、验证码等认证相关的请求和响应模型。
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


# ============== Captcha Schemas ==============


class CaptchaResponse(BaseModel):
    """验证码响应 Schema"""
    token: str = Field(
        ...,
        description="验证码 Token（UUID）"
    )
    image: str = Field(
        ...,
        description="验证码图片 Base64"
    )


class CaptchaVerifyRequest(BaseModel):
    """验证码验证请求 Schema"""
    token: str = Field(
        ...,
        description="验证码 Token"
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="用户输入的验证码"
    )


class CaptchaVerifyResponse(BaseModel):
    """验证码验证响应 Schema"""
    success: bool = Field(
        ...,
        description="验证是否成功"
    )
    verified_token: Optional[str] = Field(
        None,
        description="验证通过后的 Token，用于登录请求"
    )
    message: Optional[str] = Field(
        None,
        description="验证结果消息"
    )


# ============== Login Schemas ==============


class LoginRequest(BaseModel):
    """登录请求 Schema"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="密码"
    )
    captcha_token: str = Field(
        ...,
        description="验证码验证通过后的 Token"
    )


class LoginResponse(BaseModel):
    """登录响应 Schema"""
    access_token: str = Field(
        ...,
        description="JWT Access Token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token 类型"
    )
    expires_in: int = Field(
        ...,
        description="Token 有效期（秒）"
    )
    user: UserResponse = Field(
        ...,
        description="当前用户信息"
    )


# ============== Token Schemas ==============


class TokenResponse(BaseModel):
    """Token 刷新响应 Schema"""
    access_token: str = Field(
        ...,
        description="新的 JWT Access Token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token 类型"
    )
    expires_in: int = Field(
        ...,
        description="Token 有效期（秒）"
    )


class TokenPayload(BaseModel):
    """JWT Token 载荷 Schema（内部使用）"""
    sub: str = Field(..., description="Subject（用户ID）")
    exp: int = Field(..., description="过期时间戳")
    type: str = Field(default="access", description="Token 类型")


# ============== Message Schemas ==============


class MessageResponse(BaseModel):
    """通用消息响应 Schema"""
    message: str = Field(
        ...,
        description="消息内容"
    )


class ErrorResponse(BaseModel):
    """错误响应 Schema"""
    detail: str = Field(
        ...,
        description="错误详情"
    )
    error_code: Optional[str] = Field(
        None,
        description="错误代码"
    )
