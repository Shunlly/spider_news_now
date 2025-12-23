/**
 * 路由预加载工具
 * Route Preload Utilities
 *
 * 提前加载即将访问的路由组件
 */

// 路由组件映射
const routeComponents = {
  dashboard: () => import('../pages/DashboardPage'),
  'data-pool': () => import('../pages/DataPoolPage'),
  news: () => import('../pages/NewsPage'),
  social: () => import('../pages/SocialPage'),
  telegram: () => import('../pages/TelegramPage'),
  twitter: () => import('../pages/TwitterPage'),
  search: () => import('../pages/SearchPage'),
  settings: () => import('../pages/SettingsPage'),
}

type RouteName = keyof typeof routeComponents

// 预加载单个路由
export function preloadRoute(name: RouteName) {
  const loader = routeComponents[name]
  if (loader) {
    loader()
  }
}

// 预加载多个路由
export function preloadRoutes(names: RouteName[]) {
  names.forEach(preloadRoute)
}

// 预加载所有路由（适合空闲时使用）
export function preloadAllRoutes() {
  Object.values(routeComponents).forEach((loader) => loader())
}

// 在空闲时预加载常用路由
export function preloadOnIdle() {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      preloadRoutes(['dashboard', 'data-pool', 'news', 'social'])
    })
  } else {
    // Fallback for Safari（不支持 requestIdleCallback）
    // 500ms 后开始预加载，确保主页面已加载完成
    setTimeout(() => {
      preloadRoutes(['dashboard', 'data-pool', 'news', 'social'])
    }, 500)
  }
}
