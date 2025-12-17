/**
 * 错误处理工具函数
 * Error Handling Utilities
 */

/**
 * 从 unknown 类型的错误中提取错误消息
 * 用于 catch 块中安全地获取错误信息
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message)
  }
  return '未知错误'
}

/**
 * 检查是否为 API 错误响应
 */
export function isApiError(error: unknown): error is { response?: { data?: { message?: string; detail?: string } } } {
  return (
    error !== null &&
    typeof error === 'object' &&
    'response' in error
  )
}

/**
 * 从 API 错误中提取消息
 */
export function getApiErrorMessage(error: unknown, fallback = '操作失败'): string {
  if (isApiError(error)) {
    const data = error.response?.data
    if (data?.message) return data.message
    if (data?.detail) return data.detail
  }
  const msg = getErrorMessage(error)
  return msg !== '未知错误' ? msg : fallback
}
