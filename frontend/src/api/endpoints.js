/**
 * API endpoint constants.
 */

export const API_ENDPOINTS = {
  // News endpoints
  NEWS_ARTICLES: '/news/articles',
  NEWS_ARTICLES_GROUPED: '/news/articles/grouped',
  NEWS_ARTICLE_DETAIL: (id) => `/news/articles/${id}`,
  NEWS_SOURCES: '/news/sources',
  NEWS_STATISTICS: '/news/statistics',

  // Scraper endpoints
  SCRAPERS_STATUS: '/scrapers/status',
  SCRAPER_TRIGGER: (sourceKey) => `/scrapers/${sourceKey}/trigger`,
  SCRAPER_RUNS: (sourceKey) => `/scrapers/${sourceKey}/runs`,
  SCRAPER_ENABLE: (sourceKey) => `/scrapers/${sourceKey}/enable`,
  SCRAPER_DISABLE: (sourceKey) => `/scrapers/${sourceKey}/disable`,

  // Health
  HEALTH: '/health'
}

export default API_ENDPOINTS
