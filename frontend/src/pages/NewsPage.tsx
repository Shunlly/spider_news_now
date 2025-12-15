/**
 * 新闻管理页面
 * News Management Page
 */

import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { GlassCard, GlassButton, GlassInput } from '@/components/glass'
import {
  IconSearch,
  IconRefresh,
  IconDownload,
  IconFilter,
  IconLeft,
  IconRight,
  IconLink,
  IconCalendar,
  IconClose,
  IconFile,
  IconDoubleLeft,
  IconDoubleRight,
} from '@arco-design/web-react/icon'
import {
  newsService,
  scraperService,
  exportsService,
  type NewsArticle,
  type NewsListResponse,
  type NewsSource,
  type ExportFormat,
} from '@/services'

export default function NewsPage() {
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
  const [exportTasks, setExportTasks] = useState<any[]>([])
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
      alert('下载失败，请重试')
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
        // 3秒后关闭模态框
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
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">新闻管理</h1>
          <p className="text-white/60 mt-1">
            共 {total.toLocaleString()} 篇文章
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton
            icon={<IconRefresh />}
            onClick={fetchArticles}
            disabled={loading}
          >
            刷新
          </GlassButton>
          <GlassButton icon={<IconDownload />} onClick={() => setShowExportModal(true)}>导出</GlassButton>
        </div>
      </div>

      {/* 搜索和过滤 */}
      <GlassCard className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <GlassInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索文章标题..."
              prefix={<IconSearch />}
            />
          </div>
          <div className="flex items-center gap-2">
            <IconFilter className="text-white/60" />
            <select
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value)
                setPage(1)
              }}
              className="bg-slate-800 border border-white/20 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-white/40"
            >
              <option value="" className="bg-slate-800 text-white">全部来源</option>
              {sources.map((source) => (
                <option key={source.source_key} value={source.source_key} className="bg-slate-800 text-white">
                  {source.display_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </GlassCard>

      {/* 文章列表 */}
      <GlassCard className="overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-white/60">暂无文章数据</p>
          </div>
        ) : (
          <div className="divide-y divide-white/10">
            {articles.map((article) => (
              <div
                key={article.id}
                className="p-4 hover:bg-white/5 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-white font-medium truncate mb-2 cursor-pointer hover:text-indigo-400 transition-colors"
                      onClick={() => handleViewArticle(article)}
                    >
                      {article.title}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-white/50">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-white/10 rounded">
                        {article.source_key}
                      </span>
                      {article.category && (
                        <span className="text-white/40">{article.category}</span>
                      )}
                      <span className="inline-flex items-center gap-1">
                        <IconCalendar className="text-xs" />
                        {formatDate(article.published_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleViewArticle(article)}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                      title="查看正文"
                    >
                      <IconFile className="text-white/60" />
                    </button>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                      title="打开原文"
                    >
                      <IconLink className="text-white/60" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {totalPages > 0 && (
          <div className="flex flex-wrap items-center justify-between px-4 py-3 border-t border-white/10 gap-4">
            {/* 左侧：分页信息和每页数量选择 */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-white/50">
                共 {total.toLocaleString()} 条，第 {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} 条
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-white/50">每页</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value))
                    setPage(1)
                  }}
                  className="bg-slate-800 border border-white/20 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-white/40"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <span className="text-sm text-white/50">条</span>
              </div>
            </div>

            {/* 中间：分页按钮 */}
            <div className="flex items-center gap-1">
              {/* 首页 */}
              <button
                onClick={() => setPage(1)}
                disabled={page === 1}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="首页"
              >
                <IconDoubleLeft className="text-white" />
              </button>
              {/* 上一页 */}
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="上一页"
              >
                <IconLeft className="text-white" />
              </button>

              {/* 页码按钮 */}
              <div className="flex items-center gap-1">
                {(() => {
                  const pages: (number | string)[] = []
                  const showPages = 7 // 显示的页码数量

                  if (totalPages <= showPages) {
                    // 总页数小于等于显示数量，全部显示
                    for (let i = 1; i <= totalPages; i++) {
                      pages.push(i)
                    }
                  } else {
                    // 总页数大于显示数量，智能显示
                    if (page <= 4) {
                      // 当前页靠近开头
                      for (let i = 1; i <= 5; i++) pages.push(i)
                      pages.push('...')
                      pages.push(totalPages)
                    } else if (page >= totalPages - 3) {
                      // 当前页靠近结尾
                      pages.push(1)
                      pages.push('...')
                      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
                    } else {
                      // 当前页在中间
                      pages.push(1)
                      pages.push('...')
                      for (let i = page - 1; i <= page + 1; i++) pages.push(i)
                      pages.push('...')
                      pages.push(totalPages)
                    }
                  }

                  return pages.map((p, idx) =>
                    p === '...' ? (
                      <span key={`ellipsis-${idx}`} className="px-2 text-white/40">...</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => setPage(p as number)}
                        className={`min-w-[32px] h-8 px-2 rounded-lg text-sm transition-colors ${
                          p === page
                            ? 'bg-indigo-500/80 text-white font-medium'
                            : 'hover:bg-white/10 text-white/60'
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )
                })()}
              </div>

              {/* 下一页 */}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="下一页"
              >
                <IconRight className="text-white" />
              </button>
              {/* 末页 */}
              <button
                onClick={() => setPage(totalPages)}
                disabled={page === totalPages}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="末页"
              >
                <IconDoubleRight className="text-white" />
              </button>
            </div>

            {/* 右侧：跳转 */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-white/50">跳至</span>
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
                className="w-16 bg-slate-800 border border-white/20 rounded px-2 py-1 text-white text-sm text-center focus:outline-none focus:border-white/40"
              />
              <span className="text-sm text-white/50">页</span>
              <button
                onClick={() => {
                  const targetPage = parseInt(jumpPage)
                  if (targetPage >= 1 && targetPage <= totalPages) {
                    setPage(targetPage)
                    setJumpPage('')
                  }
                }}
                className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm text-white transition-colors"
              >
                确定
              </button>
            </div>
          </div>
        )}
      </GlassCard>

      {/* 导出模态框 */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <GlassCard className="w-full max-w-lg p-6 max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">导出新闻数据</h3>
              <button
                onClick={() => setShowExportModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg"
              >
                <IconClose className="text-white/60" />
              </button>
            </div>
            <div className="space-y-4 flex-1 overflow-y-auto">
              <div>
                <label className="block text-sm text-white/60 mb-2">导出格式</label>
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                  className="w-full bg-slate-800 border border-white/20 rounded-lg px-3 py-2 text-white"
                >
                  <option value="CSV" className="bg-slate-800 text-white">CSV</option>
                  <option value="JSON" className="bg-slate-800 text-white">JSON</option>
                  <option value="EXCEL" className="bg-slate-800 text-white">Excel</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">数据范围</label>
                <p className="text-sm text-white/40">
                  {selectedSource ? `来源: ${selectedSource}` : '全部来源'}，共 {total.toLocaleString()} 篇文章
                </p>
              </div>
              {exportMessage && (
                <p className={`text-sm ${exportMessage.includes('失败') ? 'text-red-400' : 'text-green-400'}`}>
                  {exportMessage}
                </p>
              )}
              <div className="flex justify-end gap-3">
                <GlassButton onClick={() => setShowExportModal(false)}>取消</GlassButton>
                <GlassButton
                  variant="primary"
                  onClick={handleExport}
                  loading={exporting}
                >
                  创建导出任务
                </GlassButton>
              </div>

              {/* 导出任务列表 */}
              <div className="border-t border-white/10 pt-4 mt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-white">历史导出任务</h4>
                  <button
                    onClick={fetchExportTasks}
                    className="text-xs text-white/50 hover:text-white/80"
                    disabled={loadingTasks}
                  >
                    {loadingTasks ? '加载中...' : '刷新'}
                  </button>
                </div>
                {loadingTasks ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  </div>
                ) : exportTasks.length === 0 ? (
                  <p className="text-sm text-white/40 text-center py-4">暂无导出任务</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {exportTasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                      >
                        <div className="flex-1 min-w-0 mr-3">
                          <p className="text-sm text-white truncate">{task.filename}</p>
                          <div className="flex items-center gap-2 text-xs text-white/50">
                            <span className={`px-1.5 py-0.5 rounded ${
                              task.status.toUpperCase() === 'COMPLETED' ? 'bg-green-500/20 text-green-400' :
                              task.status.toUpperCase() === 'FAILED' ? 'bg-red-500/20 text-red-400' :
                              task.status.toUpperCase() === 'PROCESSING' ? 'bg-blue-500/20 text-blue-400' :
                              'bg-yellow-500/20 text-yellow-400'
                            }`}>
                              {task.status.toUpperCase() === 'COMPLETED' ? '已完成' :
                               task.status.toUpperCase() === 'FAILED' ? '失败' :
                               task.status.toUpperCase() === 'PROCESSING' ? '处理中' : '等待中'}
                            </span>
                            {task.exported_records && (
                              <span>{task.exported_records} 条记录</span>
                            )}
                          </div>
                        </div>
                        {task.status.toUpperCase() === 'COMPLETED' && (
                          <GlassButton
                            size="sm"
                            icon={<IconDownload />}
                            onClick={() => handleDownload(task.id, task.filename)}
                          >
                            下载
                          </GlassButton>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* 文章详情模态框 - 使用 Portal 渲染到 body */}
      {selectedArticle && createPortal(
        <>
          {/* 遮罩层 */}
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999]"
            onClick={() => setSelectedArticle(null)}
            style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
          />
          {/* 模态框 - 视口居中 */}
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
            <GlassCard className="w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-white/10 flex items-start justify-between gap-4 flex-shrink-0">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-white mb-2">{selectedArticle.title}</h3>
                  <div className="flex items-center gap-4 text-sm text-white/50 flex-wrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-white/10 rounded">
                      {selectedArticle.source_key}
                    </span>
                    {selectedArticle.category && (
                      <span className="text-white/40">{selectedArticle.category}</span>
                    )}
                    <span className="inline-flex items-center gap-1">
                      <IconCalendar className="text-xs" />
                      {formatDate(selectedArticle.published_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedArticle(null)}
                  className="p-2 hover:bg-white/10 rounded-lg flex-shrink-0"
                >
                  <IconClose className="text-white/60" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {articleLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                  </div>
                ) : selectedArticle.content_text ? (
                  <div
                    className="text-white/80 leading-relaxed prose prose-invert max-w-none [&_img]:max-w-full [&_img]:h-auto [&_img]:rounded-lg [&_img]:my-4"
                    dangerouslySetInnerHTML={{ __html: selectedArticle.content_text }}
                  />
                ) : (
                  <div className="text-center py-12">
                    <p className="text-white/60 mb-4">暂无正文内容</p>
                    <a
                      href={selectedArticle.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      <IconLink />
                      查看原文
                    </a>
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-white/10 flex justify-end gap-3 flex-shrink-0">
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <GlassButton icon={<IconLink />}>查看原文</GlassButton>
                </a>
                <GlassButton onClick={() => setSelectedArticle(null)}>关闭</GlassButton>
              </div>
            </GlassCard>
          </div>
        </>,
        document.body
      )}
    </div>
  )
}
