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
export { default as telegramService } from './telegramService'
export type {
  TelegramUserInfo,
  TelegramDialog,
  TelegramEntity,
  TelegramMessage,
  TelegramBaseResponse,
  TelegramStatusResponse,
} from './telegramService'
export { default as quotaService } from './quotaService'
export { default as adminService } from './adminService'
export type {
  Tenant,
  CreateTenantRequest,
  UpdateTenantRequest,
  TenantListResponse,
  SystemStats,
  AuditLog,
  AuditLogListResponse,
  SystemMetrics,
  HealthStatus,
} from './adminService'
export { default as dataPoolService } from './dataPoolService'
export type {
  DataVisibility,
  PlatformType,
  DataPointer,
  ArticleContent,
  ArticleAnalysis,
  DataPointerDetail,
  DataPointerListResponse,
  UserDataRelation,
  DomainStats,
  DataPoolStatistics,
} from './dataPoolService'
