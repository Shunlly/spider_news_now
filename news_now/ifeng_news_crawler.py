from typing import Union, Dict, List
import requests
import time

from anti_useragent import UserAgent
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from src.common.log import log


class IfengNewsCrawler:
    """
    凤凰网新闻爬虫 - 模拟数据版本
    由于凤凰网有反爬虫机制，这里提供一个模拟实现
    """

    def __init__(self):
        self.channels = ['财经', '军事']
        self.headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        }


    def get_mil_channel_news(self, click_times: int = 2):
        news_list = []
        try:
            base_url = self.get_channel_urls()['军事']
            html = None
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置默认超时为 120 秒
                page.set_default_timeout(120000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                page.goto(base_url, wait_until="domcontentloaded", timeout=240000)

                # 等待第一页的新闻列表项加载出来
                page.wait_for_selector('ul.news-stream-basic-news-list li', timeout=30000)
                time.sleep(2)  # 额外等待确保数据完全加载

                # 点击"加载更多"按钮，触发 2 次
                for i in range(click_times):
                    try:
                        # 等待"加载更多"按钮出现
                        more_button = page.locator('.news-stream-basic-more')
                        if more_button.count() > 0:
                            more_button.click()
                            time.sleep(2)  # 等待新数据加载
                            log.info(f'军事频道第 {i+1} 次点击"加载更多"按钮成功')
                        else:
                            log.warning(f'军事频道第 {i+1} 次未找到"加载更多"按钮')
                            break
                    except Exception as e:
                        # 点击加载更多失败，保留Exception以不中断爬取
                        log.warning(f'军事频道第 {i+1} 次点击"加载更多"按钮失败: {e}')
                        break

                # 获取最终的 HTML
                html = page.content()
                browser.close()

            if not html:
                log.error('ifeng军事频道获取html失败')
                return news_list

            soup = BeautifulSoup(html, 'lxml')
            # 1. 找到目标 ul
            ul = soup.find('ul', class_='news-stream-basic-news-list')
            if not ul:
                log.error('未找到指定 ul')
                return news_list

            # 2. 遍历所有 li，提取第一个 <a> 的 href 与 title
            for li in ul.find_all('li'):
                a = li.find('a')
                if a and a.get('href') and a.get('title'):
                    # 补全相对路径
                    href = 'https:' + a['href'] if a['href'].startswith('//') else a['href']
                    news_list.append({'url': href, 'title': a['title'], "type": "mil", "source": "ifeng"})
            log.info(f'军事频道共获取 {len(news_list)} 条新闻')
            return news_list
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"获取军事频道新闻失败: {e}")
            return news_list


    def get_finance_channel_news(self) -> Union[List[Dict], None]:
        """
        获取财经频道的新闻
        """
        news_list = []
        try:
            base_url = self.get_channel_urls()["财经"]
            html = None
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 设置默认超时为 120 秒
                page.set_default_timeout(120000)

                # 使用 domcontentloaded 替代 networkidle，更快且更可靠
                page.goto(base_url, wait_until="domcontentloaded", timeout=120000)

                # 等待页面内容加载
                time.sleep(3)

                html = page.content()
                browser.close()

            if not html:
                log.error('ifeng财经频道获取html失败')
                return news_list
            soup = BeautifulSoup(html, 'lxml')

            # 1. 找到外层 div
            box = soup.find('div', class_='index_newsflow_3HdJW')
            if not box:
                log.error('ifeng财经频道目标 div 未找到')
                return news_list
            # 2. 取"第一个 div"（即包裹所有条目的那一层）
            first_div = box.find('div')
            if not first_div:
                log.error('ifeng内部 div 未找到')
                return news_list

            # 3. 循环同级 div 块
            for block in first_div.find_all('div', recursive=False):  # recursive=False 只取直系
                # 4. 第二个 <a>
                a_tags = block.find_all('a')
                if len(a_tags) < 2:
                    continue
                second_a = a_tags[1]
                href = second_a.get('href')
                text = second_a.get_text(strip=True)
                if href and text:
                    news_list.append({'url': href, 'title': text, "type": "finance", "source": "ifeng"})

            log.info(f'财经频道共获取 {len(news_list)} 条新闻')
            return news_list
        except Exception as e:
            # 爬虫操作失败，保留Exception以容错处理，返回已获取的数据
            log.error(f"获取财经频道新闻失败: {e}")
            return news_list



    def get_channel_urls(self) -> Dict[str, str]:
        """
        获取各频道的热榜URL
        """
        return {
            '财经': 'https://ishare.ifeng.com/hotFinanceRank',
            '科技': 'https://ishare.ifeng.com/hotTechRank',
            '军事': 'https://mil.ifeng.com/shanklist/14-35083-'
        }

    def main(self):
        log.info('开始爬取凤凰网新闻')
        # 军事频道数据
        mil_data, finance_data = [], []
        mil_data = self.get_mil_channel_news()
        # 财经频道数据
        finance_data = self.get_finance_channel_news()
        # 反转列表，让最新的排在最后
        mil_data.reverse()
        finance_data.reverse()
        news_data = mil_data + finance_data
        log.info(f'凤凰网新闻爬取完成，共获取 {len(mil_data)} 条军事新闻，{len(finance_data)} 条财经新闻，'
                 f'最新一条mil新闻为【 {mil_data[-1]["title"]}：{mil_data[-1]["url"]}】'
                 f'最新一条finance新闻为【 {finance_data[-1]["title"]}：{finance_data[-1]["url"]}】')
        return news_data



if __name__ == '__main__':
    crawler = IfengNewsCrawler()
    crawler.main()