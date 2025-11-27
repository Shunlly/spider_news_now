from typing import Union, Dict, List
import requests
from bs4 import BeautifulSoup


class CurrentEvents:
    """
    时事
    """
    def __init__(self):
        pass

    def get_163_current_events(self) -> Union[List[Dict], None]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            res = requests.get('https://news.163.com/domestic/', headers=headers, timeout=10)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'html.parser')

            news_list = []
            processed_urls = set()

            # 查找所有链接，过滤出新闻文章
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                url = link.get('href', '')
                title = link.get_text(strip=True)

                # 基本过滤：必须有URL和标题，标题长度要合适
                if not url or not title or len(title) < 5:
                    continue

                # 确保URL是完整的
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = 'https://news.163.com' + url

                # 检查是否是新闻文章链接（通常以.html结尾或包含特定路径）
                if not (url.endswith('.html') or '/dy/article/' in url or '/news/article/' in url):
                    continue

                # 检查是否是163新闻域名
                if 'news.163.com' not in url and '163.com' not in url:
                    continue

                # 过滤掉导航链接等非新闻内容
                excluded_keywords = ['首页', '国内', '国际', '军事', '财经', '体育', '娱乐', '科技',
                                   '手机', '数码', '女人', '论坛', '视频', '房产', '家居', '教育',
                                   '读书', '游戏', '彩票', '健康', '旅游', '文化', '艺术', '更多',
                                   '网易新闻', '网易', '登录', '注册', '客户端', '反馈']

                if any(keyword in title for keyword in excluded_keywords):
                    continue

                # 避免重复
                if url in processed_urls:
                    continue

                processed_urls.add(url)
                news_list.append({
                    'url': url,
                    'title': title
                })

                # 限制返回数量，避免过多
                if len(news_list) >= 20:
                    break

            return news_list if news_list else None

        except requests.RequestException as e:
            print(f"请求163新闻失败: {e}")
            return None
        except Exception as e:
            print(f"解析163新闻失败: {e}")
            return None

if __name__ == '__main__':
    current_events = CurrentEvents()
    news_list = current_events.get_163_current_events()
    if news_list:
        for news in news_list:
            print(f"标题: {news['title']}")
            print(f"URL: {news['url']}")
            print()