"""
Twitter Service - 基于 Cookie 认证的 Twitter 数据服务

功能：
1. Cookie 认证连接
2. 获取用户信息
3. 获取用户推文列表
4. 搜索推文
5. 获取关注列表
"""

import asyncio
import time
from typing import Any
from urllib.parse import quote

import httpx
from playwright.async_api import async_playwright

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def quote_url(url: str) -> str:
    """URL 编码处理"""
    return quote(url, safe=':/?&=,')


def stamp_to_time(msecs_stamp: int) -> str:
    """时间戳转字符串"""
    time_array = time.localtime(msecs_stamp / 1000)
    return time.strftime("%Y-%m-%d %H:%M", time_array)


class TwitterService:
    """
    Twitter 服务类

    使用 Cookie 认证方式访问 Twitter GraphQL API
    """

    # Twitter 公共 Bearer Token (Web App 使用的)
    BEARER_TOKEN = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

    def __init__(self):
        self.auth_token: str | None = None
        self.ct0: str | None = None
        self._connected = False
        self._user_info: dict | None = None
        self.proxy: str | None = None

    def _get_headers(self, referer: str = "https://x.com") -> dict[str, str]:
        """构建请求头"""
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "authorization": self.BEARER_TOKEN,
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "zh-cn",
            "referer": referer,
        }

        if self.auth_token and self.ct0:
            headers["cookie"] = f"auth_token={self.auth_token}; ct0={self.ct0};"
            headers["x-csrf-token"] = self.ct0

        return headers

    async def connect(
        self,
        auth_token: str,
        ct0: str,
        proxy: str | None = None
    ) -> dict[str, Any]:
        """
        使用 Cookie 连接 Twitter

        Args:
            auth_token: Twitter auth_token cookie
            ct0: Twitter ct0 cookie (CSRF token)
            proxy: 代理地址 (可选)

        Returns:
            {"success": bool, "user_info": dict, "message": str}
        """
        self.auth_token = auth_token
        self.ct0 = ct0
        self.proxy = proxy

        try:
            # 尝试验证连接 - 获取当前用户信息
            user_info = await self._get_current_user()

            if user_info:
                self._user_info = user_info
                self._connected = True
                return {
                    "success": True,
                    "user_info": user_info,
                    "message": "连接成功",
                }
            else:
                # 即使验证失败，也标记为已连接，让用户可以尝试其他操作
                # 因为某些 API 可能在特定服务器上不可用
                self._connected = True
                self._user_info = {
                    "id": "",
                    "name": "未知用户",
                    "screen_name": "unknown",
                    "profile_image_url": None,
                    "followers_count": 0,
                    "friends_count": 0,
                    "statuses_count": 0,
                }
                return {
                    "success": True,
                    "user_info": self._user_info,
                    "message": "已保存 Cookie（验证 API 不可用，请尝试搜索用户验证）",
                }

        except Exception as e:
            logger.error(f"Twitter connect failed: {e}")
            return {"success": False, "message": str(e)}

    async def _get_current_user(self) -> dict | None:
        """获取当前登录用户信息 - 使用 settings API"""
        # 使用 Twitter settings API 获取当前用户信息
        url = "https://api.twitter.com/1.1/account/settings.json"

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=30
                )

                logger.info(f"Settings API response: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    screen_name = data.get("screen_name")

                    if screen_name:
                        # 获取完整用户信息
                        user_result = await self.get_user_by_screen_name(screen_name)
                        if user_result.get("success") and user_result.get("user"):
                            return user_result["user"]

                    # 如果无法获取完整信息，返回基本信息
                    return {
                        "id": "",
                        "name": screen_name,
                        "screen_name": screen_name,
                        "profile_image_url": None,
                        "followers_count": 0,
                        "friends_count": 0,
                        "statuses_count": 0,
                    }
                else:
                    logger.error(f"Get current user failed: {response.status_code} - {response.text[:500]}")
                    return None

        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return None

    async def get_user_by_screen_name(self, screen_name: str) -> dict[str, Any]:
        """
        通过用户名获取用户信息

        Args:
            screen_name: Twitter 用户名 (不带@)

        Returns:
            {"success": bool, "user": dict, "message": str}
        """
        if not self._connected:
            return {"success": False, "message": "未连接"}

        screen_name = screen_name.lstrip("@").strip()

        url = f'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={{"screen_name":"{screen_name}","withSafetyModeUserFields":false}}&features={{"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}}&fieldToggles={{"withAuxiliaryUserLabels":false}}'

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                response = await client.get(
                    quote_url(url),
                    headers=self._get_headers(f"https://x.com/{screen_name}"),
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {}).get("user", {}).get("result", {})

                    if not result:
                        return {"success": False, "message": "用户不存在"}

                    legacy = result.get("legacy", {})

                    return {
                        "success": True,
                        "user": {
                            "id": result.get("rest_id"),
                            "name": legacy.get("name"),
                            "screen_name": legacy.get("screen_name"),
                            "description": legacy.get("description"),
                            "profile_image_url": legacy.get("profile_image_url_https"),
                            "followers_count": legacy.get("followers_count"),
                            "friends_count": legacy.get("friends_count"),
                            "statuses_count": legacy.get("statuses_count"),
                            "media_count": legacy.get("media_count"),
                            "created_at": legacy.get("created_at"),
                            "verified": legacy.get("verified", False),
                        },
                        "message": "获取成功",
                    }
                elif "Rate limit" in response.text:
                    return {"success": False, "message": "API 请求次数超限，请稍后再试"}
                else:
                    return {"success": False, "message": f"获取失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"Get user by screen name failed: {e}")
            return {"success": False, "message": str(e)}

    async def get_user_tweets(
        self,
        user_id: str,
        count: int = 20,
        cursor: str | None = None,
        include_retweets: bool = False
    ) -> dict[str, Any]:
        """
        获取用户推文列表

        Args:
            user_id: 用户 ID (rest_id)
            count: 获取数量
            cursor: 分页游标
            include_retweets: 是否包含转推

        Returns:
            {"success": bool, "tweets": list, "next_cursor": str, "message": str}
        """
        if not self._connected:
            return {"success": False, "message": "未连接", "tweets": []}

        if include_retweets:
            # UserTweets API - 包含转推
            url_base = f'https://twitter.com/i/api/graphql/2GIWTr7XwadIixZDtyXd4A/UserTweets?variables={{"userId":"{user_id}","count":{count},'
            url_features = '"includePromotedContent":false,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}&features={"rweb_lists_timeline_redesign_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}&fieldToggles={"withAuxiliaryUserLabels":false,"withArticleRichContentState":false}'
        else:
            # UserMedia API - 仅媒体推文
            url_base = f'https://twitter.com/i/api/graphql/Le6KlbilFmSu-5VltFND-Q/UserMedia?variables={{"userId":"{user_id}","count":{count},'
            url_features = '"includePromotedContent":false,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}&features={"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'

        if cursor:
            url = url_base + f'"cursor":"{cursor}",' + url_features
        else:
            url = url_base + url_features

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                response = await client.get(
                    quote_url(url),
                    headers=self._get_headers(),
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    tweets = []
                    next_cursor = None

                    # 解析推文数据
                    instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])

                    for instruction in instructions:
                        entries = instruction.get("entries", [])
                        for entry in entries:
                            # 获取下一页游标
                            if "cursor-bottom" in entry.get("entryId", ""):
                                next_cursor = entry.get("content", {}).get("value")
                                continue

                            # 解析推文
                            tweet = self._parse_tweet_entry(entry, include_retweets)
                            if tweet:
                                tweets.append(tweet)

                    return {
                        "success": True,
                        "tweets": tweets,
                        "next_cursor": next_cursor,
                        "message": f"获取到 {len(tweets)} 条推文",
                    }

                elif "Rate limit" in response.text:
                    return {"success": False, "message": "API 请求次数超限", "tweets": []}
                else:
                    return {"success": False, "message": f"获取失败: {response.status_code}", "tweets": []}

        except Exception as e:
            logger.error(f"Get user tweets failed: {e}")
            return {"success": False, "message": str(e), "tweets": []}

    def _parse_tweet_entry(self, entry: dict, include_retweets: bool = False) -> dict | None:
        """解析推文条目"""
        try:
            entry_id = entry.get("entryId", "")

            if "promoted-tweet" in entry_id:
                return None  # 跳过广告

            if "tweet" not in entry_id:
                return None

            # 获取推文数据
            content = entry.get("content", {})
            item_content = content.get("itemContent", {})
            tweet_results = item_content.get("tweet_results", {}).get("result", {})

            # 处理嵌套的 tweet 对象
            if "tweet" in tweet_results:
                tweet_results = tweet_results["tweet"]

            legacy = tweet_results.get("legacy", {})

            if not legacy:
                return None

            # 检查是否为转推
            is_retweet = "retweeted_status_result" in legacy
            if is_retweet and not include_retweets:
                return None

            # 获取用户信息
            user_results = tweet_results.get("core", {}).get("user_results", {}).get("result", {})
            user_legacy = user_results.get("legacy", {})

            # 解析时间
            try:
                edit_control = tweet_results.get("edit_control", {})
                tweet_msecs = int(edit_control.get("editable_until_msecs", 0)) - 3600000
                tweet_time = stamp_to_time(tweet_msecs) if tweet_msecs > 0 else None
            except (ValueError, TypeError, KeyError):
                tweet_time = None

            # 解析媒体
            media = []
            extended_entities = legacy.get("extended_entities", {})
            for m in extended_entities.get("media", []):
                media_item = {
                    "type": m.get("type"),
                    "url": m.get("media_url_https"),
                    "expanded_url": m.get("expanded_url"),
                }
                # 视频获取最高质量
                if "video_info" in m:
                    variants = m["video_info"].get("variants", [])
                    best_video = max(
                        [v for v in variants if v.get("bitrate")],
                        key=lambda x: x.get("bitrate", 0),
                        default=None
                    )
                    if best_video:
                        media_item["video_url"] = best_video.get("url")
                media.append(media_item)

            return {
                "id": legacy.get("id_str"),
                "conversation_id": legacy.get("conversation_id_str"),
                "text": legacy.get("full_text"),
                "created_at": tweet_time,
                "user": {
                    "id": user_results.get("rest_id"),
                    "name": user_legacy.get("name"),
                    "screen_name": user_legacy.get("screen_name"),
                    "profile_image_url": user_legacy.get("profile_image_url_https"),
                },
                "favorite_count": legacy.get("favorite_count", 0),
                "retweet_count": legacy.get("retweet_count", 0),
                "reply_count": legacy.get("reply_count", 0),
                "views_count": tweet_results.get("views", {}).get("count"),
                "media": media,
                "is_retweet": is_retweet,
                "urls": [u.get("expanded_url") for u in legacy.get("entities", {}).get("urls", [])],
            }

        except Exception as e:
            logger.warning(f"Parse tweet entry failed: {e}")
            return None

    async def search_tweets(
        self,
        query: str,
        count: int = 20,
        cursor: str | None = None
    ) -> dict[str, Any]:
        """
        搜索推文

        Args:
            query: 搜索关键词
            count: 获取数量
            cursor: 分页游标

        Returns:
            {"success": bool, "tweets": list, "next_cursor": str, "message": str}
        """
        if not self._connected:
            return {"success": False, "message": "未连接", "tweets": []}

        # 构建搜索 URL
        encoded_query = quote(query)
        url_base = f'https://twitter.com/i/api/graphql/gkjsKepM6gl_HmFWoWKfgg/SearchTimeline?variables={{"rawQuery":"{encoded_query}","count":{count},"querySource":"typed_query","product":"Latest",'

        url_features = '"includePromotedContent":true,"withCommunity":true}&features={"rweb_lists_timeline_redesign_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'

        if cursor:
            url = url_base + f'"cursor":"{cursor}",' + url_features
        else:
            url = url_base + url_features

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                response = await client.get(
                    quote_url(url),
                    headers=self._get_headers("https://x.com/search"),
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    tweets = []
                    next_cursor = None

                    # 解析搜索结果
                    timeline = data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {})
                    instructions = timeline.get("instructions", [])

                    for instruction in instructions:
                        entries = instruction.get("entries", [])
                        for entry in entries:
                            if "cursor-bottom" in entry.get("entryId", ""):
                                next_cursor = entry.get("content", {}).get("value")
                                continue

                            tweet = self._parse_tweet_entry(entry, include_retweets=True)
                            if tweet:
                                tweets.append(tweet)

                    return {
                        "success": True,
                        "tweets": tweets,
                        "next_cursor": next_cursor,
                        "message": f"搜索到 {len(tweets)} 条推文",
                    }

                elif "Rate limit" in response.text:
                    return {"success": False, "message": "API 请求次数超限", "tweets": []}
                else:
                    # API 失败，尝试使用 Playwright
                    logger.info(f"API search failed ({response.status_code}), trying Playwright...")
                    return await self.search_tweets_playwright(query, count)

        except Exception as e:
            logger.error(f"Search tweets failed: {e}")
            # API 异常，尝试使用 Playwright
            logger.info("API search exception, trying Playwright...")
            return await self.search_tweets_playwright(query, count)

    async def search_tweets_playwright(
        self,
        query: str,
        count: int = 20
    ) -> dict[str, Any]:
        """
        使用 Playwright 搜索推文

        Args:
            query: 搜索关键词
            count: 获取数量

        Returns:
            {"success": bool, "tweets": list, "message": str}
        """
        if not self._connected or not self.auth_token or not self.ct0:
            return {"success": False, "message": "未连接", "tweets": []}

        tweets = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )

                # 设置 cookies - 需要同时设置 x.com 和 twitter.com
                cookies = [
                    {
                        "name": "auth_token",
                        "value": self.auth_token,
                        "domain": ".x.com",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True,
                    },
                    {
                        "name": "ct0",
                        "value": self.ct0,
                        "domain": ".x.com",
                        "path": "/",
                        "secure": True,
                    },
                    {
                        "name": "auth_token",
                        "value": self.auth_token,
                        "domain": ".twitter.com",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True,
                    },
                    {
                        "name": "ct0",
                        "value": self.ct0,
                        "domain": ".twitter.com",
                        "path": "/",
                        "secure": True,
                    },
                ]
                await context.add_cookies(cookies)

                page = await context.new_page()

                # 设置额外的请求头
                await page.set_extra_http_headers({
                    "x-csrf-token": self.ct0,
                    "authorization": self.BEARER_TOKEN,
                })

                # 监听 API 响应
                api_responses = []

                async def handle_response(response: Any) -> None:
                    url = response.url
                    if "SearchTimeline" in url or "adaptive.json" in url or "search" in url:
                        try:
                            if response.status == 200:
                                data = await response.json()
                                api_responses.append(data)
                                logger.info(f"Captured API response from: {url[:100]}")
                        except Exception as e:
                            logger.warning(f"Failed to parse response: {e}")

                page.on("response", handle_response)

                # 访问搜索页面
                search_url = f"https://x.com/search?q={quote(query)}&src=typed_query&f=live"
                logger.info(f"Playwright navigating to: {search_url}")

                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                except Exception as e:
                    logger.warning(f"Navigation timeout/error: {e}")

                # 等待推文加载
                await asyncio.sleep(5)

                # 滚动页面以触发更多加载
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(2)

                logger.info(f"Captured {len(api_responses)} API responses")

                # 尝试从 API 响应中解析推文
                for data in api_responses:
                    try:
                        # 解析 SearchTimeline 响应
                        timeline = data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {})
                        instructions = timeline.get("instructions", [])

                        for instruction in instructions:
                            entries = instruction.get("entries", [])
                            for entry in entries:
                                tweet = self._parse_tweet_entry(entry, include_retweets=True)
                                if tweet and len(tweets) < count:
                                    # 避免重复
                                    if not any(t["id"] == tweet["id"] for t in tweets):
                                        tweets.append(tweet)
                    except Exception as e:
                        logger.warning(f"Parse API response failed: {e}")

                # 如果 API 响应解析失败，尝试从页面 DOM 提取
                if not tweets:
                    logger.info("Trying to extract tweets from DOM...")

                    # 等待推文元素出现
                    try:
                        await page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                    except Exception:
                        logger.warning("No tweet elements found on page")
                        # 截图调试
                        try:
                            screenshot = await page.screenshot()
                            logger.info(f"Page screenshot taken, size: {len(screenshot)} bytes")
                        except Exception:
                            pass

                    tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
                    logger.info(f"Found {len(tweet_elements)} tweet elements in DOM")

                    # 保存截图和页面内容用于调试
                    if not tweet_elements:
                        try:
                            # 获取页面标题和 URL
                            title = await page.title()
                            current_url = page.url
                            logger.info(f"Page title: {title}, URL: {current_url}")

                            # 检查是否被重定向到登录页
                            if "login" in current_url.lower() or "flow" in current_url.lower():
                                logger.warning("Redirected to login page - cookies may be invalid")
                        except Exception as e:
                            logger.warning(f"Failed to get page info: {e}")

                    for element in tweet_elements[:count]:
                        try:
                            # 提取推文文本
                            text_el = await element.query_selector('[data-testid="tweetText"]')
                            text = await text_el.inner_text() if text_el else ""

                            # 提取用户名
                            user_links = await element.query_selector_all('a[href^="/"]')
                            screen_name = ""
                            for link in user_links:
                                href = await link.get_attribute("href")
                                if href and href.count("/") == 1 and not href.startswith("/#"):
                                    screen_name = href.strip("/")
                                    break

                            # 提取显示名
                            name = screen_name

                            # 提取时间
                            time_el = await element.query_selector("time")
                            created_at = ""
                            if time_el:
                                datetime_attr = await time_el.get_attribute("datetime")
                                if datetime_attr:
                                    created_at = datetime_attr[:16].replace("T", " ")

                            if text:
                                tweets.append({
                                    "id": str(hash(text + screen_name))[-10:],
                                    "conversation_id": None,
                                    "text": text,
                                    "created_at": created_at,
                                    "user": {
                                        "id": None,
                                        "name": name,
                                        "screen_name": screen_name,
                                        "profile_image_url": None,
                                    },
                                    "favorite_count": 0,
                                    "retweet_count": 0,
                                    "reply_count": 0,
                                    "views_count": None,
                                    "media": [],
                                    "is_retweet": text.startswith("RT @"),
                                    "urls": [],
                                })
                        except Exception as e:
                            logger.warning(f"Extract tweet from DOM failed: {e}")

                await browser.close()

                if tweets:
                    return {
                        "success": True,
                        "tweets": tweets,
                        "next_cursor": None,
                        "message": f"搜索到 {len(tweets)} 条推文 (Playwright)",
                    }
                else:
                    return {
                        "success": False,
                        "tweets": [],
                        "message": "未找到推文，可能需要登录或 Cookie 已过期",
                    }

        except Exception as e:
            logger.error(f"Playwright search failed: {e}")
            return {"success": False, "message": f"Playwright 搜索失败: {str(e)}", "tweets": []}

    def _parse_count(self, text: str) -> int:
        """解析数量文本 (如 1.2K, 3.5M)"""
        if not text:
            return 0
        text = text.strip().upper()
        try:
            if "K" in text:
                return int(float(text.replace("K", "")) * 1000)
            elif "M" in text:
                return int(float(text.replace("M", "")) * 1000000)
            else:
                return int(text)
        except (ValueError, TypeError):
            return 0

    async def disconnect(self) -> None:
        """断开连接"""
        self.auth_token = None
        self.ct0 = None
        self._connected = False
        self._user_info = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @property
    def user_info(self) -> dict | None:
        """当前用户信息"""
        return self._user_info


# 全局服务实例
_twitter_service: TwitterService | None = None


def get_twitter_service() -> TwitterService:
    """获取 Twitter 服务实例"""
    global _twitter_service
    if _twitter_service is None:
        _twitter_service = TwitterService()
        _twitter_service.proxy = settings.HTTP_PROXY
    return _twitter_service
