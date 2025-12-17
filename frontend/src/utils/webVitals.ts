/**
 * Web Vitals 性能监控
 * Web Vitals Performance Monitoring
 *
 * 监控核心 Web 指标：LCP, INP, CLS, FCP, TTFB
 */

type MetricName = 'CLS' | 'FCP' | 'INP' | 'LCP' | 'TTFB'

interface Metric {
  name: MetricName
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  delta: number
  id: string
  entries: PerformanceEntry[]
}

/**
 * 上报性能指标
 */
function reportMetric(metric: Metric) {
  // 开发环境打印到控制台
  if (import.meta.env.DEV) {
    const color =
      metric.rating === 'good'
        ? 'color: green'
        : metric.rating === 'needs-improvement'
          ? 'color: orange'
          : 'color: red'

    console.log(
      `%c[Web Vitals] ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating})`,
      color
    )
  }

  // 生产环境可以发送到分析服务
  // 例如: Google Analytics, 自建分析服务等
  if (import.meta.env.PROD) {
    // 使用 sendBeacon 异步上报，不阻塞页面
    // const data = {
    //   name: metric.name,
    //   value: metric.value,
    //   rating: metric.rating,
    //   delta: metric.delta,
    //   id: metric.id,
    //   url: window.location.href,
    //   timestamp: Date.now(),
    // }

    // 示例: 发送到自建分析端点
    // navigator.sendBeacon('/api/analytics/vitals', JSON.stringify(data))

    // 或者使用 Google Analytics 4
    if (typeof window.gtag === 'function') {
      window.gtag('event', metric.name, {
        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
        event_category: 'Web Vitals',
        event_label: metric.id,
        non_interaction: true,
      })
    }
  }
}

/**
 * 初始化 Web Vitals 监控
 * 使用动态导入以避免影响首屏加载
 */
export async function initWebVitals() {
  if (typeof window === 'undefined') return

  try {
    const { onCLS, onFCP, onINP, onLCP, onTTFB } = await import('web-vitals')

    // 注册所有指标监控
    onCLS(reportMetric)
    onFCP(reportMetric)
    onINP(reportMetric)
    onLCP(reportMetric)
    onTTFB(reportMetric)
  } catch {
    // web-vitals 未安装时静默失败
    console.debug('[Web Vitals] Library not available')
  }
}

/**
 * 获取当前性能快照
 */
export function getPerformanceSnapshot() {
  if (typeof window === 'undefined' || !window.performance) {
    return null
  }

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined

  if (!navigation) return null

  return {
    // DNS 查询时间
    dns: navigation.domainLookupEnd - navigation.domainLookupStart,
    // TCP 连接时间
    tcp: navigation.connectEnd - navigation.connectStart,
    // SSL 握手时间
    ssl: navigation.secureConnectionStart > 0
      ? navigation.connectEnd - navigation.secureConnectionStart
      : 0,
    // 首字节时间 (TTFB)
    ttfb: navigation.responseStart - navigation.requestStart,
    // 响应下载时间
    download: navigation.responseEnd - navigation.responseStart,
    // DOM 解析时间
    domParse: navigation.domContentLoadedEventEnd - navigation.responseEnd,
    // 页面完全加载时间
    loadComplete: navigation.loadEventEnd - navigation.fetchStart,
  }
}

// 添加 gtag 类型声明
declare global {
  interface Window {
    gtag?: (
      command: 'event',
      eventName: string,
      eventParams?: Record<string, unknown>
    ) => void
  }
}
