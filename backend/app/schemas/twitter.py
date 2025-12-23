"""
Twitter Pydantic Schema
Twitter 数据请求/响应模型

提供 Twitter Cookie 认证、用户信息和推文获取的数据模型。
"""


from pydantic import BaseModel, Field

# =============================================================
# 认证相关模型
# =============================================================

class TwitterConnectRequest(BaseModel):
    """Twitter Cookie 连接请求"""
    auth_token: str = Field(..., description="Twitter auth_token cookie")
    ct0: str = Field(..., description="Twitter ct0 cookie (CSRF token)")
    proxy: str | None = Field(None, description="代理地址 (可选)")


class TwitterUserInfo(BaseModel):
    """Twitter 用户信息"""
    id: str = Field(..., description="用户 ID")
    name: str | None = Field(None, description="显示名称")
    screen_name: str | None = Field(None, description="用户名")
    description: str | None = Field(None, description="个人简介")
    profile_image_url: str | None = Field(None, description="头像 URL")
    followers_count: int | None = Field(None, description="粉丝数")
    friends_count: int | None = Field(None, description="关注数")
    statuses_count: int | None = Field(None, description="推文数")
    media_count: int | None = Field(None, description="媒体推文数")
    created_at: str | None = Field(None, description="创建时间")
    verified: bool = Field(False, description="是否认证")


# =============================================================
# 推文相关模型
# =============================================================

class TwitterMediaItem(BaseModel):
    """推文媒体项"""
    type: str | None = Field(None, description="媒体类型: photo/video/animated_gif")
    url: str | None = Field(None, description="媒体 URL")
    expanded_url: str | None = Field(None, description="展开 URL")
    video_url: str | None = Field(None, description="视频 URL (仅视频)")


class TwitterTweetUser(BaseModel):
    """推文作者信息"""
    id: str | None = Field(None, description="用户 ID")
    name: str | None = Field(None, description="显示名称")
    screen_name: str | None = Field(None, description="用户名")
    profile_image_url: str | None = Field(None, description="头像 URL")


class TwitterTweet(BaseModel):
    """推文模型"""
    id: str = Field(..., description="推文 ID")
    conversation_id: str | None = Field(None, description="对话 ID")
    text: str | None = Field(None, description="推文内容")
    created_at: str | None = Field(None, description="发布时间")
    user: TwitterTweetUser | None = Field(None, description="作者信息")
    favorite_count: int = Field(0, description="喜欢数")
    retweet_count: int = Field(0, description="转推数")
    reply_count: int = Field(0, description="回复数")
    views_count: str | None = Field(None, description="浏览数")
    media: list[TwitterMediaItem] = Field(default_factory=list, description="媒体列表")
    is_retweet: bool = Field(False, description="是否为转推")
    urls: list[str] = Field(default_factory=list, description="链接列表")


# =============================================================
# 请求模型
# =============================================================

class TwitterGetUserRequest(BaseModel):
    """获取用户信息请求"""
    screen_name: str = Field(..., description="用户名 (不带@)")


class TwitterGetTweetsRequest(BaseModel):
    """获取推文列表请求"""
    user_id: str = Field(..., description="用户 ID")
    count: int = Field(20, ge=1, le=100, description="获取数量")
    cursor: str | None = Field(None, description="分页游标")
    include_retweets: bool = Field(False, description="是否包含转推")


class TwitterSearchRequest(BaseModel):
    """搜索推文请求"""
    query: str = Field(..., description="搜索关键词")
    count: int = Field(20, ge=1, le=100, description="获取数量")
    cursor: str | None = Field(None, description="分页游标")


# =============================================================
# 响应模型
# =============================================================

class TwitterBaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")


class TwitterConnectResponse(TwitterBaseResponse):
    """连接响应"""
    user_info: TwitterUserInfo | None = Field(None, description="当前用户信息")


class TwitterStatusResponse(BaseModel):
    """状态响应"""
    connected: bool = Field(..., description="是否已连接")
    user_info: TwitterUserInfo | None = Field(None, description="当前用户信息")


class TwitterUserResponse(TwitterBaseResponse):
    """用户信息响应"""
    user: TwitterUserInfo | None = Field(None, description="用户信息")


class TwitterTweetsResponse(TwitterBaseResponse):
    """推文列表响应"""
    tweets: list[TwitterTweet] = Field(default_factory=list, description="推文列表")
    next_cursor: str | None = Field(None, description="下一页游标")
    total: int = Field(0, description="返回数量")
