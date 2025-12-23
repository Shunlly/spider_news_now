/**
 * HUD 风格全文搜索页面
 * HUD-style Full-Text Search Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useCallback } from 'react'
import DOMPurify from 'dompurify'
import { HUDPanel, StoneButton } from '@/components/ui'
import {
  Search,
  Filter,
  Calendar,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  X,
  Activity,
  Zap,
  Database,
} from 'lucide-react'
import { searchService, type SearchHit, type SearchResponse } from '@/services'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchHit[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hitsPerPage] = useState(20)
  const [processingTimeMs, setProcessingTimeMs] = useState(0)

  // 过滤器
  const [showFilters, setShowFilters] = useState(false)
  const [sourceFilter, setSourceFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Facets
  const [facets, setFacets] = useState<{
    source_key?: Record<string, number>
    category?: Record<string, number>
  }>({})

  const handleSearch = useCallback(async (newPage = 1) => {
    if (!query.trim()) return

    setLoading(true)
    setPage(newPage)
    try {
      const response: SearchResponse = await searchService.search({
        q: query,
        page: newPage,
        hits_per_page: hitsPerPage,
        source_key: sourceFilter || undefined,
        category: categoryFilter || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      })
      setResults(response.hits)
      setTotal(response.total_hits)
      setProcessingTimeMs(response.processing_time_ms)
      setFacets(response.facets || {})
      setSearched(true)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }, [query, hitsPerPage, sourceFilter, categoryFilter, startDate, endDate])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(1)
    }
  }

  const clearFilters = () => {
    setSourceFilter('')
    setCategoryFilter('')
    setStartDate('')
    setEndDate('')
  }

  const hasActiveFilters = sourceFilter || categoryFilter || startDate || endDate

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  const totalPages = Math.ceil(total / hitsPerPage)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">全文搜索</h1>
        <p className="text-slate-500 mt-1 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>搜索所有采集的内容</span>
        </p>
      </div>

      {/* 搜索框 */}
      <HUDPanel color="purple" className="mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入搜索关键词..."
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg pl-12 pr-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 focus:shadow-[0_0_15px_rgba(168,85,247,0.2)] transition-all"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-3 rounded-lg border transition-all ${
              hasActiveFilters
                ? 'bg-purple-500/20 border-purple-500/50 text-purple-400'
                : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-purple-500/30'
            }`}
          >
            <Filter className="w-5 h-5" />
          </button>
          <StoneButton onClick={() => handleSearch(1)} disabled={loading || !query.trim()}>
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Zap className="w-4 h-4" />
            )}
            <span className="ml-2">搜索</span>
          </StoneButton>
        </div>

        {/* 过滤器面板 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-slate-400 uppercase tracking-wider">高级过滤</span>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
                >
                  <X className="w-3 h-3" />
                  清除过滤
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">来源</label>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
                >
                  <option value="">全部来源</option>
                  {Object.entries(facets.source_key || {}).map(([key, count]) => (
                    <option key={key} value={key}>
                      {key} ({count})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">分类</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
                >
                  <option value="">全部分类</option>
                  {Object.entries(facets.category || {}).map(([key, count]) => (
                    <option key={key} value={key}>
                      {key} ({count})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">开始日期</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">结束日期</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
                />
              </div>
            </div>
          </div>
        )}
      </HUDPanel>

      {/* 搜索结果 */}
      <HUDPanel title="搜索结果" color="cyan">
        {!searched ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="relative">
              <Search className="w-20 h-20 text-slate-700" />
              <div className="absolute inset-0 animate-ping">
                <Search className="w-20 h-20 text-cyan-500/20" />
              </div>
            </div>
            <p className="text-slate-400 mt-6">输入关键词开始搜索</p>
            <p className="text-slate-600 text-sm mt-2">
              支持中文分词、按来源/分类过滤、时间范围筛选
            </p>
          </div>
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
            <p className="text-slate-400 mt-4">搜索中...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Database className="w-16 h-16 text-slate-700" />
            <p className="text-slate-400 mt-4">未找到匹配的结果</p>
            <p className="text-slate-600 text-sm mt-2">
              尝试使用不同的关键词或调整过滤条件
            </p>
          </div>
        ) : (
          <>
            {/* 结果统计 */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-700/50">
              <span className="text-sm text-slate-400">
                找到 <span className="text-cyan-400 font-mono font-bold">{total.toLocaleString()}</span> 条结果
              </span>
              <span className="text-xs text-slate-600 font-mono">
                <Zap className="w-3 h-3 inline mr-1 text-yellow-400" />
                {processingTimeMs}ms
              </span>
            </div>

            {/* 结果列表 */}
            <div className="space-y-3">
              {results.map((hit, index) => (
                <div
                  key={hit.id}
                  className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
                  style={{
                    animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both`,
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-slate-200 font-medium mb-2">
                        {hit._formatted?.title ? (
                          <span
                            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(hit._formatted.title) }}
                            className="[&>em]:text-cyan-400 [&>em]:not-italic [&>em]:font-bold [&>em]:bg-cyan-500/20 [&>em]:px-0.5 [&>em]:rounded"
                          />
                        ) : (
                          hit.title
                        )}
                      </h3>
                      {hit._formatted?.content && (
                        <p className="text-sm text-slate-500 line-clamp-2 mb-3">
                          <span
                            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(hit._formatted.content) }}
                            className="[&>em]:text-cyan-400 [&>em]:not-italic [&>em]:font-bold [&>em]:bg-cyan-500/20 [&>em]:px-0.5 [&>em]:rounded"
                          />
                        </p>
                      )}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                          {hit.source_key}
                        </span>
                        {hit.category && (
                          <span className="text-slate-500">{hit.category}</span>
                        )}
                        {hit.published_at && (
                          <span className="inline-flex items-center gap-1 text-slate-600">
                            <Calendar className="w-3 h-3" />
                            {formatDate(hit.published_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    {hit.url && (
                      <a
                        href={hit.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-shrink-0 p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-700/50">
                <span className="text-sm text-slate-500 font-mono">
                  PAGE <span className="text-cyan-400">{page}</span> / {totalPages}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSearch(page - 1)}
                    disabled={page === 1}
                    className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 text-slate-400" />
                  </button>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const pageNum = Math.max(1, Math.min(page - 2, totalPages - 4)) + i
                      if (pageNum > totalPages) return null
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handleSearch(pageNum)}
                          className={`w-8 h-8 rounded-lg text-sm transition-all ${
                            pageNum === page
                              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                              : 'hover:bg-slate-700/50 text-slate-400'
                          }`}
                        >
                          {pageNum}
                        </button>
                      )
                    })}
                  </div>
                  <button
                    onClick={() => handleSearch(page + 1)}
                    disabled={page === totalPages}
                    className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </HUDPanel>

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
