from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import requests
from sqlalchemy.orm import Session
from tenacity import stop_after_attempt, retry, wait_exponential, retry_if_exception_type

from src.app.data_sources.news_now.huanqiu_news_crawler import HuanqiuNewsCrawler
from src.app.data_sources.news_now.ifeng_news_crawler import IfengNewsCrawler
from src.app.data_sources.news_now.qq_news_crawler import QQNewsCrawler
from src.app.data_sources.news_now.sina_news_crawler import SinaNewsCrawler
from src.app.data_sources.news_now.wangyi_news_crawler import WangyiNewsCrawler
from src.app.data_sources.news_now.yicai_news_crawler import YiCaiNewsCrawler
from src.app.data_sources.source_base import DataSourceBase
from src.common.log import log
from src.common.exceptions import (
    DataSourceAPIError,
    DataSourceParseError,
    HTTPRequestError,
    HTTPTimeoutError,
)
from src.core.constants import SourceCategory
from src.database.sync_db import get_sync_db_session
from src.service.chat_question_disassemble import ChatQuestionDisassembleService
from src.service.chat_search_disassemble import ChatSearchDisassembleService
from src.service.source_config import source_config
from src.service.source_type import source_type_service
from src.service.whole_news import WholeNewsService
from src.utils.markdown_handle import strip_lead_ast
from src.utils.sync_task_util import save_sync_task
import re


class NewsNowClient(DataSourceBase):
    """新闻数据源客户端

    支持从多个新闻源爬取实时新闻，包括新浪、腾讯、网易等。

    Attributes:
        base_url: NewNow API基础URL
        id_value: 支持的新闻源ID列表
        channel_dict: 频道映射字典
    """

    def __init__(self) -> None:
        super().__init__()
        self.base_url: str = "https://newsnow.busiyi.world/api"
        self.id_value: List[str] = ["thepaper", "ifeng", "cls", "wallstreetcn", "ithome", "zaobao"]
        self.channel_dict: Dict[str, str] = {
            "sina-china_events": "新浪国内",
            "sina-world_events": "新浪国际",
            "sina-ent": "新浪娱乐",
            # "ifeng-mil": "凤凰军事",
            # "ifeng-finance": "凤凰财经",
            "qq_news-sports": "腾讯体育",
            "qq_news-tech": "腾讯科技",
            "163-culture": "网易文化",
            "yicai-finance": "第一财经",
            "huanqiu-mil": "环球军事",
        }


    @staticmethod
    def fix_sina_image_links(md_content: str) -> str:
        """修复新浪新闻中的图片链接

        将类似 //wx1.sinaimg.cn 和 //k.sinaimg.cn 这样的相对链接
        转换为完整的 https:// 链接

        Args:
            md_content: Markdown内容

        Returns:
            修复后的Markdown内容
        """
        # 匹配以 // 开头，包含 sinaimg.cn 的图片链接
        pattern = r'(\!\[.*?\]\()(//(wx\d+\.sinaimg\.cn|k\.sinaimg\.cn)[^\)]+)(\))'

        def add_https(match):
            return f"{match.group(1)}https:{match.group(2)}{match.group(4)}"

        fixed_content = re.sub(pattern, add_https, md_content)
        return fixed_content

    def get_news_source_id(self, idv: str, source: str) -> Optional[str]:
        """获取新闻源配置ID

        Args:
            idv: 新闻类型标识
            source: 新闻来源

        Returns:
            源配置ID，如果未找到返回None

        Raises:
            KeyError: 当频道键不存在时
        """
        db: Session = get_sync_db_session()
        try:
            source_type_id = source_type_service.get_hot_news_source_type_id(db)
            key = f"{source}-{idv}"
            name = self.channel_dict[key]  # 可能抛出KeyError
            source_config_id = source_config.get_by_source_config_id(db, source_type_id, name)
            if source_config_id:
                return source_config_id.id
            else:
                log.warning(f"未找到source_config配置: source_type_id={source_type_id}, name={name}")
                return None
        finally:
            db.close()

    @staticmethod
    def get_other_news() -> List[Dict[str, str]]:
        """获取其他新闻 - 多线程版本

        Returns:
            新闻列表，每个新闻包含url, title, type, source等字段
        """
        all_news: List[Dict[str, str]] = []

        # 定义各个爬虫任务
        def fetch_sina() -> List[Dict[str, str]]:
            try:
                sina = SinaNewsCrawler()
                news = sina.main()
                log.info(f"新浪新闻: {len(news)} 条")
                return news
            except Exception as e:
                # 爬虫任务失败，返回空列表
                log.error(f"新浪新闻爬取失败: {str(e)}")
                return []

        # def fetch_ifeng():
        #     try:
        #         ifeng = IfengNewsCrawler()
        #         news = ifeng.main()
        #         log.info(f"凤凰新闻: {len(news)} 条")
        #         return news
        #     except Exception as e:
        #         log.error(f"凤凰新闻爬取失败: {str(e)}")
        #         return []

        def fetch_qq():
            try:
                qq = QQNewsCrawler()
                news = qq.main()
                log.info(f"腾讯新闻: {len(news)} 条")
                return news
            except Exception as e:
                # 爬虫任务失败，返回空列表
                log.error(f"腾讯新闻爬取失败: {str(e)}")
                return []

        def fetch_wangyi():
            try:
                wangyi = WangyiNewsCrawler()
                news = wangyi.main()
                log.info(f"网易新闻: {len(news)} 条")
                return news
            except Exception as e:
                # 爬虫任务失败，返回空列表
                log.error(f"网易新闻爬取失败: {str(e)}")
                return []

        def fetch_yicai():
            try:
                yicai = YiCaiNewsCrawler()
                news = yicai.main()
                log.info(f"第一财经新闻: {len(news)} 条")
                return news
            except Exception as e:
                # 爬虫任务失败，返回空列表
                log.error(f"第一财经新闻爬取失败: {str(e)}")
                return []

        def fetch_huanqiu():
            try:
                huanqiu = HuanqiuNewsCrawler()
                news = huanqiu.main()
                log.info(f"环球网新闻: {len(news)} 条")
                return news
            except Exception as e:
                # 爬虫任务失败，返回空列表
                log.error(f"环球网新闻爬取失败: {str(e)}")
                return []

        try:
            # 使用线程池并发执行所有爬虫任务
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(fetch_sina): "新浪",
                    # executor.submit(fetch_ifeng): "凤凰",
                    executor.submit(fetch_qq): "腾讯",
                    executor.submit(fetch_wangyi): "网易",
                    executor.submit(fetch_yicai): "第一财经",
                    executor.submit(fetch_huanqiu): "环球网",
                }

                # 收集结果
                for future in as_completed(futures):
                    source_name = futures[future]
                    try:
                        result = future.result()
                        all_news.extend(result)
                    except Exception as e:
                        # 并发任务中的单个爬虫失败，记录后继续
                        log.error(f"{source_name}新闻处理异常: {str(e)}")

            log.info(f"总共获取到 {len(all_news)} 条新闻")
            return all_news

        except Exception as e:
            # 线程池执行异常，返回已获取的新闻
            log.error(f"获取新闻时发生错误: {str(e)}")
            return all_news



    def main(self) -> None:
        """处理新闻爬取和存储的主流程

        获取各个新闻源的数据，解析为markdown，上传到存储，并保存到数据库。
        """
        s_time: datetime = datetime.now()
        whole_news: List[Dict[str, str]] = self.get_other_news()
        db: Session = get_sync_db_session()
        try:
            count: int = 1
            for wn in whole_news:
                try:
                    url: str = wn['url']
                    title: str = wn['title']
                    news_type: str = wn['type']
                    source: str = wn['source']
                    log.info(f"正在处理: {title}")

                    # 检查URL是否已存在
                    news = WholeNewsService.get_by_news_url(db, url)
                    if news:
                        log.info(f"已解析相应的url：{url}")
                        continue

                    # 获取source_config_id，如果获取失败则跳过
                    try:
                        source_config_id = self.get_news_source_id(news_type, source)
                        if not source_config_id:
                            log.warning(f"未找到source_config_id，跳过处理: {title}, source={source}, type={news_type}")
                            continue
                    except KeyError as e:
                        log.warning(f"频道配置不存在，跳过处理: {title}, key={source}-{news_type}, error={str(e)}")
                        continue
                    except Exception as e:
                        # 获取source_config_id失败，跳过当前新闻
                        log.error(f"获取source_config_id失败，跳过处理: {title}, error={str(e)}")
                        continue

                    # 远程解析url成md
                    md_result: Optional[str] = self.unifuncs_reader(url)
                    # 本地的解析url成md
                    # md_result = self.parse_url(url)
                    if md_result:
                        new_md: str = strip_lead_ast(md_result)
                        # 如果是新浪新闻，修复图片链接
                        if source == 'sina':
                            new_md = self.fix_sina_image_links(new_md)
                        storage_path: str = self.upload_md(new_md, title)
                        parse_md = self.parse_md(storage_path, source_config_id, url)
                        document_id = None
                        if parse_md:
                            document_id = parse_md[0]['document_id']
                        if not document_id:
                            log.error(f"document_id为空，调用自动解析失败，原始数据为{str(parse_md)}")
                        log.info(f"处理完成: {title}")
                        db_inner = get_sync_db_session()
                        try:
                            news_record = WholeNewsService.create(
                                db_inner,
                                news_source=source,
                                news_url=url,
                                news_path=storage_path,
                                document_id=document_id,
                                extra_data=wn,
                                news_type=news_type,
                                source_config_id=source_config_id
                            )
                            db_inner.commit()
                            if news_record:
                                log.info(f"保存成功: {title}")
                            else:
                                log.error(f"保存失败: {title}")
                                continue
                            e_time = datetime.now()
                            save_sync_task(db=db_inner,
                                           s_time=s_time,
                                           e_time=e_time,
                                           task_type="UPLOAD",
                                           source_id=news_record.id,
                                           source_type=SourceCategory.ARTICLE.value,
                                           task_status="SUCCESS",
                                           total=count
                                           )
                            count += 1
                        finally:
                            db_inner.close()
                except Exception as e:
                    # 单条新闻处理失败，记录后继续处理下一条
                    log.error(f"获取新闻时发生错误: {str(e)}, 新闻url：{wn['url']}")
                    continue
            log.info("news now已经处理完成")
        finally:
            db.close()


if __name__ == '__main__':
    # config = NewsNowConfig()
    client = NewsNowClient()
    client.main()
