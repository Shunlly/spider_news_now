import json

import requests
from anti_useragent import UserAgent

from src.common.log import log


class HuanqiuNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
        }
        self.base_url = "https://mil.huanqiu.com/api/list2"
        self.article_url = "https://mil.huanqiu.com/article/"
        self.params = {
            'node': '/e3pmh1dm8/e3pmt7hva',
            'offset': 0,
            'limit': 24
        }

    def get_mil_news(self, pages=3):
        """
        获取环球军事新闻

        :param pages: 要获取的页数,默认3页
        :return: 包含所有新闻的列表
        """
        news_data = []

        for page in range(pages):
            # 计算每页的offset
            offset = page * 24

            # 更新params
            params = {
                'node': '/e3pmh1dm8/e3pmt7hva',
                'offset': offset,
                'limit': 24
            }

            try:
                res = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                res.raise_for_status()
                list_json = json.loads(res.text)

                # 提取当前页的新闻
                items = list_json.get('list', [])
                valid_count = 0
                for item in items:
                    # 安全获取字段,避免None值 (字段名是 aid 而不是 ait)
                    aid = item.get('aid')
                    title = item.get('title')

                    if aid and title:
                        news_data.append({
                            "url": f"{self.article_url}{aid.strip()}",
                            'title': title.strip(),
                            "type": "mil",
                            "source": "huanqiu"
                        })
                        valid_count += 1

                log.info(f"成功获取第 {page + 1} 页,共 {len(items)} 条新闻,有效 {valid_count} 条")

            except Exception as e:
                # 获取单页失败，保留Exception以不中断批量处理
                log.error(f"获取第 {page + 1} 页失败: {e}")
                continue

        log.info(f"总共获取 {len(news_data)} 条新闻")
        return news_data

    def main(self):
        mil_news = self.get_mil_news()
        mil_news.reverse()
        log.info(f'环球网新闻爬取完成，共获取 {len(mil_news)} 条军事新闻'
                 f'最新一条mil新闻为【 {mil_news[-1]["title"]}：{mil_news[-1]["url"]}】')

        return mil_news



if __name__ == '__main__':
    HuanqiuNewsCrawler().main()