"""
Telegram Service - 基于 Telethon MTProto API 的 Telegram 服务

功能：
1. 用户账号认证（StringSession）
2. 获取已加入的频道/群组列表
3. 搜索频道
4. 加入/退出频道
5. 获取历史消息
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import (
    Channel, Chat, User,
    Message, MessageMediaPhoto, MessageMediaDocument,
    MessageEntityTextUrl, MessageEntityUrl,
    KeyboardButtonUrl,
)
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    ChannelPrivateError,
    UsernameNotOccupiedError,
    FloodWaitError,
)

from app.core.logging import get_logger

logger = get_logger(__name__)


class TelegramService:
    """
    Telegram 服务类

    使用 Telethon 的 MTProto API 实现完整的 Telegram 功能。
    """

    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.string_session: Optional[str] = None
        self._connected = False
        self._user_info: Optional[Dict] = None

    async def init_client(
        self,
        api_id: int,
        api_hash: str,
        string_session: str = "",
        proxy: Optional[Dict] = None
    ) -> bool:
        """
        初始化 Telegram 客户端

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            string_session: StringSession 字符串（可选，用于恢复会话）
            proxy: 代理配置 {"type": "socks5", "host": "...", "port": ...}

        Returns:
            是否成功初始化
        """
        try:
            self.api_id = api_id
            self.api_hash = api_hash
            self.string_session = string_session

            # 构建客户端参数
            session = StringSession(string_session) if string_session else StringSession()

            client_params = {
                "session": session,
                "api_id": api_id,
                "api_hash": api_hash,
            }

            # 配置代理
            if proxy:
                proxy_type = proxy.get("type", "socks5")
                if proxy_type == "socks5":
                    import socks
                    client_params["proxy"] = (
                        socks.SOCKS5,
                        proxy.get("host"),
                        proxy.get("port"),
                        True,  # rdns
                        proxy.get("username"),
                        proxy.get("password"),
                    )

            self.client = TelegramClient(**client_params)
            await self.client.connect()

            logger.info("Telegram client initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False

    async def send_code(self, phone: str) -> Dict[str, Any]:
        """
        发送登录验证码

        Args:
            phone: 手机号码（带国家代码，如 +86xxx）

        Returns:
            {"success": bool, "phone_code_hash": str, "message": str}
        """
        if not self.client:
            return {"success": False, "message": "Client not initialized"}

        try:
            result = await self.client.send_code_request(phone)
            return {
                "success": True,
                "phone_code_hash": result.phone_code_hash,
                "message": "验证码已发送",
            }
        except FloodWaitError as e:
            return {
                "success": False,
                "message": f"请求过于频繁，请等待 {e.seconds} 秒后重试",
            }
        except Exception as e:
            logger.error(f"Failed to send code: {e}")
            return {"success": False, "message": str(e)}

    async def sign_in(
        self,
        phone: str,
        code: str,
        phone_code_hash: str,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证登录

        Args:
            phone: 手机号码
            code: 验证码
            phone_code_hash: send_code 返回的 hash
            password: 两步验证密码（如果启用）

        Returns:
            {"success": bool, "string_session": str, "user_info": dict, "message": str}
        """
        if not self.client:
            return {"success": False, "message": "Client not initialized"}

        try:
            await self.client.sign_in(phone, code, phone_code_hash=phone_code_hash)

            # 获取用户信息
            me = await self.client.get_me()
            self._user_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone,
            }
            self._connected = True

            # 获取 StringSession
            session_string = self.client.session.save()

            return {
                "success": True,
                "string_session": session_string,
                "user_info": self._user_info,
                "message": "登录成功",
            }

        except SessionPasswordNeededError:
            if password:
                try:
                    await self.client.sign_in(password=password)
                    me = await self.client.get_me()
                    self._user_info = {
                        "id": me.id,
                        "first_name": me.first_name,
                        "last_name": me.last_name,
                        "username": me.username,
                        "phone": me.phone,
                    }
                    self._connected = True
                    session_string = self.client.session.save()
                    return {
                        "success": True,
                        "string_session": session_string,
                        "user_info": self._user_info,
                        "message": "登录成功",
                    }
                except Exception as e:
                    return {"success": False, "message": f"两步验证失败: {e}"}
            else:
                return {
                    "success": False,
                    "need_password": True,
                    "message": "需要两步验证密码",
                }

        except PhoneCodeInvalidError:
            return {"success": False, "message": "验证码错误"}

        except PhoneCodeExpiredError:
            return {"success": False, "message": "验证码已过期"}

        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            return {"success": False, "message": str(e)}

    async def connect_with_session(self, string_session: str) -> Dict[str, Any]:
        """
        使用已有的 StringSession 连接

        Args:
            string_session: 之前保存的 session 字符串

        Returns:
            {"success": bool, "user_info": dict, "message": str}
        """
        if not self.client:
            return {"success": False, "message": "Client not initialized"}

        try:
            if not await self.client.is_user_authorized():
                return {"success": False, "message": "Session 无效或已过期"}

            me = await self.client.get_me()
            self._user_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone,
            }
            self._connected = True

            return {
                "success": True,
                "user_info": self._user_info,
                "message": "连接成功",
            }

        except Exception as e:
            logger.error(f"Connect with session failed: {e}")
            return {"success": False, "message": str(e)}

    async def get_dialogs(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取已加入的对话列表（频道、群组、私聊）

        Args:
            limit: 返回数量限制
            offset: 偏移量
            filter_type: 过滤类型 "channel" | "group" | "user" | None

        Returns:
            对话列表
        """
        if not self.client or not self._connected:
            return []

        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs(limit=limit + offset):
                if len(dialogs) >= limit:
                    break

                entity = dialog.entity
                dialog_type = None
                participant_count = None

                if isinstance(entity, Channel):
                    if entity.megagroup:
                        dialog_type = "group"
                    else:
                        dialog_type = "channel"
                    participant_count = getattr(entity, "participants_count", None)
                elif isinstance(entity, Chat):
                    dialog_type = "group"
                    participant_count = getattr(entity, "participants_count", None)
                elif isinstance(entity, User):
                    dialog_type = "user"

                # 应用过滤
                if filter_type and dialog_type != filter_type:
                    continue

                dialogs.append({
                    "id": entity.id,
                    "title": dialog.title or getattr(entity, "first_name", ""),
                    "username": getattr(entity, "username", None),
                    "type": dialog_type,
                    "participant_count": participant_count,
                    "unread_count": dialog.unread_count,
                    "last_message_date": dialog.date.isoformat() if dialog.date else None,
                    "is_pinned": dialog.pinned,
                })

            return dialogs

        except Exception as e:
            logger.error(f"Failed to get dialogs: {e}")
            return []

    async def search_channel(self, username: str) -> Dict[str, Any]:
        """
        搜索频道/用户

        Args:
            username: 用户名（不带@）

        Returns:
            {"success": bool, "entity": dict, "message": str}
        """
        if not self.client or not self._connected:
            return {"success": False, "message": "Not connected"}

        try:
            # 清理用户名
            username = username.lstrip("@").strip()
            if username.startswith("https://t.me/"):
                username = username.replace("https://t.me/", "")

            # 尝试解析用户名
            result = await self.client(ResolveUsernameRequest(username))

            entity = None
            entity_type = None

            # 优先获取频道/群组
            if result.chats:
                entity = result.chats[0]
                if isinstance(entity, Channel):
                    entity_type = "group" if entity.megagroup else "channel"
                else:
                    entity_type = "group"
            elif result.users:
                entity = result.users[0]
                entity_type = "user"

            if entity:
                return {
                    "success": True,
                    "entity": {
                        "id": entity.id,
                        "title": getattr(entity, "title", None) or getattr(entity, "first_name", ""),
                        "username": getattr(entity, "username", None),
                        "type": entity_type,
                        "participant_count": getattr(entity, "participants_count", None),
                        "description": getattr(entity, "about", None),
                    },
                    "message": "找到频道",
                }
            else:
                return {"success": False, "message": "未找到频道"}

        except UsernameNotOccupiedError:
            return {"success": False, "message": "用户名不存在"}
        except Exception as e:
            logger.error(f"Search channel failed: {e}")
            return {"success": False, "message": str(e)}

    async def join_channel(self, channel: str) -> Dict[str, Any]:
        """
        加入频道

        Args:
            channel: 频道用户名或链接

        Returns:
            {"success": bool, "message": str}
        """
        if not self.client or not self._connected:
            return {"success": False, "message": "Not connected"}

        try:
            # 解析频道
            channel = channel.lstrip("@").strip()
            if "t.me/" in channel:
                channel = channel.split("t.me/")[-1]

            entity = await self.client.get_entity(channel)
            await self.client(JoinChannelRequest(entity))

            return {"success": True, "message": "加入成功"}

        except ChannelPrivateError:
            return {"success": False, "message": "这是一个私有频道，需要邀请链接"}
        except Exception as e:
            logger.error(f"Join channel failed: {e}")
            return {"success": False, "message": str(e)}

    async def leave_channel(self, channel_id: int) -> Dict[str, Any]:
        """
        退出频道

        Args:
            channel_id: 频道 ID

        Returns:
            {"success": bool, "message": str}
        """
        if not self.client or not self._connected:
            return {"success": False, "message": "Not connected"}

        try:
            entity = await self.client.get_entity(channel_id)
            await self.client(LeaveChannelRequest(entity))

            return {"success": True, "message": "退出成功"}

        except Exception as e:
            logger.error(f"Leave channel failed: {e}")
            return {"success": False, "message": str(e)}

    async def get_messages(
        self,
        channel_id: int,
        limit: int = 100,
        offset_id: int = 0,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取频道历史消息

        Args:
            channel_id: 频道 ID
            limit: 消息数量限制
            offset_id: 从指定消息 ID 开始获取
            min_date: 最早日期
            max_date: 最晚日期

        Returns:
            消息列表
        """
        if not self.client or not self._connected:
            return []

        try:
            entity = await self.client.get_entity(channel_id)
            messages = []

            async for msg in self.client.iter_messages(
                entity,
                limit=limit,
                offset_id=offset_id,
                offset_date=max_date,
            ):
                # 检查日期范围
                if min_date and msg.date.replace(tzinfo=None) < min_date:
                    break

                # 解析消息
                parsed = self._parse_message(msg)
                if parsed:
                    messages.append(parsed)

            return messages

        except Exception as e:
            logger.error(f"Get messages failed: {e}")
            return []

    def _parse_message(self, msg: Message) -> Optional[Dict[str, Any]]:
        """
        解析消息

        Args:
            msg: Telethon Message 对象

        Returns:
            解析后的消息字典
        """
        if not msg or not msg.message:
            return None

        try:
            # 提取媒体信息
            media_type = None

            if msg.media:
                if isinstance(msg.media, MessageMediaPhoto):
                    media_type = "photo"
                elif isinstance(msg.media, MessageMediaDocument):
                    doc = msg.media.document
                    if doc:
                        for attr in doc.attributes:
                            if hasattr(attr, "file_name"):
                                media_type = "document"
                            elif hasattr(attr, "duration"):
                                media_type = "video" if hasattr(attr, "w") else "audio"

            # 提取 URL
            urls = []
            if msg.entities:
                for entity in msg.entities:
                    if isinstance(entity, MessageEntityTextUrl):
                        urls.append(entity.url)
                    elif isinstance(entity, MessageEntityUrl):
                        url = msg.message[entity.offset:entity.offset + entity.length]
                        urls.append(url)

            # 提取按钮 URL
            if msg.reply_markup:
                if hasattr(msg.reply_markup, "rows"):
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonUrl):
                                urls.append(button.url)

            # 格式化为 HTML
            html_content = self._format_to_html(msg)

            return {
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "text": msg.message,
                "html": html_content,
                "views": msg.views,
                "forwards": msg.forwards,
                "reply_to_id": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
                "media_type": media_type,
                "urls": urls,
                "sender_id": msg.sender_id,
            }

        except Exception as e:
            logger.warning(f"Failed to parse message: {e}")
            return None

    def _format_to_html(self, msg: Message) -> str:
        """
        将消息格式化为 HTML

        Args:
            msg: Telethon Message 对象

        Returns:
            HTML 格式的消息内容
        """
        if not msg.message:
            return ""

        text = msg.message
        if not msg.entities:
            return text

        # 按 offset 倒序处理，避免索引偏移
        entities = sorted(msg.entities, key=lambda e: e.offset, reverse=True)

        for entity in entities:
            start = entity.offset
            end = entity.offset + entity.length
            content = text[start:end]

            if hasattr(entity, "url"):
                # TextUrl
                replacement = f'<a href="{entity.url}">{content}</a>'
            elif entity.__class__.__name__ == "MessageEntityBold":
                replacement = f"<strong>{content}</strong>"
            elif entity.__class__.__name__ == "MessageEntityItalic":
                replacement = f"<em>{content}</em>"
            elif entity.__class__.__name__ == "MessageEntityCode":
                replacement = f"<code>{content}</code>"
            elif entity.__class__.__name__ == "MessageEntityPre":
                replacement = f"<pre>{content}</pre>"
            elif entity.__class__.__name__ == "MessageEntityUrl":
                replacement = f'<a href="{content}">{content}</a>'
            elif entity.__class__.__name__ == "MessageEntityMention":
                replacement = f'<a href="https://t.me/{content[1:]}">{content}</a>'
            elif entity.__class__.__name__ == "MessageEntityHashtag":
                replacement = f"<span class='hashtag'>{content}</span>"
            else:
                continue

            text = text[:start] + replacement + text[end:]

        return text

    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self._connected = False
            self._user_info = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @property
    def user_info(self) -> Optional[Dict]:
        """当前用户信息"""
        return self._user_info


# 全局服务实例
_telegram_service: Optional[TelegramService] = None


def get_telegram_service() -> TelegramService:
    """获取 Telegram 服务实例"""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service
