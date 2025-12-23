/**
 * 配额服务
 * Quota Service
 *
 * 提供配额相关的 API 调用：
 * - 获取当前用户配额信息
 */

import apiClient from './api';
import type { QuotaInfo } from '../types/auth';

/**
 * 配额服务类
 */
class QuotaService {
  /**
   * 获取当前用户配额信息
   */
  async getQuota(): Promise<QuotaInfo> {
    return apiClient.get('/quota');
  }
}

// 导出单例
const quotaService = new QuotaService();
export default quotaService;
