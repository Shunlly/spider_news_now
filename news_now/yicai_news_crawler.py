import time
import re
from datetime import datetime, timedelta

from anti_useragent import UserAgent
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.common.log import log


class YiCaiNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
        }
        self.base_url = "https://www.yicai.com/news/"

    def parse_publish_time(self, time_str: str) -> str:
        """
        解析发布时间字符串，转换为标准时间格式
        支持格式:
        - "MM-DD HH:MM" (如 "10-11 21:25" 或 "06-20 11:14")
        - "昨天 HH:MM" (如 "昨天 23:12")
        - "X分钟前"
        - "X小时前"
        - "X天前"

        返回: "YYYY-MM-DD HH:MM:SS" 格式的时间字符串
        """
        try:
            now = datetime.now()
            time_str = time_str.strip()

            # 格式1: "MM-DD HH:MM" (如 "10-11 21:25")
            match = re.match(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', time_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4))

                # 使用当前年份
                year = now.year
                parsed_time = datetime(year, month, day, hour, minute)

                # 如果解析出的时间大于当前时间，说明是去年的
                if parsed_time > now:
                    parsed_time = datetime(year - 1, month, day, hour, minute)

                return parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            # 格式2: "昨天 HH:MM" (如 "昨天 23:12")
            match = re.match(r'昨天\s+(\d{2}):(\d{2})', time_str)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                # 计算昨天的日期
                yesterday = now - timedelta(days=1)
                parsed_time = datetime(yesterday.year, yesterday.month, yesterday.day, hour, minute)
                return parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            # 格式3: "X分钟前"
            match = re.match(r'(\d+)分钟前', time_str)
            if match:
                minutes = int(match.group(1))
                parsed_time = now - timedelta(minutes=minutes)
                return parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            # 格式4: "X小时前"
            match = re.match(r'(\d+)小时前', time_str)
            if match:
                hours = int(match.group(1))
                parsed_time = now - timedelta(hours=hours)
                return parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            # 格式5: "X天前"
            match = re.match(r'(\d+)天前', time_str)
            if match:
                days = int(match.group(1))
                parsed_time = now - timedelta(days=days)
                return parsed_time.strftime('%Y-%m-%d %H:%M:%S')

            # 如果无法解析，返回当前时间
            log.warning(f'无法解析时间格式: {time_str}，使用当前时间')
            return now.strftime('%Y-%m-%d %H:%M:%S')

        except Exception as e:
            # 时间解析失败，保留Exception以容错处理
            log.error(f'解析时间失败: {time_str}, 错误: {e}')
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_finance_channel_news(self, click_times: int = 2):
        news_list = []
        try:
            html = None
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置默认超时为 120 秒
                page.set_default_timeout(120000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=240000)

                # 等待第一页的新闻列表项加载出来
                page.wait_for_selector('div#newslist a', timeout=30000)
                time.sleep(2)  # 额外等待确保数据完全加载

                # 点击"加载更多"按钮，触发指定次数
                for i in range(click_times):
                    try:
                        # 等待"加载更多"按钮出现
                        more_button = page.locator('button.btnmore')
                        if more_button.count() > 0:
                            more_button.click()
                            time.sleep(2)  # 等待新数据加载
                            log.info(f'第一财经，财经频道第 {i + 1} 次点击"加载更多"按钮成功')
                        else:
                            log.warning(f'第一财经，财经频道第 {i + 1} 次未找到"加载更多"按钮，跳出循环')
                            break
                    except Exception as e:
                        # 点击加载更多失败，保留Exception以不中断爬取
                        log.warning(f'第一财经，财经频道第 {i + 1} 次点击"加载更多"按钮失败: {e}，跳出循环')
                        break

                # 获取最终的 HTML
                html = page.content()
                browser.close()

            if not html:
                log.error('第一财经，财经频道获取html失败')
                return news_list

            soup = BeautifulSoup(html, 'lxml')
            # 1. 找到目标 div#newslist
            newslist_div = soup.find('div', id='newslist')
            if not newslist_div:
                log.error('未找到指定 div#newslist')
                return news_list

            # 2. 遍历所有 a 标签，提取 href 和 h2 标签中的文本
            for a in newslist_div.find_all('a', class_='f-db'):
                href = a.get('href')
                h2 = a.find('h2')

                # 过滤掉 topic 开头的链接（如专题、研报精选等）
                if href and href.startswith('/topic/'):
                    continue

                # 只有当 href 和 h2 都存在且 h2 有文本时才添加
                if href and h2 and h2.get_text(strip=True):
                    title = h2.get_text(strip=True)
                    # 补全相对路径
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.yicai.com' + href

                    # 提取发布时间
                    publish_time = None
                    try:
                        # 查找 div.author > div.rightspan > span (第二个span)
                        author_div = a.find('div', class_='author')
                        if author_div:
                            rightspan_div = author_div.find('div', class_='rightspan')
                            if rightspan_div:
                                # 获取所有 span 标签，第二个是时间
                                spans = rightspan_div.find_all('span')
                                if len(spans) >= 2:
                                    time_str = spans[1].get_text(strip=True)
                                    publish_time = self.parse_publish_time(time_str)
                    except Exception as e:
                        # 提取发布时间失败，保留Exception以容错处理
                        log.warning(f'提取发布时间失败: {e}，链接: {href}')

                    news_list.append({
                        'url': href,
                        'title': title,
                        'type': 'finance',
                        'source': 'yicai',
                        'publish_time': publish_time
                    })

            log.info(f'第一财经，财经频道共获取 {len(news_list)} 条新闻')
            return news_list
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"获取第一财经，财经频道新闻失败: {e}")
            return news_list


    def main(self):
        log.info('开始爬取第一财经网新闻')
        finance_data = []
        # 财经频道数据
        finance_data = self.get_finance_channel_news()
        # 反转列表，让最新的排在最后
        finance_data.reverse()
        log.info(f'第一财经网新闻爬取完成，共获取{len(finance_data)} 条财经新闻，'
                 f'最新一条finance新闻为【 {finance_data[-1]["title"]}：{finance_data[-1]["url"]}】')
        return finance_data


if __name__ == '__main__':
    yicai_news_crawler = YiCaiNewsCrawler()
    finance_data = yicai_news_crawler.main()
    print(finance_data)