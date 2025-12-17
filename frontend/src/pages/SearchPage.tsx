/**
 * 全文搜索页面
 * Full-Text Search Page
 *
 * Stone 色系极简设计
 */

import { useState, useCallback } from 'react'
import { StoneCard, StoneButton, StoneInput, StoneSelect } from '@/components/ui'
import {
  Search,
  Filter,
  Calendar,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  X,
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
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-stone-900">全文搜索</h1>
        <p className="text-stone-500 mt-1">搜索所有采集的内容</p>
      </div>

      {/* 搜索框 */}
      <StoneCard className="p-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <StoneInput
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入搜索关键词..."
              prefix={<Search className="w-4 h-4" />}
            />
          </div>
          <StoneButton
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
            className={hasActiveFilters ? 'ring-2 ring-stone-400' : ''}
          >
            <Filter className="w-4 h-4" />
            {hasActiveFilters && (
              <span className="ml-1 w-2 h-2 rounded-full bg-stone-600"></span>
            )}
          </StoneButton>
          <StoneButton onClick={() => handleSearch(1)} disabled={loading || !query.trim()}>
            {loading ? '搜索中...' : '搜索'}
          </StoneButton>
        </div>

        {/* 过滤器面板 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-stone-200">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-stone-500">高级过滤</span>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-stone-600 hover:text-stone-900 flex items-center gap-1"
                >
                  <X className="w-3 h-3" />
                  清除过滤
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs text-stone-400 mb-1">来源</label>
                <StoneSelect
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="w-full"
                >
                  <option value="">全部来源</option>
                  {Object.entries(facets.source_key || {}).map(([key, count]) => (
                    <option key={key} value={key}>
                      {key} ({count})
                    </option>
                  ))}
                </StoneSelect>
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1">分类</label>
                <StoneSelect
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full"
                >
                  <option value="">全部分类</option>
                  {Object.entries(facets.category || {}).map(([key, count]) => (
                    <option key={key} value={key}>
                      {key} ({count})
                    </option>
                  ))}
                </StoneSelect>
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1">开始日期</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-white border border-stone-200 rounded-xl px-3 py-2 text-stone-900 text-sm focus:outline-none focus:border-stone-400"
                />
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1">结束日期</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-white border border-stone-200 rounded-xl px-3 py-2 text-stone-900 text-sm focus:outline-none focus:border-stone-400"
                />
              </div>
            </div>
          </div>
        )}
      </StoneCard>

      {/* 搜索结果 */}
      <StoneCard className="overflow-hidden">
        {!searched ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Search className="w-16 h-16 text-stone-200 mb-4" />
            <p className="text-stone-500">输入关键词开始搜索</p>
            <p className="text-stone-400 text-sm mt-2">
              支持中文分词、按来源/分类过滤、时间范围筛选
            </p>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-stone-900"></div>
          </div>
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Search className="w-16 h-16 text-stone-200 mb-4" />
            <p className="text-stone-500">未找到匹配的结果</p>
            <p className="text-stone-400 text-sm mt-2">
              尝试使用不同的关键词或调整过滤条件
            </p>
          </div>
        ) : (
          <>
            {/* 结果统计 */}
            <div className="px-4 py-3 border-b border-stone-100 flex items-center justify-between">
              <span className="text-sm text-stone-500">
                找到 <span className="text-stone-900 font-medium">{total.toLocaleString()}</span> 条结果
              </span>
              <span className="text-xs text-stone-400">
                耗时 {processingTimeMs}ms
              </span>
            </div>

            {/* 结果列表 */}
            <div className="divide-y divide-stone-100">
              {results.map((hit) => (
                <div key={hit.id} className="p-4 hover:bg-stone-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-stone-900 font-medium mb-2">
                        {hit._formatted?.title ? (
                          <span
                            dangerouslySetInnerHTML={{ __html: hit._formatted.title }}
                            className="[&>em]:text-stone-600 [&>em]:not-italic [&>em]:font-bold [&>em]:bg-yellow-100"
                          />
                        ) : (
                          hit.title
                        )}
                      </h3>
                      {hit._formatted?.content && (
                        <p className="text-sm text-stone-500 line-clamp-2 mb-2">
                          <span
                            dangerouslySetInnerHTML={{ __html: hit._formatted.content }}
                            className="[&>em]:text-stone-700 [&>em]:not-italic [&>em]:font-bold [&>em]:bg-yellow-100"
                          />
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-stone-400">
                        <span className="px-2 py-0.5 bg-stone-100 rounded">
                          {hit.source_key}
                        </span>
                        {hit.category && (
                          <span className="text-stone-400">{hit.category}</span>
                        )}
                        {hit.published_at && (
                          <span className="inline-flex items-center gap-1">
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
                        className="flex-shrink-0 p-2 hover:bg-stone-100 rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-4 h-4 text-stone-500" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-stone-100">
                <span className="text-sm text-stone-500">
                  第 {page} / {totalPages} 页
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSearch(page - 1)}
                    disabled={page === 1}
                    className="p-2 hover:bg-stone-100 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 text-stone-700" />
                  </button>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const pageNum = Math.max(1, Math.min(page - 2, totalPages - 4)) + i
                      if (pageNum > totalPages) return null
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handleSearch(pageNum)}
                          className={`w-8 h-8 rounded-lg text-sm transition-colors ${
                            pageNum === page
                              ? 'bg-stone-900 text-white'
                              : 'hover:bg-stone-100 text-stone-600'
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
                    className="p-2 hover:bg-stone-100 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 text-stone-700" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </StoneCard>
    </div>
  )
}
