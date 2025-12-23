"""
图形验证码服务 - Image Captcha Service
PIL Image Generation + Redis Storage

提供数字图形验证码功能：
1. 生成带干扰线的验证码图片
2. Redis 存储验证码状态（TTL 5分钟）
3. 验证用户输入的验证码

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

import base64
import io
import random
import secrets
import string
import uuid
from dataclasses import dataclass

import redis.asyncio as redis
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 验证码图片尺寸
CAPTCHA_WIDTH = 150
CAPTCHA_HEIGHT = 50
# 验证码字符数量
CAPTCHA_LENGTH = 4


@dataclass
class CaptchaResult:
    """验证码生成结果"""
    token: str
    image_base64: str


@dataclass
class CaptchaState:
    """验证码存储状态（Redis）"""
    code: str
    attempts: int = 0
    verified: bool = False


class CaptchaService:
    """
    图形验证码服务

    生成数字图形验证码：
    - 随机数字组合
    - 干扰线和噪点
    - 用户输入验证
    """

    def __init__(self):
        """初始化 Redis 连接"""
        self._redis: redis.Redis | None = None

    async def get_redis(self) -> redis.Redis:
        """获取 Redis 连接（延迟初始化）"""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    # ============== 图片生成 ==============

    def _generate_code(self) -> str:
        """生成随机验证码（纯数字）"""
        return ''.join(random.choices(string.digits, k=CAPTCHA_LENGTH))

    def _get_font(self, size: int = 36) -> ImageFont.FreeTypeFont:
        """获取字体"""
        # 尝试使用系统字体
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue

        # 回退到默认字体
        return ImageFont.load_default()

    def _generate_captcha_image(self, code: str) -> Image.Image:
        """
        生成验证码图片

        Args:
            code: 验证码文本

        Returns:
            PIL Image 对象
        """
        # 创建图片
        img = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 绘制背景噪点
        for _ in range(100):
            x = random.randint(0, CAPTCHA_WIDTH)
            y = random.randint(0, CAPTCHA_HEIGHT)
            color = (
                random.randint(150, 230),
                random.randint(150, 230),
                random.randint(150, 230)
            )
            draw.point((x, y), fill=color)

        # 绘制干扰线
        for _ in range(5):
            x1 = random.randint(0, CAPTCHA_WIDTH)
            y1 = random.randint(0, CAPTCHA_HEIGHT)
            x2 = random.randint(0, CAPTCHA_WIDTH)
            y2 = random.randint(0, CAPTCHA_HEIGHT)
            color = (
                random.randint(100, 180),
                random.randint(100, 180),
                random.randint(100, 180)
            )
            draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

        # 绘制验证码文字
        font = self._get_font(36)

        # 计算每个字符的位置
        char_width = CAPTCHA_WIDTH // (CAPTCHA_LENGTH + 1)

        for i, char in enumerate(code):
            # 随机颜色（深色）
            color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )

            # 随机偏移和旋转
            x = char_width * (i + 0.5) + random.randint(-5, 5)
            y = random.randint(5, 15)

            # 绘制字符
            draw.text((x, y), char, font=font, fill=color)

        # 轻微模糊
        img = img.filter(ImageFilter.SMOOTH)

        return img

    def _image_to_base64(self, img: Image.Image) -> str:
        """将 PIL Image 转换为 Base64 字符串"""
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    # ============== Redis 存储 ==============

    def _get_redis_key(self, token: str) -> str:
        """生成 Redis 键名"""
        return f"captcha:{token}"

    async def _store_captcha_state(self, token: str, state: CaptchaState) -> None:
        """
        存储验证码状态到 Redis

        TTL 设置为配置的过期时间（默认 5 分钟）
        """
        r = await self.get_redis()
        key = self._get_redis_key(token)

        await r.hset(key, mapping={
            'code': state.code,
            'attempts': str(state.attempts),
            'verified': '1' if state.verified else '0'
        })

        await r.expire(key, settings.CAPTCHA_EXPIRE_SECONDS)
        logger.debug("Captcha state stored", extra={"token": token, "ttl": settings.CAPTCHA_EXPIRE_SECONDS})

    async def _get_captcha_state(self, token: str) -> CaptchaState | None:
        """从 Redis 获取验证码状态"""
        r = await self.get_redis()
        key = self._get_redis_key(token)

        data = await r.hgetall(key)
        if not data:
            return None

        return CaptchaState(
            code=data['code'],
            attempts=int(data.get('attempts', 0)),
            verified=data.get('verified') == '1'
        )

    async def _update_captcha_attempts(self, token: str, attempts: int) -> None:
        """更新验证码尝试次数"""
        r = await self.get_redis()
        key = self._get_redis_key(token)
        await r.hset(key, 'attempts', str(attempts))

    async def _mark_captcha_verified(self, token: str) -> str:
        """
        标记验证码为已验证，返回验证令牌
        """
        r = await self.get_redis()
        key = self._get_redis_key(token)

        verified_token = secrets.token_urlsafe(32)

        await r.hset(key, mapping={
            'verified': '1',
            'verified_token': verified_token
        })

        await r.expire(key, 600)  # 10 分钟
        return verified_token

    async def _delete_captcha(self, token: str) -> None:
        """删除验证码"""
        r = await self.get_redis()
        key = self._get_redis_key(token)
        await r.delete(key)

    # ============== 公共接口 ==============

    async def generate(self) -> CaptchaResult:
        """
        生成新的图形验证码

        Returns:
            CaptchaResult 包含 token 和验证码图片 Base64
        """
        token = str(uuid.uuid4())
        code = self._generate_code()

        # 生成图片
        img = self._generate_captcha_image(code)
        image_base64 = self._image_to_base64(img)

        # 存储状态到 Redis
        state = CaptchaState(code=code)
        await self._store_captcha_state(token, state)

        logger.info("Captcha generated", extra={"token": token})

        return CaptchaResult(
            token=token,
            image_base64=image_base64
        )

    async def verify(self, token: str, submitted_code: str) -> tuple[bool, str | None, str]:
        """
        验证用户输入的验证码

        Args:
            token: 验证码 token
            submitted_code: 用户提交的验证码

        Returns:
            (是否验证成功, 验证令牌或None, 消息)
        """
        # 开发环境跳过验证
        if settings.SKIP_CAPTCHA:
            logger.warning("Captcha verification skipped (SKIP_CAPTCHA=True)")
            verified_token = secrets.token_urlsafe(32)
            return True, verified_token, "验证成功（开发模式）"

        # 获取验证码状态
        state = await self._get_captcha_state(token)

        if state is None:
            logger.warning("Captcha not found or expired", extra={"token": token})
            return False, None, "验证码已过期，请刷新"

        # 检查是否已验证
        if state.verified:
            logger.warning("Captcha already verified", extra={"token": token})
            return False, None, "验证码已使用"

        # 检查尝试次数
        if state.attempts >= settings.CAPTCHA_MAX_ATTEMPTS:
            await self._delete_captcha(token)
            logger.warning("Captcha max attempts exceeded", extra={"token": token})
            return False, None, "验证码尝试次数过多，请刷新"

        # 更新尝试次数
        state.attempts += 1
        await self._update_captcha_attempts(token, state.attempts)

        # 验证码比较（不区分大小写）
        if submitted_code.lower() == state.code.lower():
            verified_token = await self._mark_captcha_verified(token)
            logger.info("Captcha verified successfully", extra={"token": token})
            return True, verified_token, "验证成功"
        else:
            remaining = settings.CAPTCHA_MAX_ATTEMPTS - state.attempts
            logger.info(
                "Captcha verification failed",
                extra={"token": token, "remaining": remaining}
            )
            if remaining > 0:
                return False, None, f"验证码错误，还剩 {remaining} 次机会"
            else:
                await self._delete_captcha(token)
                return False, None, "验证码错误，请刷新"

    async def validate_verified_token(self, token: str, verified_token: str) -> bool:
        """
        验证登录请求中的验证令牌
        """
        if settings.SKIP_CAPTCHA:
            return True

        r = await self.get_redis()
        key = self._get_redis_key(token)

        data = await r.hgetall(key)
        if not data:
            return False

        if data.get('verified') != '1':
            return False

        stored_token = data.get('verified_token')
        if stored_token != verified_token:
            return False

        await self._delete_captcha(token)
        return True

    async def verify_code(self, token: str, code: str) -> bool:
        """
        简单验证验证码（用于注册等场景）

        Args:
            token: 验证码 token
            code: 用户输入的验证码

        Returns:
            验证是否成功
        """
        # 开发环境跳过验证
        if settings.SKIP_CAPTCHA:
            logger.warning("Captcha verification skipped (SKIP_CAPTCHA=True)")
            return True

        # 获取验证码状态
        state = await self._get_captcha_state(token)

        if state is None:
            logger.warning("Captcha not found or expired", extra={"token": token})
            return False

        # 检查是否已验证
        if state.verified:
            logger.warning("Captcha already verified", extra={"token": token})
            return False

        # 验证码比较（不区分大小写）
        if code.lower() == state.code.lower():
            await self._delete_captcha(token)
            logger.info("Captcha verified successfully", extra={"token": token})
            return True

        logger.info("Captcha verification failed", extra={"token": token})
        return False


# 全局服务实例
captcha_service = CaptchaService()
