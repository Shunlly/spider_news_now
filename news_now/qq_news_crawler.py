from typing import Union, Dict, List
import requests
import time
import random

from anti_useragent import UserAgent
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.common.log import log


class QQNewsCrawler:
    """
    腾讯新闻爬虫 - 模拟数据版本
    由于腾讯新闻有反爬虫机制，这里提供一个模拟实现
    """

    def __init__(self):
        self.channels = ['体育', '科技']
        self.sports_url = 'https://news.qq.com/ch/sports'
        self.tech_url = 'https://news.qq.com/ch/tech'
        self.headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def commmon_func(url, url_type):
        news_data = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置页面默认超时为 240 秒（4 分钟）
                page.set_default_timeout(240000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                # networkidle 等待所有网络请求完成，容易超时
                page.goto(url, wait_until="domcontentloaded", timeout=120000)

                # 等待关键元素出现，超时 60 秒
                page.wait_for_selector(".channel-feed-list", state="attached", timeout=60000)

                # 3. 页面多次向下滚动，让 JS 加载更多数据
                scroll_times = 5  # 滚动次数
                for i in range(scroll_times):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.5)  # 每次滚动后等待数据加载

                # 滚动完成后再等待一下，确保最后一批数据加载完成
                time.sleep(2)

                # 4. 取所有 feed 条目
                items = page.locator(".channel-feed-list > .channel-feed-item").all()

                for idx, row in enumerate(items, 1):
                    # 方法 A：直接 CSS 拿“第 2 个 a”
                    a = row.locator("a.article-title")
                    href = a.get_attribute("href")
                    # 关键：再往下拿 span
                    text = a.locator("span").nth(0).inner_text()
                    if href:
                        news_data.append({
                            "title": text,
                            "url": href,
                            "type": url_type,
                            "source": "qq_news",
                        })
                browser.close()
            log.info(f"共抓到 {len(news_data)} 条")
            return news_data
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"爬取qq news的{url_type}失败，{str(e)}")
            return news_data

    def get_sports_channel_news(self):
        sports_news = self.commmon_func(self.sports_url, "sports")
        return sports_news


    def get_tech_channel_news(self):
        tech_news = self.commmon_func(self.tech_url, "tech")
        return tech_news


    def main(self):
        log.info("开始爬取腾讯新闻")
        sports_news, tech_news = [], []
        sports_news = self.commmon_func(self.sports_url, "sports")
        tech_news = self.commmon_func(self.tech_url, "tech")
        # 反转列表，让最新的排在最后
        sports_news.reverse()
        tech_news.reverse()
        log.info(f"爬取腾讯新闻完成，sports频道{len(sports_news)}条，tech频道{len(tech_news)}条。"
                 f"sports最新的一条新闻为【 {sports_news[-1]['title']} 】【 {sports_news[-1]['url']}】"
                 f"tech最新的一条新闻为【 {tech_news[-1]['title']} 】【 {tech_news[-1]['url']}】")
        return  sports_news + tech_news



if __name__ == '__main__':
    crawler = QQNewsCrawler()
    a = crawler.main()
    print(a)

