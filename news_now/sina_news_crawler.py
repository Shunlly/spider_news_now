import time

from anti_useragent import UserAgent
from playwright.sync_api import sync_playwright, Route

from src.common.log import log


class SinaNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        }
        self.ent_url = "https://ent.sina.com.cn/"
        self.china_url = "https://news.sina.com.cn/china/"
        self.world_url = "https://news.sina.com.cn/world/"


    def get_ent_channel_news(self):
        news_data = []
        try:
            def scroll_to_bottom(page):
                """快速滚到底，等 1 s 让 JS 补数据"""
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(10)  # 视网速可调

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # 关键：请求拦截
                # page.route("**/*", block_useless)
                page.goto(self.ent_url, wait_until='domcontentloaded', timeout=120000)

                scroll_to_bottom(page)

                # 1. 每条卡片
                cards = page.locator('div.cardlist-a__list > div.ty-card')

                # 2. 取第二个 div.ty-card-r 里 h3 > a
                for i in range(cards.count()):
                    a = cards.nth(i).locator('div:nth-child(2) > h3 > a').first
                    href = a.get_attribute('href')
                    text = a.inner_text().strip()
                    news_data.append({
                        "url": href.strip(),
                        'title': text.strip(),
                        "type": "ent",
                        "source": "sina"
                    })

                browser.close()
            return news_data
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"爬取sina news的ent报错，报错信息：{str(e)}")
            return news_data

    def get_china_channel_news(self, page_num: int = 3):
        news_data = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置默认超时为 120 秒
                page.set_default_timeout(120000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                page.goto(self.china_url, wait_until='domcontentloaded', timeout=240000)

                # 等待新闻列表容器加载完成
                try:
                    page.wait_for_selector('div.feed-card-content > div:first-child > div.feed-card-item', timeout=60000)
                except Exception as e:
                    # 等待新闻列表超时，保留Exception以容错处理
                    log.warning(f"等待新闻列表超时: {str(e)}")
                    browser.close()
                    return news_data

                # 等待翻页按钮出现
                try:
                    page.wait_for_selector('.pagebox_next', timeout=60000)
                except Exception as e:
                    # 等待翻页按钮超时，保留Exception以容错处理
                    log.warning(f"等待翻页按钮超时: {str(e)}")

                # 额外等待确保动态内容加载
                time.sleep(3)

                # 循环3轮：初始页 + 点击翻页page_num -1 次
                for round_num in range(page_num):
                    log.info(f"正在抓取新浪国内新闻第 {round_num + 1} 页")

                    # 1. 先定位 feed-card-content 下第一个 div
                    # 2. 里面每条 feed-card-item
                    items = page.locator('div.feed-card-content > div:first-child > div.feed-card-item')

                    for i in range(items.count()):
                        try:
                            a = items.nth(i).locator('h2 > a').first
                            href = a.get_attribute('href')
                            text = a.inner_text().strip()
                            if href and text:
                                news_data.append({
                                    'url': href.strip(),
                                    'title': text.strip(),
                                    "type": "china_events",
                                    "source": "sina"
                                })
                        except Exception as e:
                            # 提取单条新闻失败，保留Exception以不中断批量处理
                            log.warning(f"提取第 {i+1} 条新闻失败: {str(e)}")
                            continue

                    log.info(f"第 {round_num + 1} 页抓取到 {items.count()} 条新闻")

                    # 如果不是最后一轮，点击下一页按钮
                    if round_num < page_num - 1:
                        try:
                            # 精确定位"下一页"按钮（不包含"next5"类的那个）
                            next_button = page.locator('.pagebox_next').filter(has_text='下一页')
                            if next_button.count() > 0:
                                next_button.click()
                                # 等待页面加载新内容，使用 domcontentloaded 代替 networkidle
                                time.sleep(2)
                                page.wait_for_load_state('domcontentloaded', timeout=60000)
                                # 额外等待，让 JS 渲染新内容
                                time.sleep(2)
                            else:
                                log.warning(f"第{round_num + 1}轮未找到下一页按钮，停止翻页")
                                break
                        except Exception as e:
                            # 翻页操作失败，保留Exception以容错处理
                            log.warning(f"第{round_num + 1}轮点击下一页失败：{str(e)}")
                            break

                browser.close()
            log.info(f"新浪国内新闻共抓取 {len(news_data)} 条")
            return news_data
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"爬取sina news的china报错，报错信息：{str(e)}")
            return news_data

    def get_world_channel_news(self):
        news_data = []
        # 1. 最外层容器
        SELECTOR_BOX = 'div#subShowContent1_static'
        # 2. 4 个 news 块
        NEWS_IDS = ['subShowContent1_news1',
                    'subShowContent1_news2',
                    'subShowContent1_news3',
                    'subShowContent1_news4']
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # 调试完可改 True
                page = browser.new_page()
                page.goto(self.world_url, wait_until='domcontentloaded', timeout=120000)

                # 等容器出现
                page.wait_for_selector(SELECTOR_BOX, timeout=60000)

                for news_id in NEWS_IDS:
                    # 逐块定位
                    block = page.query_selector(f'div#{news_id}')
                    if not block:  # 万一某块没渲染出来
                        continue
                    items = block.query_selector_all('div.news-item')
                    for it in items:
                        a = it.query_selector('h2 a')
                        if not a:
                            continue
                        news_data.append({
                            'url': a.get_attribute('href').strip(),
                            'title': a.inner_text().strip(),
                            "type": "world_events",
                            "source": "sina"
                        })

                browser.close()
            return news_data
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"爬取sina news的world报错，报错信息：{str(e)}")
            return news_data

    def main(self):
        log.info("开始爬取sina news")
        ent_news, china_news, world_news = [], [], []
        ent_news = self.get_ent_channel_news()
        china_news = self.get_china_channel_news()
        world_news = self.get_world_channel_news()
        # 反转列表，让最新的排在最后
        ent_news.reverse()
        china_news.reverse()
        world_news.reverse()
        log.info(f"爬取sina news完成,{len(ent_news)} 条ent新闻, {len(china_news)} 条china新闻, {len(world_news)} 条world新闻"
                 f"ent最新的一条新闻为【{ent_news[-1]['title']}: {ent_news[-1]['url']}】"
                 f"china最新的一条新闻为【{china_news[-1]['title']}: {china_news[-1]['url']}】"
                 f"world最新的一条新闻为【{world_news[-1]['title']}: {world_news[-1]['url']}】")
        return ent_news + china_news + world_news


if __name__ == '__main__':
    crawler = SinaNewsCrawler()
    a = crawler.main()
    print(a)