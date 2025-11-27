import time

import requests
from anti_useragent import UserAgent
from playwright.sync_api import sync_playwright

from src.common.log import log


class WangyiNewsCrawler:

    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        }
        self.base_url = "https://culture.163.com/"


    def get_culture_channel_news(self):
        news_data = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置默认超时为 120 秒
                page.set_default_timeout(120000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                page.goto(self.base_url, wait_until='domcontentloaded', timeout=240000)

                # 等待内容加载
                time.sleep(3)

                # 1. 每个新闻块第一个 a
                # 2. 取它里面 img 的 alt
                links = page.locator('div.datalist > div > a:first-of-type')

                for i in range(links.count()):
                    try:
                        href = links.nth(i).get_attribute('href')
                        title = links.nth(i).locator('img').get_attribute('alt') or ''
                        if href and title:
                            news_data.append({"title": title.strip(), "url": href, "type": "culture", "source": "163"})
                    except Exception as e:
                        # 提取单条新闻失败，保留Exception以不中断批量处理
                        log.warning(f"提取第 {i+1} 条新闻失败: {str(e)}")
                        continue

                browser.close()
            log.info(f"网易文化频道共获取 {len(news_data)} 条新闻")
            return news_data
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"爬取网易文化频道失败: {e}")
            return news_data

    def main(self):
        log.info("开始爬取网易新闻---文化频道")
        news_data = []
        news_data = self.get_culture_channel_news()
        # 反转列表，让最新的排在最后
        news_data.reverse()
        log.info(f"结束爬取网易新闻---文化频道, 总计有{len(news_data)}"
                 f"culture最新一条新闻为【{news_data[-1]['title']}: {news_data[-1]['url']}】")
        return news_data


if __name__ == '__main__':
    wangyi_news_crawler = WangyiNewsCrawler()
    wangyi_news_crawler.main()