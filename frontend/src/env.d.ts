/// <reference types="vite/client" />

// 扩展 Vite 环境变量类型
// eslint-disable-next-line @typescript-eslint/no-unused-vars
declare interface ImportMetaEnv {
  /** API 服务器基础地址 */
  readonly VITE_API_BASE_URL: string
  /** 应用标题 */
  readonly VITE_APP_TITLE: string
  /** WebSocket 服务器地址 (可选) */
  readonly VITE_WS_URL?: string
}

// 全局类型扩展
declare global {
  interface Window {
    /** Google Analytics */
    gtag?: (
      command: 'event',
      eventName: string,
      eventParams?: Record<string, unknown>
    ) => void
  }
}

export {}
