/**
 * HUD 风格主布局组件
 * HUD-style Main Layout Component
 *
 * 深色主题 + 发光效果
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
  Zap,
  ChevronRight,
  Activity,
  Database,
  Shield,
  Users,
  Building2,
  FileSearch,
  Server,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuthStore } from '../stores/authStore'
import { StoneDropdown, type DropdownItem } from '@/components/ui'
import { preloadRoute } from '@/utils/preload'
import QuotaDisplay from '@/components/QuotaDisplay'
import { isAdmin } from '../types/auth'

type NavColor = 'cyan' | 'purple' | 'green' | 'blue' | 'pink'

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
  preloadKey: 'dashboard' | 'news' | 'data-pool' | 'social' | 'telegram' | 'twitter' | 'search' | 'settings'
  color: NavColor
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: '仪表盘', icon: <LayoutDashboard className="w-5 h-5" />, preloadKey: 'dashboard', color: 'cyan' },
  { path: '/data-pool', label: '数据池', icon: <Database className="w-5 h-5" />, preloadKey: 'data-pool', color: 'green' },
  { path: '/news', label: '新闻管理', icon: <FileText className="w-5 h-5" />, preloadKey: 'news', color: 'purple' },
  { path: '/social', label: '社交数据', icon: <MessageSquare className="w-5 h-5" />, preloadKey: 'social', color: 'green' },
  { path: '/telegram', label: 'Telegram', icon: <Send className="w-5 h-5" />, preloadKey: 'telegram', color: 'cyan' },
  { path: '/twitter', label: 'Twitter', icon: <Twitter className="w-5 h-5" />, preloadKey: 'twitter', color: 'blue' },
  { path: '/search', label: '全文搜索', icon: <Search className="w-5 h-5" />, preloadKey: 'search', color: 'pink' },
  { path: '/settings', label: '系统设置', icon: <Settings className="w-5 h-5" />, preloadKey: 'settings', color: 'purple' },
]

// 管理员导航项
const adminNavItems: NavItem[] = [
  { path: '/admin/tenants', label: '租户管理', icon: <Building2 className="w-5 h-5" />, preloadKey: 'settings', color: 'cyan' },
  { path: '/admin/users', label: '用户管理', icon: <Users className="w-5 h-5" />, preloadKey: 'settings', color: 'purple' },
  { path: '/admin/audit-logs', label: '审计日志', icon: <FileSearch className="w-5 h-5" />, preloadKey: 'settings', color: 'green' },
  { path: '/admin/system', label: '系统监控', icon: <Server className="w-5 h-5" />, preloadKey: 'settings', color: 'blue' },
]

const colorClasses: Record<NavColor, { active: string; hover: string; glow: string }> = {
  cyan: {
    active: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.3)]',
    hover: 'hover:border-cyan-500/30 hover:text-cyan-400',
    glow: 'text-cyan-400',
  },
  purple: {
    active: 'bg-purple-500/20 text-purple-400 border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.3)]',
    hover: 'hover:border-purple-500/30 hover:text-purple-400',
    glow: 'text-purple-400',
  },
  green: {
    active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.3)]',
    hover: 'hover:border-emerald-500/30 hover:text-emerald-400',
    glow: 'text-emerald-400',
  },
  blue: {
    active: 'bg-blue-500/20 text-blue-400 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]',
    hover: 'hover:border-blue-500/30 hover:text-blue-400',
    glow: 'text-blue-400',
  },
  pink: {
    active: 'bg-pink-500/20 text-pink-400 border-pink-500/50 shadow-[0_0_15px_rgba(236,72,153,0.3)]',
    hover: 'hover:border-pink-500/30 hover:text-pink-400',
    glow: 'text-pink-400',
  },
}

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
          {isAdmin(user) && (
            <span className="text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded">
              ADMIN
            </span>
          )}
        </div>
      ),
      icon: <User className="w-4 h-4" />,
      onClick: () => navigate('/profile'),
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
    <div className="min-h-screen bg-slate-950">
      {/* 顶部导航栏 */}
      <nav className="fixed top-0 left-0 right-0 h-16 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800/50 z-50 px-4">
        <div className="h-full flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* 菜单切换按钮 */}
            <button
              className="p-2 hover:bg-slate-800/50 rounded-lg lg:hidden transition-colors"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? (
                <X className="w-5 h-5 text-slate-400" />
              ) : (
                <Menu className="w-5 h-5 text-slate-400" />
              )}
            </button>

            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-cyan-500/30 to-blue-500/30 rounded-lg flex items-center justify-center border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <Zap className="w-5 h-5 text-cyan-400" />
              </div>
              <h1 className="text-lg font-bold text-cyan-400 hidden sm:block tracking-wide">
                SPIDER NEWS
              </h1>
            </div>
          </div>

          {/* 右侧操作区 */}
          <div className="flex items-center gap-4">
            {/* 搜索框 */}
            <div className="hidden md:block">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="搜索..."
                  className="w-64 pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-200 placeholder-slate-500 text-sm outline-none focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all"
                />
              </div>
            </div>

            {/* 系统状态 */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <span className="text-sm text-slate-400 font-mono">ONLINE</span>
            </div>

            {/* 用户信息 */}
            <StoneDropdown
              trigger={
                <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg cursor-pointer hover:border-cyan-500/30 transition-all">
                  <div className="w-7 h-7 bg-gradient-to-br from-cyan-500/30 to-purple-500/30 rounded-lg flex items-center justify-center border border-cyan-500/30">
                    <span className="text-cyan-400 text-sm font-bold">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <span className="text-sm text-slate-300 hidden sm:block font-mono">
                    {user?.username || 'USER'}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-500 rotate-90" />
                </div>
              }
              items={userDropdownItems}
              position="bottom-right"
            />
          </div>
        </div>
      </nav>

      {/* 侧边栏 */}
      <aside
        className={clsx(
          'fixed top-16 left-0 bottom-0 w-64 bg-slate-900/50 backdrop-blur-xl border-r border-slate-800/50 transition-transform duration-300 z-40 flex flex-col',
          !sidebarOpen && '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* 导航区域 - 可滚动 */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          {navItems.map((item, index) => {
            const colors = colorClasses[item.color]
            return (
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
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 border border-transparent',
                    isActive
                      ? colors.active
                      : `text-slate-400 hover:bg-slate-800/50 ${colors.hover}`
                  )
                }
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {item.icon}
                <span className="font-medium">{item.label}</span>
              </NavLink>
            )
          })}

          {/* 管理员菜单 - 仅管理员可见 */}
          {isAdmin(user) && (
            <>
              <div className="my-4 border-t border-slate-700/50" />
              <div className="flex items-center gap-2 px-4 py-2 text-xs text-slate-500 font-medium uppercase tracking-wider">
                <Shield className="w-4 h-4" />
                管理中心
              </div>
              {adminNavItems.map((item, index) => {
                const colors = colorClasses[item.color]
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => {
                      if (window.innerWidth < 1024) {
                        setSidebarOpen(false)
                      }
                    }}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 border border-transparent',
                        isActive
                          ? colors.active
                          : `text-slate-400 hover:bg-slate-800/50 ${colors.hover}`
                      )
                    }
                    style={{ animationDelay: `${(navItems.length + index) * 0.05}s` }}
                  >
                    {item.icon}
                    <span className="font-medium">{item.label}</span>
                  </NavLink>
                )
              })}
            </>
          )}
        </nav>

        {/* 底部信息 - 固定在底部 */}
        <div className="flex-shrink-0 p-4 space-y-3 border-t border-slate-800/50">
          {/* 配额显示 */}
          <QuotaDisplay mode="compact" />

          {/* 版本信息 */}
          <div className="p-3 bg-slate-800/30 border border-slate-700/50 rounded-lg">
            <p className="text-xs text-slate-500 font-mono">SPIDER NEWS HUD</p>
            <p className="text-xs text-cyan-400/50 font-mono">v2.0.0</p>
          </div>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main
        className={clsx(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarOpen ? 'lg:ml-64' : 'ml-0'
        )}
      >
        <Outlet />
      </main>

      {/* 移动端遮罩层 */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
