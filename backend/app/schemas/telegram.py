"""
Telegram Pydantic Schema
Telegram 数据请求/响应模型

提供 Telegram 认证、频道管理和消息获取的数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================
# 认证相关模型
# =============================================================

class TelegramInitRequest(BaseModel):
    """初始化 Telegram 客户端请求"""
    api_id: int = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API Hash")
    string_session: str | None = Field("", description="StringSession（可选，用于恢复会话）")
    proxy: dict[str, Any] | None = Field(None, description="代理配置")


class TelegramSendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., description="手机号码（带国家代码，如 +86xxx）")


class TelegramSignInRequest(BaseModel):
    """验证登录请求"""
    phone: str = Field(..., description="手机号码")
    code: str = Field(..., description="验证码")
    phone_code_hash: str = Field(..., description="send_code 返回的 hash")
    password: str | None = Field(None, description="两步验证密码（如果启用）")


class TelegramConnectRequest(BaseModel):
    """使用 StringSession 连接请求"""
    api_id: int = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API Hash")
    string_session: str = Field(..., description="之前保存的 session 字符串")
    proxy: dict[str, Any] | None = Field(None, description="代理配置")


# =============================================================
# 频道/对话相关模型
# =============================================================

class TelegramDialogResponse(BaseModel):
    """对话响应模型"""
    id: int = Field(..., description="对话 ID")
    title: str = Field(..., description="对话标题")
    username: str | None = Field(None, description="用户名")
    type: str | None = Field(None, description="对话类型: channel/group/user")
    participant_count: int | None = Field(None, description="参与者数量")
    unread_count: int = Field(0, description="未读消息数")
    last_message_date: str | None = Field(None, description="最后消息时间")
    is_pinned: bool = Field(False, description="是否置顶")


class TelegramEntityResponse(BaseModel):
    """频道/实体响应模型"""
    id: int = Field(..., description="实体 ID")
    title: str = Field(..., description="标题/名称")
    username: str | None = Field(None, description="用户名")
    type: str | None = Field(None, description="类型: channel/group/user")
    participant_count: int | None = Field(None, description="参与者数量")
    description: str | None = Field(None, description="描述")


class TelegramSearchRequest(BaseModel):
    """搜索频道请求"""
    username: str = Field(..., description="用户名或链接（不带@）")


class TelegramSearchPublicRequest(BaseModel):
    """关键词搜索请求"""
    query: str = Field(..., description="搜索关键词（支持中文）")
    limit: int = Field(20, ge=1, le=50, description="返回数量限制")


class TelegramJoinRequest(BaseModel):
    """加入频道请求"""
    channel: str = Field(..., description="频道用户名或链接")


class TelegramLeaveRequest(BaseModel):
    """退出频道请求"""
    channel_id: int = Field(..., description="频道 ID")


# =============================================================
# 消息相关模型
# =============================================================

class TelegramMessageResponse(BaseModel):
    """消息响应模型"""
    id: int = Field(..., description="消息 ID")
    date: str | None = Field(None, description="发布时间")
    text: str | None = Field(None, description="消息文本")
    html: str | None = Field(None, description="HTML 格式内容")
    views: int | None = Field(None, description="浏览次数")
    forwards: int | None = Field(None, description="转发次数")
    reply_to_id: int | None = Field(None, description="回复消息 ID")
    media_type: str | None = Field(None, description="媒体类型")
    urls: list[str] = Field(default_factory=list, description="提取的 URL 列表")
    sender_id: int | None = Field(None, description="发送者 ID")


class TelegramMessagesRequest(BaseModel):
    """获取消息请求"""
    channel_id: int = Field(..., description="频道 ID")
    limit: int = Field(100, ge=1, le=1000, description="消息数量限制")
    offset_id: int = Field(0, description="从指定消息 ID 开始获取")
    min_date: datetime | None = Field(None, description="最早日期")
    max_date: datetime | None = Field(None, description="最晚日期")


# =============================================================
# 通用响应模型
# =============================================================

class TelegramUserInfo(BaseModel):
    """用户信息"""
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None


class TelegramBaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")


class TelegramInitResponse(TelegramBaseResponse):
    """初始化响应"""
    pass


class TelegramSendCodeResponse(TelegramBaseResponse):
    """发送验证码响应"""
    phone_code_hash: str | None = Field(None, description="验证码 hash")


class TelegramSignInResponse(TelegramBaseResponse):
    """登录响应"""
    string_session: str | None = Field(None, description="StringSession 字符串")
    user_info: TelegramUserInfo | None = Field(None, description="用户信息")
    need_password: bool = Field(False, description="是否需要两步验证密码")


class TelegramConnectResponse(TelegramBaseResponse):
    """连接响应"""
    user_info: TelegramUserInfo | None = Field(None, description="用户信息")


class TelegramDialogsResponse(TelegramBaseResponse):
    """对话列表响应"""
    dialogs: list[TelegramDialogResponse] = Field(default_factory=list)
    total: int = Field(0, description="总数")


class TelegramSearchResponse(TelegramBaseResponse):
    """搜索响应"""
    entity: TelegramEntityResponse | None = Field(None, description="找到的实体")


class TelegramSearchPublicResponse(TelegramBaseResponse):
    """关键词搜索响应"""
    entities: list[TelegramEntityResponse] = Field(default_factory=list, description="搜索结果列表")


class TelegramMessagesResponse(TelegramBaseResponse):
    """消息列表响应"""
    messages: list[TelegramMessageResponse] = Field(default_factory=list)
    total: int = Field(0, description="返回的消息数")


class TelegramStatusResponse(BaseModel):
    """状态响应"""
    connected: bool = Field(..., description="是否已连接")
    user_info: TelegramUserInfo | None = Field(None, description="当前用户信息")
