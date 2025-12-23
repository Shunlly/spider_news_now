/**
 * HUD 风格数据池页面
 * HUD-style Data Pool Page
 *
 * 统一展示所有平台的数据
 */

import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import DOMPurify from 'dompurify'
import { HUDPanel, StoneButton, StoneModal, useToast } from '@/components/ui'
import {
  Search,
  RefreshCw,
  Filter,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Calendar,
  X,
  FileText,
  ChevronsLeft,
  ChevronsRight,
  Activity,
  Database,
  Star,
  Bookmark,
  Globe,
  Users,
  Lock,
  Newspaper,
  Twitter,
  MessageCircle,
  Shield,
  CheckSquare,
  Square,
} from 'lucide-react'
import {
  dataPoolService,
  type DataPointer,
  type DataPointerDetail,
  type DataPointerListResponse,
  type DataPoolStatistics,
  type DataVisibility,
} from '@/services'
import { useAuthStore } from '@/stores/authStore'
import { isAdmin as checkIsAdmin } from '@/types/auth'

// 平台图标映射
const platformIcons: Record<string, React.ReactNode> = {
  news: <Newspaper className="w-4 h-4" />,
  twitter: <Twitter className="w-4 h-4" />,
  telegram: <MessageCircle className="w-4 h-4" />,
}

// 可见性图标映射
const visibilityIcons: Record<DataVisibility, React.ReactNode> = {
  private: <Lock className="w-3 h-3" />,
  tenant_shared: <Users className="w-3 h-3" />,
  public: <Globe className="w-3 h-3" />,
}

// 可见性颜色
const visibilityColors: Record<DataVisibility, string> = {
  private: 'text-red-400 bg-red-500/20 border-red-500/30',
  tenant_shared: 'text-amber-400 bg-amber-500/20 border-amber-500/30',
  public: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30',
}

// 可见性中文名
const visibilityLabels: Record<DataVisibility, string> = {
  private: '私有',
  tenant_shared: '团队共享',
  public: '公开',
}

export default function DataPoolPage() {
  const toast = useToast()
  const { user } = useAuthStore()
  const isAdmin = checkIsAdmin(user)

  const [pointers, setPointers] = useState<DataPointer[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [jumpPage, setJumpPage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedDomain, setSelectedDomain] = useState('')
  const [statistics, setStatistics] = useState<DataPoolStatistics | null>(null)

  // 视图模式: all | favorites | bookmarks
  const [viewMode, setViewMode] = useState<'all' | 'favorites' | 'bookmarks'>('all')

  // 详情模态框
  const [selectedPointer, setSelectedPointer] = useState<DataPointerDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // 管理员功能 - 批量选择和可见性管理
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [showVisibilityModal, setShowVisibilityModal] = useState(false)
  const [targetVisibility, setTargetVisibility] = useState<DataVisibility>('private')
  const [updatingVisibility, setUpdatingVisibility] = useState(false)

  const fetchPointers = useCallback(async () => {
    setLoading(true)
    try {
      let response: DataPointerListResponse

      if (viewMode === 'favorites') {
        response = await dataPoolService.getFavorites({ page, page_size: pageSize })
      } else if (viewMode === 'bookmarks') {
        response = await dataPoolService.getBookmarks({ page, page_size: pageSize })
      } else {
        const params: Record<string, string | number> = {
          page,
          page_size: pageSize,
        }
        if (selectedDomain) params.domain = selectedDomain
        response = await dataPoolService.getDataPointers(params)
      }

      setPointers(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('Failed to fetch data pointers:', error)
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, selectedDomain, viewMode])

  const fetchStatistics = async () => {
    try {
      const stats = await dataPoolService.getStatistics()
      setStatistics(stats)
    } catch (error) {
      console.error('Failed to fetch statistics:', error)
    }
  }

  useEffect(() => {
    fetchPointers()
  }, [fetchPointers])

  useEffect(() => {
    fetchStatistics()
  }, [])

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      if (searchQuery !== debouncedSearch && page !== 1) {
        setPage(1)
      }
    }, 500)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery])

  // 查看详情
  const handleViewDetail = async (pointer: DataPointer) => {
    setSelectedPointer(pointer as DataPointerDetail)
    setDetailLoading(true)
    try {
      const detail = await dataPoolService.getDataPointer(pointer.id)
      setSelectedPointer(detail)
    } catch (error) {
      console.error('Failed to fetch detail:', error)
      toast.error('获取详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  // 切换收藏
  const handleToggleFavorite = async (pointerId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const result = await dataPoolService.toggleFavorite(pointerId)
      // 更新本地状态
      setPointers(prev => prev.map(p =>
        p.id === pointerId ? { ...p, _isFavorited: result.is_favorited } as DataPointer : p
      ))
      toast.success(result.is_favorited ? '已收藏' : '已取消收藏')
      // 如果在收藏视图中取消收藏，刷新列表
      if (viewMode === 'favorites' && !result.is_favorited) {
        fetchPointers()
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      toast.error('操作失败')
    }
  }

  // 切换书签
  const handleToggleBookmark = async (pointerId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const result = await dataPoolService.toggleBookmark(pointerId)
      setPointers(prev => prev.map(p =>
        p.id === pointerId ? { ...p, _isBookmarked: result.is_bookmarked } as DataPointer : p
      ))
      toast.success(result.is_bookmarked ? '已添加书签' : '已移除书签')
      // 如果在书签视图中取消书签，刷新列表
      if (viewMode === 'bookmarks' && !result.is_bookmarked) {
        fetchPointers()
      }
    } catch (error) {
      console.error('Failed to toggle bookmark:', error)
      toast.error('操作失败')
    }
  }

  // ========== 管理员功能 ==========

  // 切换选中状态
  const handleToggleSelect = (pointerId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(pointerId)) {
        newSet.delete(pointerId)
      } else {
        newSet.add(pointerId)
      }
      return newSet
    })
  }

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedIds.size === pointers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(pointers.map(p => p.id)))
    }
  }

  // 更新单个项目的可见性
  const handleUpdateVisibility = async (pointerId: string, visibility: DataVisibility) => {
    try {
      await dataPoolService.updateVisibility(pointerId, visibility)
      setPointers(prev => prev.map(p =>
        p.id === pointerId ? { ...p, visibility } : p
      ))
      toast.success('可见性已更新')
    } catch (error) {
      console.error('Failed to update visibility:', error)
      toast.error('更新失败')
    }
  }

  // 批量更新可见性
  const handleBatchUpdateVisibility = async () => {
    if (selectedIds.size === 0) {
      toast.error('请先选择数据')
      return
    }
    setUpdatingVisibility(true)
    try {
      const result = await dataPoolService.batchUpdateVisibility(
        Array.from(selectedIds),
        targetVisibility
      )
      setPointers(prev => prev.map(p =>
        selectedIds.has(p.id) ? { ...p, visibility: targetVisibility } : p
      ))
      toast.success(`已更新 ${result.updated_count} 条数据的可见性`)
      setShowVisibilityModal(false)
      setSelectedIds(new Set())
    } catch (error) {
      console.error('Failed to batch update visibility:', error)
      toast.error('批量更新失败')
    } finally {
      setUpdatingVisibility(false)
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const domains = statistics?.by_domain || []

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">数据池</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>共 <span className="text-cyan-400 font-mono">{statistics?.total_pointers?.toLocaleString() || 0}</span> 条数据</span>
            {statistics && (
              <>
                <span className="text-slate-600">|</span>
                <Star className="w-4 h-4 text-amber-400" />
                <span className="text-slate-400">{statistics.user_favorites_count} 收藏</span>
                <Bookmark className="w-4 h-4 text-purple-400" />
                <span className="text-slate-400">{statistics.user_bookmarks_count} 书签</span>
              </>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StoneButton
            variant="secondary"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={() => { fetchPointers(); fetchStatistics(); }}
            disabled={loading}
          >
            刷新
          </StoneButton>
        </div>
      </div>

      {/* 视图切换 + 搜索过滤 */}
      <HUDPanel color="purple" className="mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* 视图切换 */}
          <div className="flex items-center gap-1 p-1 bg-slate-800/50 rounded-lg border border-slate-700/50">
            <button
              onClick={() => { setViewMode('all'); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                viewMode === 'all'
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Database className="w-4 h-4 inline mr-1" />
              全部
            </button>
            <button
              onClick={() => { setViewMode('favorites'); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                viewMode === 'favorites'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Star className="w-4 h-4 inline mr-1" />
              收藏
            </button>
            <button
              onClick={() => { setViewMode('bookmarks'); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                viewMode === 'bookmarks'
                  ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Bookmark className="w-4 h-4 inline mr-1" />
              书签
            </button>
          </div>

          {/* 搜索 */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索标题..."
                className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 transition-colors"
              />
            </div>
          </div>

          {/* 平台过滤 */}
          {viewMode === 'all' && (
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <select
                value={selectedDomain}
                onChange={(e) => {
                  setSelectedDomain(e.target.value)
                  setPage(1)
                }}
                className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500/50 transition-colors"
              >
                <option value="">全部平台</option>
                {domains.map((d) => (
                  <option key={d.domain} value={d.domain}>
                    {d.domain} ({d.count})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </HUDPanel>

      {/* 管理员批量操作栏 */}
      {isAdmin && viewMode === 'all' && (
        <div className="mb-4 p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleSelectAll}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
            >
              {selectedIds.size === pointers.length && pointers.length > 0 ? (
                <CheckSquare className="w-4 h-4 text-cyan-400" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              {selectedIds.size === pointers.length && pointers.length > 0 ? '取消全选' : '全选'}
            </button>
            <span className="text-xs text-slate-500">
              已选择 <span className="text-cyan-400 font-mono">{selectedIds.size}</span> 项
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StoneButton
              size="sm"
              variant="secondary"
              icon={<Shield className="w-4 h-4" />}
              onClick={() => setShowVisibilityModal(true)}
              disabled={selectedIds.size === 0}
            >
              批量设置可见性
            </StoneButton>
          </div>
        </div>
      )}

      {/* 数据列表 */}
      <HUDPanel
        title={viewMode === 'all' ? '数据列表' : viewMode === 'favorites' ? '我的收藏' : '我的书签'}
        subtitle="统一数据视图"
        color="cyan"
      >
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
          </div>
        ) : pointers.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">
              {viewMode === 'favorites' ? '暂无收藏数据' :
               viewMode === 'bookmarks' ? '暂无书签数据' : '暂无数据'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {pointers.map((pointer, index) => (
              <div
                key={pointer.id}
                className={`p-4 rounded-lg bg-slate-800/30 border transition-all cursor-pointer ${
                  selectedIds.has(pointer.id)
                    ? 'border-cyan-500/50 bg-cyan-500/5'
                    : 'border-slate-700/50 hover:border-cyan-500/30'
                }`}
                onClick={() => handleViewDetail(pointer)}
                style={{
                  animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both`,
                }}
              >
                <div className="flex items-start justify-between gap-4">
                  {/* 管理员选择框 */}
                  {isAdmin && viewMode === 'all' && (
                    <button
                      onClick={(e) => handleToggleSelect(pointer.id, e)}
                      className="p-1 flex-shrink-0 mt-0.5"
                    >
                      {selectedIds.has(pointer.id) ? (
                        <CheckSquare className="w-5 h-5 text-cyan-400" />
                      ) : (
                        <Square className="w-5 h-5 text-slate-500 hover:text-slate-300" />
                      )}
                    </button>
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-slate-200 font-medium truncate mb-2 hover:text-cyan-400 transition-colors">
                      {pointer.title || '(无标题)'}
                    </h3>
                    <div className="flex items-center gap-3 text-xs flex-wrap">
                      {/* 平台标签 */}
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                        {platformIcons[pointer.domain] || <Database className="w-3 h-3" />}
                        {pointer.domain}
                      </span>
                      {/* 可见性 - 管理员可点击更改 */}
                      {isAdmin ? (
                        <div className="relative group">
                          <button
                            onClick={(e) => e.stopPropagation()}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${visibilityColors[pointer.visibility]} hover:opacity-80 transition-opacity`}
                          >
                            {visibilityIcons[pointer.visibility]}
                            {visibilityLabels[pointer.visibility]}
                          </button>
                          <div className="absolute left-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                            {(['private', 'tenant_shared', 'public'] as DataVisibility[]).map((v) => (
                              <button
                                key={v}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleUpdateVisibility(pointer.id, v)
                                }}
                                className={`flex items-center gap-2 w-full px-3 py-2 text-xs hover:bg-slate-700/50 first:rounded-t-lg last:rounded-b-lg ${
                                  pointer.visibility === v ? 'text-cyan-400' : 'text-slate-400'
                                }`}
                              >
                                {visibilityIcons[v]}
                                {visibilityLabels[v]}
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${visibilityColors[pointer.visibility]}`}>
                          {visibilityIcons[pointer.visibility]}
                          {visibilityLabels[pointer.visibility]}
                        </span>
                      )}
                      {/* 内容/分析状态 */}
                      {pointer.has_content && (
                        <span className="inline-flex items-center gap-1 text-emerald-400">
                          <FileText className="w-3 h-3" />
                          正文
                        </span>
                      )}
                      {pointer.has_analysis && (
                        <span className="inline-flex items-center gap-1 text-blue-400">
                          <Activity className="w-3 h-3" />
                          分析
                        </span>
                      )}
                      {/* 时间 */}
                      <span className="inline-flex items-center gap-1 text-slate-500">
                        <Calendar className="w-3 h-3" />
                        {formatDate(pointer.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={(e) => handleToggleFavorite(pointer.id, e)}
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="收藏"
                    >
                      <Star className="w-4 h-4 text-slate-500 hover:text-amber-400" />
                    </button>
                    <button
                      onClick={(e) => handleToggleBookmark(pointer.id, e)}
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="书签"
                    >
                      <Bookmark className="w-4 h-4 text-slate-500 hover:text-purple-400" />
                    </button>
                    {pointer.url && (
                      <a
                        href={pointer.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="打开原文"
                      >
                        <ExternalLink className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {totalPages > 0 && (
          <div className="flex flex-wrap items-center justify-between mt-6 pt-4 border-t border-slate-700/50 gap-4">
            {/* 左侧：分页信息和每页数量选择 */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-500 font-mono">
                <span className="text-cyan-400">{(page - 1) * pageSize + 1}</span>-<span className="text-cyan-400">{Math.min(page * pageSize, total)}</span> / {total.toLocaleString()}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">每页</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value))
                    setPage(1)
                  }}
                  className="bg-slate-800/50 border border-slate-700/50 rounded px-2 py-1 text-sm text-slate-300 focus:outline-none focus:border-cyan-500/50"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>

            {/* 中间：分页按钮 */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(1)}
                disabled={page === 1}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="首页"
              >
                <ChevronsLeft className="w-4 h-4 text-slate-400" />
              </button>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="上一页"
              >
                <ChevronLeft className="w-4 h-4 text-slate-400" />
              </button>

              <div className="flex items-center gap-1">
                {(() => {
                  const pages: (number | string)[] = []
                  const showPages = 7

                  if (totalPages <= showPages) {
                    for (let i = 1; i <= totalPages; i++) {
                      pages.push(i)
                    }
                  } else {
                    if (page <= 4) {
                      for (let i = 1; i <= 5; i++) pages.push(i)
                      pages.push('...')
                      pages.push(totalPages)
                    } else if (page >= totalPages - 3) {
                      pages.push(1)
                      pages.push('...')
                      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
                    } else {
                      pages.push(1)
                      pages.push('...')
                      for (let i = page - 1; i <= page + 1; i++) pages.push(i)
                      pages.push('...')
                      pages.push(totalPages)
                    }
                  }

                  return pages.map((p, idx) =>
                    p === '...' ? (
                      <span key={`ellipsis-${idx}`} className="px-2 text-slate-500">...</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => setPage(p as number)}
                        className={`min-w-[32px] h-8 px-2 rounded-lg text-sm transition-all ${
                          p === page
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                            : 'hover:bg-slate-700/50 text-slate-400'
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )
                })()}
              </div>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="下一页"
              >
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
              <button
                onClick={() => setPage(totalPages)}
                disabled={page === totalPages}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="末页"
              >
                <ChevronsRight className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            {/* 右侧：跳转 */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">跳至</span>
              <input
                type="text"
                value={jumpPage}
                onChange={(e) => setJumpPage(e.target.value.replace(/\D/g, ''))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const targetPage = parseInt(jumpPage)
                    if (targetPage >= 1 && targetPage <= totalPages) {
                      setPage(targetPage)
                      setJumpPage('')
                    }
                  }
                }}
                placeholder={String(page)}
                className="w-14 bg-slate-800/50 border border-slate-700/50 rounded px-2 py-1 text-sm text-slate-300 text-center focus:outline-none focus:border-cyan-500/50"
              />
              <span className="text-xs text-slate-500">页</span>
              <button
                onClick={() => {
                  const targetPage = parseInt(jumpPage)
                  if (targetPage >= 1 && targetPage <= totalPages) {
                    setPage(targetPage)
                    setJumpPage('')
                  }
                }}
                className="px-3 py-1 text-xs bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded transition-colors"
              >
                GO
              </button>
            </div>
          </div>
        )}
      </HUDPanel>

      {/* 详情模态框 */}
      {selectedPointer && createPortal(
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999]"
            onClick={() => setSelectedPointer(null)}
          />
          <div
            className="fixed z-[10000]"
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '90vw',
              maxWidth: '768px',
              maxHeight: '80vh',
            }}
          >
            <div className="relative overflow-hidden rounded-xl bg-slate-900/95 backdrop-blur-sm border border-cyan-500/30 shadow-[0_0_30px_rgba(6,182,212,0.2)] max-h-[80vh] flex flex-col">
              {/* 角落装饰 */}
              <div className="absolute top-0 left-0 w-6 h-6 border-l-2 border-t-2 border-cyan-500/30" />
              <div className="absolute top-0 right-0 w-6 h-6 border-r-2 border-t-2 border-cyan-500/30" />
              <div className="absolute bottom-0 left-0 w-6 h-6 border-l-2 border-b-2 border-cyan-500/30" />
              <div className="absolute bottom-0 right-0 w-6 h-6 border-r-2 border-b-2 border-cyan-500/30" />

              <div className="p-6 border-b border-slate-700/50 flex items-start justify-between gap-4 flex-shrink-0">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">
                    {selectedPointer.title || '(无标题)'}
                  </h3>
                  <div className="flex items-center gap-3 text-xs flex-wrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                      {platformIcons[selectedPointer.domain] || <Database className="w-3 h-3" />}
                      {selectedPointer.domain}
                    </span>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${visibilityColors[selectedPointer.visibility]}`}>
                      {visibilityIcons[selectedPointer.visibility]}
                      {visibilityLabels[selectedPointer.visibility]}
                    </span>
                    <span className="inline-flex items-center gap-1 text-slate-500">
                      <Calendar className="w-3 h-3" />
                      {formatDate(selectedPointer.created_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedPointer(null)}
                  className="p-2 hover:bg-slate-700/50 rounded-lg flex-shrink-0 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {detailLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                  </div>
                ) : selectedPointer.content?.content_text ? (
                  <div>
                    {selectedPointer.content.summary && (
                      <div className="mb-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">
                        <h4 className="text-sm font-medium text-slate-400 mb-2">摘要</h4>
                        <p className="text-slate-300">{selectedPointer.content.summary}</p>
                      </div>
                    )}
                    <div
                      className="text-slate-300 leading-relaxed prose prose-invert max-w-none [&_img]:max-w-full [&_img]:h-auto [&_img]:rounded-lg [&_img]:my-4"
                      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(selectedPointer.content.content_text) }}
                    />
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 mb-4">暂无正文内容</p>
                    {selectedPointer.url && (
                      <a
                        href={selectedPointer.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        查看原文
                      </a>
                    )}
                  </div>
                )}

                {/* 分析结果 */}
                {selectedPointer.analyses && selectedPointer.analyses.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-slate-700/50">
                    <h4 className="text-sm font-medium text-slate-400 mb-4">分析结果</h4>
                    <div className="space-y-3">
                      {selectedPointer.analyses.map((analysis) => (
                        <div
                          key={analysis.id}
                          className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-cyan-400">
                              {analysis.analysis_type}
                            </span>
                            {analysis.confidence && (
                              <span className="text-xs text-slate-500">
                                置信度: {(analysis.confidence * 100).toFixed(1)}%
                              </span>
                            )}
                          </div>
                          <pre className="text-xs text-slate-400 overflow-x-auto">
                            {JSON.stringify(analysis.result, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-slate-700/50 flex justify-end gap-3 flex-shrink-0 bg-slate-800/50">
                {selectedPointer.url && (
                  <a href={selectedPointer.url} target="_blank" rel="noopener noreferrer">
                    <StoneButton variant="secondary" icon={<ExternalLink className="w-4 h-4" />}>
                      查看原文
                    </StoneButton>
                  </a>
                )}
                <StoneButton variant="secondary" onClick={() => setSelectedPointer(null)}>
                  关闭
                </StoneButton>
              </div>
            </div>
          </div>
        </>,
        document.body
      )}

      {/* 批量可见性设置模态框 */}
      <StoneModal
        open={showVisibilityModal}
        onClose={() => setShowVisibilityModal(false)}
        title="批量设置可见性"
        width="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-400">
            已选择 <span className="text-cyan-400 font-mono">{selectedIds.size}</span> 条数据
          </p>
          <div className="space-y-2">
            {(['private', 'tenant_shared', 'public'] as DataVisibility[]).map((v) => (
              <button
                key={v}
                onClick={() => setTargetVisibility(v)}
                className={`flex items-center gap-3 w-full p-3 rounded-lg border transition-all ${
                  targetVisibility === v
                    ? 'border-cyan-500/50 bg-cyan-500/10'
                    : 'border-slate-700/50 hover:border-slate-600'
                }`}
              >
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${visibilityColors[v]}`}>
                  {visibilityIcons[v]}
                </span>
                <div className="text-left">
                  <p className="text-sm text-slate-200">{visibilityLabels[v]}</p>
                  <p className="text-xs text-slate-500">
                    {v === 'private' && '仅自己可见'}
                    {v === 'tenant_shared' && '团队成员可见'}
                    {v === 'public' && '所有用户可见'}
                  </p>
                </div>
              </button>
            ))}
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/50">
            <StoneButton variant="secondary" onClick={() => setShowVisibilityModal(false)}>
              取消
            </StoneButton>
            <StoneButton onClick={handleBatchUpdateVisibility} loading={updatingVisibility}>
              确认更新
            </StoneButton>
          </div>
        </div>
      </StoneModal>

      {/* 动画样式 */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
