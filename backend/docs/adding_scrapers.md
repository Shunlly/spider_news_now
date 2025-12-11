# Adding New Scrapers

This guide explains how to add new news scrapers to the system without modifying core code.

## Overview

The scraper system uses a plugin architecture where each scraper inherits from `BaseScraper` and implements the required `scrape()` method.

## Step 1: Create the Scraper Class

Create a new file in `backend/app/scrapers/` with the naming convention `{source_key}_scraper.py`.

### Example: `example_scraper.py`

```python
"""Example news scraper implementation."""

from datetime import datetime
from typing import List, Dict, Any
import httpx

from app.scrapers.base import BaseScraper


class ExampleScraper(BaseScraper):
    """
    Scraper for Example News website.
    """

    def __init__(self):
        super().__init__(
            source_key="example",  # Must match lowercase class prefix
            display_name="Example News"
        )
        self.base_url = "https://news.example.com"

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape articles from Example News.

        Returns:
            List of article dictionaries with url, title, category, published_at
        """
        articles = []

        async with httpx.AsyncClient() as client:
            # Example: Fetch news from API
            response = await client.get(f"{self.base_url}/api/news")
            data = response.json()

            for item in data.get("articles", []):
                article = {
                    "url": item["link"],
                    "title": item["title"],
                    "category": item.get("category", "general"),
                    "published_at": datetime.fromisoformat(item["date"]),
                }
                articles.append(article)

        return articles
```

## Step 2: Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| File name | `{source_key}_scraper.py` | `example_scraper.py` |
| Class name | `{SourceKey}Scraper` | `ExampleScraper` |
| source_key | lowercase, alphanumeric + underscore | `example`, `my_source` |

**Important**: The class name must be the capitalized version of `source_key` followed by `Scraper`.
- `source_key="sina"` → `SinaScraper`
- `source_key="example"` → `ExampleScraper`
- `source_key="my_source"` → `My_sourceScraper` (avoid underscores in source_key)

## Step 3: Required Methods

### `scrape()` - Required

Returns a list of article dictionaries:

```python
async def scrape(self) -> List[Dict[str, Any]]:
    """
    Returns:
        List[Dict] with keys:
            - url: str (required) - Article URL
            - title: str (required) - Article title
            - category: str (optional) - Category code
            - published_at: datetime (optional) - Publication time
    """
    pass
```

### `parse()` - Optional Override

Override if you need custom parsing logic:

```python
def parse(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
    """Custom parsing logic."""
    # Call parent implementation first
    article = super().parse(raw_article)
    # Add custom processing
    article["category"] = self._map_category(article["category"])
    return article
```

### `validate()` - Optional Override

Override for additional validation:

```python
def validate(self, article: Dict[str, Any]) -> bool:
    """Custom validation."""
    if not super().validate(article):
        return False
    # Add custom validation
    if "blocked-domain" in article["url"]:
        return False
    return True
```

## Step 4: Register via API

Once your scraper file is created, register it via the API:

```bash
# Create new source
curl -X POST http://localhost:8000/api/v1/scrapers \
  -H "Content-Type: application/json" \
  -d '{
    "source_key": "example",
    "display_name": "Example News",
    "scraper_module": "app.scrapers.example_scraper",
    "enabled": true,
    "schedule_interval": 1800
  }'
```

### API Response

```json
{
  "id": 7,
  "source_key": "example",
  "display_name": "Example News",
  "enabled": true,
  "status": "idle",
  "schedule_interval": 1800,
  "last_run_at": null,
  "last_success_at": null,
  "failure_count": 0
}
```

## Step 5: Test the Scraper

### Manual Trigger

```bash
curl -X POST http://localhost:8000/api/v1/scrapers/example/trigger
```

### Check Status

```bash
curl http://localhost:8000/api/v1/scrapers/status
```

### View Collected Articles

```bash
curl "http://localhost:8000/api/v1/news/articles?source=example"
```

## Step 6: Manage the Scraper

### Enable/Disable

```bash
# Disable
curl -X PUT http://localhost:8000/api/v1/scrapers/example/disable

# Enable
curl -X PUT http://localhost:8000/api/v1/scrapers/example/enable
```

### Update Schedule

```bash
curl -X PUT http://localhost:8000/api/v1/scrapers/example/config \
  -H "Content-Type: application/json" \
  -d '{"schedule_interval": 3600}'  # Run every hour
```

## Category Codes

Use standard category codes for consistency:

| Code | Description |
|------|-------------|
| `ent` | Entertainment |
| `china` | Domestic (China) |
| `world` | International |
| `military` | Military |
| `finance` | Finance/Business |
| `tech` | Technology |
| `sports` | Sports |

## Error Handling

The base class handles errors gracefully:

1. If `scrape()` raises an exception, an empty list is returned
2. Individual article parsing errors don't stop other articles
3. Failed scraper runs are logged and tracked

## Using Playwright for JavaScript Sites

For sites that require JavaScript rendering:

```python
from playwright.async_api import async_playwright

class DynamicScraper(BaseScraper):
    async def scrape(self) -> List[Dict[str, Any]]:
        articles = []

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto(self.base_url)
            await page.wait_for_selector(".article-list")

            items = await page.query_selector_all(".article-item")
            for item in items:
                title = await item.query_selector("h2")
                link = await item.query_selector("a")
                articles.append({
                    "title": await title.inner_text(),
                    "url": await link.get_attribute("href"),
                })

            await browser.close()

        return articles
```

## Best Practices

1. **Rate Limiting**: Add delays between requests to avoid being blocked
2. **User Agent**: Set appropriate User-Agent headers
3. **Error Handling**: Handle network errors, timeouts, and parsing failures
4. **Logging**: Use `self.logger` for debugging and monitoring
5. **Testing**: Test your scraper independently before registering

## Example: Complete Scraper

See existing scrapers for reference:

- `backend/app/scrapers/sina_scraper.py` - Basic HTTP scraper
- `backend/app/scrapers/qq_scraper.py` - API-based scraper
- `backend/app/scrapers/wangyi_scraper.py` - Playwright-based scraper

## Troubleshooting

### "Scraper class not found"

Ensure your class name follows the convention: `{SourceKey}Scraper`

### "Cannot import module"

Check the `scraper_module` path is correct: `app.scrapers.your_scraper`

### Articles not appearing

1. Check scraper logs: `docker-compose logs backend`
2. Verify `scrape()` returns valid article dicts
3. Check article validation (URL format, non-empty title)
