/**
 * 服务层导出
 * Services Export
 */

export { default as apiClient } from './api'
export { default as newsService } from './newsService'
export type { NewsArticle, NewsListResponse, NewsStatistics } from './newsService'
export { default as searchService } from './searchService'
export type { SearchHit, SearchResponse, IndexStats } from './searchService'
export { default as socialService } from './socialService'
export type {
  Platform,
  SessionStatus,
  SocialSession,
  SocialMessage,
  SessionListResponse,
  MessageListResponse,
  SocialStatistics,
} from './socialService'
export { default as credentialsService } from './credentialsService'
export type {
  Credential,
  CredentialStatus,
  CredentialListResponse,
  CredentialActionResponse,
} from './credentialsService'
export { default as proxiesService } from './proxiesService'
export type {
  ProxyConfig,
  ProxyProtocol,
  ProxyStatus,
  ProxyListResponse,
  ProxyActionResponse,
} from './proxiesService'
export { default as exportsService } from './exportsService'
export type {
  DataSource,
  ExportFormat,
  ExportStatus,
  ExportTask,
  ExportListResponse,
  ExportActionResponse,
} from './exportsService'
export { default as scraperService } from './scraperService'
export type {
  ScraperStatus,
  ScraperStatusResponse,
  ScraperRunResponse,
  NewsSource,
  SourcesResponse,
} from './scraperService'
