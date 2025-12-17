/**
 * 主布局组件
 * Main Layout Component
 *
 * Stone 色系极简设计
 * 包含导航栏、侧边栏和主内容区域
 */

import { useState, useCallback } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Send,
  Twitter,
  Search,
  Settings,
  Menu,
  X,
  User,
  LogOut,
  Newspaper,
  ChevronRight,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuthStore } from '../stores/authStore'
import { StoneDropdown, type DropdownItem } from '@/components/ui'
import { preloadRoute } from '@/utils/preload'

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
  preloadKey: 'dashboard' | 'news' | 'social' | 'telegram' | 'twitter' | 'search' | 'settings'
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: '仪表盘', icon: <LayoutDashboard className="w-5 h-5" />, preloadKey: 'dashboard' },
  { path: '/news', label: '新闻管理', icon: <FileText className="w-5 h-5" />, preloadKey: 'news' },
  { path: '/social', label: '社交数据', icon: <MessageSquare className="w-5 h-5" />, preloadKey: 'social' },
  { path: '/telegram', label: 'Telegram', icon: <Send className="w-5 h-5" />, preloadKey: 'telegram' },
  { path: '/twitter', label: 'Twitter', icon: <Twitter className="w-5 h-5" />, preloadKey: 'twitter' },
  { path: '/search', label: '全文搜索', icon: <Search className="w-5 h-5" />, preloadKey: 'search' },
  { path: '/settings', label: '系统设置', icon: <Settings className="w-5 h-5" />, preloadKey: 'settings' },
]

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  // 预加载处理
  const handlePreload = useCallback((key: NavItem['preloadKey']) => {
    preloadRoute(key)
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const userDropdownItems: DropdownItem[] = [
    {
      key: 'profile',
      label: (
        <div className="flex items-center gap-2">
          <span>{user?.username || '用户'}</span>
          {user?.role === 'admin' && (
            <span className="text-xs bg-stone-900 text-white px-2 py-0.5 rounded">
              管理员
            </span>
          )}
        </div>
      ),
      icon: <User className="w-4 h-4" />,
    },
    { key: 'divider', label: '', divider: true },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogOut className="w-4 h-4" />,
      onClick: handleLogout,
      danger: true,
    },
  ]

  return (
    <div className="min-h-screen bg-stone-200">
      {/* 顶部导航栏 */}
      <nav className="stone-navbar">
        <div className="flex items-center gap-4">
          {/* 菜单切换按钮 */}
          <button
            className="p-2 hover:bg-stone-100 rounded-lg lg:hidden transition-colors"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? (
              <X className="w-5 h-5 text-stone-600" />
            ) : (
              <Menu className="w-5 h-5 text-stone-600" />
            )}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-stone-900 rounded-lg flex items-center justify-center">
              <Newspaper className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-lg font-semibold text-stone-900 hidden sm:block font-space-grotesk">
              Spider News
            </h1>
          </div>
        </div>

        {/* 右侧操作区 */}
        <div className="flex items-center gap-4">
          {/* 搜索框 */}
          <div className="hidden md:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
              <input
                type="text"
                placeholder="搜索..."
                className="w-64 pl-10 pr-4 py-2 bg-stone-100 border border-stone-200 rounded-xl text-stone-900 placeholder-stone-400 text-sm outline-none focus:bg-white focus:border-stone-300 transition-colors"
              />
            </div>
          </div>

          {/* 系统状态 */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-stone-200 rounded-xl">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-stone-600">系统正常</span>
          </div>

          {/* 用户信息 */}
          <StoneDropdown
            trigger={
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-stone-200 rounded-xl cursor-pointer hover:border-stone-300 transition-colors">
                <div className="w-7 h-7 bg-stone-900 rounded-lg flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <span className="text-sm text-stone-700 hidden sm:block">
                  {user?.username || '用户'}
                </span>
                <ChevronRight className="w-4 h-4 text-stone-400 rotate-90" />
              </div>
            }
            items={userDropdownItems}
            position="bottom-right"
          />
        </div>
      </nav>

      {/* 侧边栏 */}
      <aside
        className={clsx(
          'stone-sidebar transition-transform duration-300 z-40',
          !sidebarOpen && '-translate-x-full lg:translate-x-0'
        )}
      >
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onMouseEnter={() => handlePreload(item.preloadKey)}
              onClick={() => {
                if (window.innerWidth < 1024) {
                  setSidebarOpen(false)
                }
              }}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group',
                  isActive
                    ? 'bg-stone-900 text-white shadow-stone-sm'
                    : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
                )
              }
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* 底部信息 */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="p-4 bg-white border border-stone-200 rounded-xl">
            <p className="text-xs text-stone-400">Spider News Dashboard</p>
            <p className="text-xs text-stone-400">Version 2.0.0</p>
          </div>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main
        className={clsx(
          'pt-20 pb-8 px-6 transition-all duration-300 min-h-screen',
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
          className="fixed inset-0 bg-black/30 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
