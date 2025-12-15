/**
 * 主布局组件
 * Main Layout Component
 *
 * 遵循宪法 III.A Glassmorphism 设计规范
 * 包含导航栏、侧边栏和主内容区域
 */

import { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import {
  IconDashboard,
  IconFile,
  IconMessage,
  IconSend,
  IconSearch,
  IconSettings,
  IconMenu,
  IconClose,
} from '@arco-design/web-react/icon'
import clsx from 'clsx'

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: '仪表盘', icon: <IconDashboard /> },
  { path: '/news', label: '新闻管理', icon: <IconFile /> },
  { path: '/social', label: '社交数据', icon: <IconMessage /> },
  { path: '/telegram', label: 'Telegram', icon: <IconSend /> },
  { path: '/search', label: '全文搜索', icon: <IconSearch /> },
  { path: '/settings', label: '系统设置', icon: <IconSettings /> },
]

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen">
      {/* 顶部导航栏 */}
      <nav className="glass-navbar">
        <div className="flex items-center gap-4">
          {/* 菜单切换按钮 */}
          <button
            className="glass-button p-2 lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <IconClose /> : <IconMenu />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SN</span>
            </div>
            <h1 className="text-lg font-semibold text-white hidden sm:block">
              Spider News
            </h1>
          </div>
        </div>

        {/* 右侧操作区 */}
        <div className="flex items-center gap-4">
          {/* 搜索框 */}
          <div className="hidden md:block">
            <input
              type="text"
              placeholder="搜索..."
              className="glass-input w-64"
            />
          </div>

          {/* 系统状态 */}
          <div className="flex items-center gap-2 px-3 py-1.5 glass-card">
            <span className="status-dot status-dot-active" />
            <span className="text-sm text-white/70">系统正常</span>
          </div>
        </div>
      </nav>

      {/* 侧边栏 */}
      <aside
        className={clsx(
          'glass-sidebar transition-transform duration-300',
          !sidebarOpen && '-translate-x-full lg:translate-x-0'
        )}
      >
        <nav className="space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200',
                  isActive
                    ? 'bg-white/20 text-white border border-white/20'
                    : 'text-white/60 hover:text-white hover:bg-white/10'
                )
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* 底部信息 */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="glass-card p-4">
            <p className="text-xs text-white/40">Spider News Dashboard</p>
            <p className="text-xs text-white/40">Version 2.0.0</p>
          </div>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main
        className={clsx(
          'pt-20 pb-8 px-6 transition-all duration-300',
          sidebarOpen ? 'lg:ml-64' : 'ml-0'
        )}
      >
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>

      {/* 移动端遮罩层 */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
