/**
 * 数据导出服务
 * Data Export Service
 */

import apiClient from './api'

export type DataSource = 'news' | 'social_sessions' | 'social_messages'
// 后端枚举名称为大写 (CSV, JSON, EXCEL)
export type ExportFormat = 'CSV' | 'JSON' | 'EXCEL'
// 后端枚举状态也为大写
export type ExportStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED'

export interface ExportTask {
  id: number
  data_source: DataSource
  export_format: ExportFormat
  status: ExportStatus
  filename: string
  file_path?: string
  file_size?: number
  total_records?: number
  exported_records?: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface ExportListResponse {
  data: ExportTask[]
  total: number
}

export interface ExportActionResponse {
  success: boolean
  message: string
  task?: ExportTask
  download_url?: string
}

export const exportsService = {
  // 获取导出任务列表
  async getExportTasks(params?: {
    status?: ExportStatus
    data_source?: DataSource
    limit?: number
    offset?: number
  }): Promise<ExportListResponse> {
    return apiClient.get('/exports', { params })
  },

  // 获取导出任务详情
  async getExportTask(id: number): Promise<ExportTask> {
    return apiClient.get(`/exports/${id}`)
  },

  // 创建导出任务
  async createExport(data: {
    data_source: DataSource
    export_format: ExportFormat
    filters?: Record<string, string | number | boolean>
    filename?: string
  }): Promise<ExportActionResponse> {
    return apiClient.post('/exports', data)
  },

  // 下载导出文件
  async downloadExport(id: number): Promise<Blob> {
    return apiClient.get(`/exports/${id}/download`, {
      responseType: 'blob',
    })
  },

  // 重试导出任务
  async retryExport(id: number): Promise<ExportActionResponse> {
    return apiClient.post(`/exports/${id}/retry`)
  },

  // 删除导出任务
  async deleteExport(id: number): Promise<ExportActionResponse> {
    return apiClient.delete(`/exports/${id}`)
  },

  // 清理过期导出
  async cleanupExports(days = 7): Promise<ExportActionResponse> {
    return apiClient.post('/exports/cleanup', null, { params: { days } })
  },

  // 获取下载 URL
  getDownloadUrl(id: number): string {
    return `/api/v1/exports/${id}/download`
  },
}

export default exportsService
