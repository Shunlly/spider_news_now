/**
 * HUD 风格新闻管理页面
 * HUD-style News Management Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import DOMPurify from 'dompurify'
import { HUDPanel, StoneButton, StoneSelect, StoneModal, useToast } from '@/components/ui'
import {
  Search,
  RefreshCw,
  Download,
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
} from 'lucide-react'
import {
  newsService,
  scraperService,
  exportsService,
  type NewsArticle,
  type NewsListResponse,
  type NewsSource,
  type ExportFormat,
  type ExportTask,
} from '@/services'

export default function NewsPage() {
  const toast = useToast()
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [jumpPage, setJumpPage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedSource, setSelectedSource] = useState('')
  const [sources, setSources] = useState<NewsSource[]>([])

  // 导出状态
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('CSV')
  const [exporting, setExporting] = useState(false)
  const [exportMessage, setExportMessage] = useState('')
  const [exportTasks, setExportTasks] = useState<ExportTask[]>([])
  const [loadingTasks, setLoadingTasks] = useState(false)

  // 文章详情状态
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null)
  const [articleLoading, setArticleLoading] = useState(false)

  const fetchArticles = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      }
      if (selectedSource) params.source = selectedSource
      if (debouncedSearch.trim()) params.search = debouncedSearch.trim()

      const response: NewsListResponse = await newsService.getArticles(params)
      setArticles(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('Failed to fetch articles:', error)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, selectedSource, debouncedSearch])

  const fetchSources = async () => {
    try {
      const response = await scraperService.getSources()
      setSources(response.sources || [])
    } catch (error) {
      console.error('Failed to fetch sources:', error)
    }
  }

  // 获取导出任务列表
  const fetchExportTasks = async () => {
    setLoadingTasks(true)
    try {
      const response = await exportsService.getExportTasks({ limit: 10 })
      setExportTasks(response.data || [])
    } catch (error) {
      console.error('Failed to fetch export tasks:', error)
    } finally {
      setLoadingTasks(false)
    }
  }

  // 下载导出文件
  const handleDownload = async (taskId: number, filename: string) => {
    try {
      const blob = await exportsService.downloadExport(taskId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download:', error)
      toast.error('下载失败，请重试')
    }
  }

  useEffect(() => {
    fetchArticles()
  }, [fetchArticles])

  useEffect(() => {
    fetchSources()
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

  // 打开导出模态框时获取任务列表
  useEffect(() => {
    if (showExportModal) {
      fetchExportTasks()
    }
  }, [showExportModal])

  // 导出处理
  const handleExport = async () => {
    setExporting(true)
    setExportMessage('')
    try {
      const filters: Record<string, string> = {}
      if (selectedSource) filters.source_key = selectedSource

      const response = await exportsService.createExport({
        data_source: 'news',
        export_format: exportFormat,
        filters,
      })

      if (response.success) {
        setExportMessage('导出任务已创建，正在后台处理...')
        setTimeout(() => {
          setShowExportModal(false)
          setExportMessage('')
        }, 3000)
      } else {
        setExportMessage(response.message || '导出失败')
      }
    } catch (error) {
      console.error('Failed to export:', error)
      setExportMessage('导出请求失败，请重试')
    } finally {
      setExporting(false)
    }
  }

  // 查看文章详情
  const handleViewArticle = async (article: NewsArticle) => {
    setSelectedArticle(article)
    setArticleLoading(true)
    try {
      const detail = await newsService.getArticle(article.id)
      setSelectedArticle(detail)
    } catch (error) {
      console.error('Failed to fetch article detail:', error)
    } finally {
      setArticleLoading(false)
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">新闻管理</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>共 <span className="text-cyan-400 font-mono">{total.toLocaleString()}</span> 篇文章</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StoneButton
            variant="secondary"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={fetchArticles}
            disabled={loading}
          >
            刷新
          </StoneButton>
          <StoneButton icon={<Download className="w-4 h-4" />} onClick={() => setShowExportModal(true)}>导出</StoneButton>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <HUDPanel color="purple" className="mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索文章标题..."
                className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 transition-colors"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value)
                setPage(1)
              }}
              className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500/50 transition-colors"
            >
              <option value="">全部来源</option>
              {sources.map((source) => (
                <option key={source.source_key} value={source.source_key}>
                  {source.display_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </HUDPanel>

      {/* 文章列表 */}
      <HUDPanel title="文章列表" subtitle="实时数据" color="cyan">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">暂无文章数据</p>
          </div>
        ) : (
          <div className="space-y-2">
            {articles.map((article, index) => (
              <div
                key={article.id}
                className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
                style={{
                  animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both`,
                }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-slate-200 font-medium truncate mb-2 cursor-pointer hover:text-cyan-400 transition-colors"
                      onClick={() => handleViewArticle(article)}
                    >
                      {article.title}
                    </h3>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                        {article.source_key}
                      </span>
                      {article.category && (
                        <span className="text-slate-500">{article.category}</span>
                      )}
                      <span className="inline-flex items-center gap-1 text-slate-500">
                        <Calendar className="w-3 h-3" />
                        {formatDate(article.published_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => handleViewArticle(article)}
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="查看正文"
                    >
                      <FileText className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                    </button>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="打开原文"
                    >
                      <ExternalLink className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                    </a>
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

      {/* 导出模态框 */}
      <StoneModal
        open={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="导出新闻数据"
        width="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">导出格式</label>
            <StoneSelect
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="w-full"
            >
              <option value="CSV">CSV</option>
              <option value="JSON">JSON</option>
              <option value="EXCEL">Excel</option>
            </StoneSelect>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">数据范围</label>
            <p className="text-sm text-slate-500">
              {selectedSource ? `来源: ${selectedSource}` : '全部来源'}，共 {total.toLocaleString()} 篇文章
            </p>
          </div>
          {exportMessage && (
            <p className={`text-sm ${exportMessage.includes('失败') ? 'text-red-400' : 'text-emerald-400'}`}>
              {exportMessage}
            </p>
          )}
          <div className="flex justify-end gap-3">
            <StoneButton variant="secondary" onClick={() => setShowExportModal(false)}>取消</StoneButton>
            <StoneButton onClick={handleExport} loading={exporting}>创建导出任务</StoneButton>
          </div>

          {/* 导出任务列表 */}
          <div className="border-t border-slate-700 pt-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-slate-300">历史导出任务</h4>
              <button
                onClick={fetchExportTasks}
                className="text-xs text-slate-500 hover:text-cyan-400 transition-colors"
                disabled={loadingTasks}
              >
                {loadingTasks ? '加载中...' : '刷新'}
              </button>
            </div>
            {loadingTasks ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-cyan-400"></div>
              </div>
            ) : exportTasks.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">暂无导出任务</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {exportTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex-1 min-w-0 mr-3">
                      <p className="text-sm text-slate-300 truncate">{task.filename}</p>
                      <div className="flex items-center gap-2 text-xs">
                        <span className={`px-1.5 py-0.5 rounded ${
                          task.status.toUpperCase() === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                          task.status.toUpperCase() === 'FAILED' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          task.status.toUpperCase() === 'PROCESSING' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                          'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        }`}>
                          {task.status.toUpperCase() === 'COMPLETED' ? '已完成' :
                           task.status.toUpperCase() === 'FAILED' ? '失败' :
                           task.status.toUpperCase() === 'PROCESSING' ? '处理中' : '等待中'}
                        </span>
                        {task.exported_records && (
                          <span className="text-slate-500">{task.exported_records} 条记录</span>
                        )}
                      </div>
                    </div>
                    {task.status.toUpperCase() === 'COMPLETED' && (
                      <StoneButton
                        size="sm"
                        variant="secondary"
                        icon={<Download className="w-3 h-3" />}
                        onClick={() => handleDownload(task.id, task.filename)}
                      >
                        下载
                      </StoneButton>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </StoneModal>

      {/* 文章详情模态框 - HUD 风格 */}
      {selectedArticle && createPortal(
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999]"
            onClick={() => setSelectedArticle(null)}
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
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">{selectedArticle.title}</h3>
                  <div className="flex items-center gap-4 text-xs flex-wrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                      {selectedArticle.source_key}
                    </span>
                    {selectedArticle.category && (
                      <span className="text-slate-500">{selectedArticle.category}</span>
                    )}
                    <span className="inline-flex items-center gap-1 text-slate-500">
                      <Calendar className="w-3 h-3" />
                      {formatDate(selectedArticle.published_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedArticle(null)}
                  className="p-2 hover:bg-slate-700/50 rounded-lg flex-shrink-0 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {articleLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                  </div>
                ) : selectedArticle.content_text ? (
                  <div
                    className="text-slate-300 leading-relaxed prose prose-invert max-w-none [&_img]:max-w-full [&_img]:h-auto [&_img]:rounded-lg [&_img]:my-4"
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(selectedArticle.content_text) }}
                  />
                ) : (
                  <div className="text-center py-12">
                    <p className="text-slate-500 mb-4">暂无正文内容</p>
                    <a
                      href={selectedArticle.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                      查看原文
                    </a>
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-slate-700/50 flex justify-end gap-3 flex-shrink-0 bg-slate-800/50">
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <StoneButton variant="secondary" icon={<ExternalLink className="w-4 h-4" />}>查看原文</StoneButton>
                </a>
                <StoneButton variant="secondary" onClick={() => setSelectedArticle(null)}>关闭</StoneButton>
              </div>
            </div>
          </div>
        </>,
        document.body
      )}

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
