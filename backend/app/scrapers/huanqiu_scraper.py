"""Huanqiu News scraper - refactored for async with BaseScraper."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

import httpx

from app.scrapers.base import BaseScraper


class HuanqiuScraper(BaseScraper):
    """Scraper for Huanqiu News (环球网) - Military channel."""

    def __init__(self):
        super().__init__(source_key="huanqiu", display_name="环球网")
        self.base_url = "https://mil.huanqiu.com/api/list2"
        self.article_url = "https://mil.huanqiu.com/article/"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape military news from Huanqiu using API."""
        news_data = []
        try:
            params = {
                'node': '/e3pmh1dm8/e3pmt7hva',
                'offset': 0,
                'limit': 24
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Fetch 3 pages
                for page_num in range(3):
                    params['offset'] = page_num * 24

                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()

                    data = response.json()
                    articles = data.get('list', [])

                    for article in articles:
                        aid = article.get('aid')
                        title = article.get('title')

                        if aid and title:
                            news_data.append({
                                "url": f"{self.article_url}{aid}",
                                "title": title,
                                "category": "military",
                                "published_at": datetime.now(),
                            })

                    await asyncio.sleep(1)  # Rate limiting

            self.logger.info(f"Scraped {len(news_data)} articles")
            return news_data

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            return news_data
