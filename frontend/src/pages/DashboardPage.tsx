/**
 * HUD 风格 Dashboard 页面
 * HUD-style Dashboard Page
 *
 * 科幻电影风格的监控面板
 * 深色主题 + 发光效果 + 实时数据
 */

import { useEffect, useState, useCallback } from 'react'
import {
  FileText,
  MessageSquare,
  Calendar,
  Database,
  Zap,
  RefreshCw,
  Activity,
  Clock,
} from 'lucide-react'
import { HUDStatCard, HUDPanel, HUDActivityList, StoneButton, QuotaWarning } from '@/components/ui'
import SourcePieChart from '@/components/charts/SourcePieChart'
import QuotaDisplay from '@/components/QuotaDisplay'
import { scraperService, newsService, quotaService, type ScraperStatus } from '@/services'
import type { QuotaInfo } from '@/types/auth'

// HUD 颜色配置
const CHART_COLORS = ['#06b6d4', '#a855f7', '#3b82f6', '#10b981', '#ec4899', '#f97316']

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [scrapers, setScrapers] = useState<ScraperStatus[]>([])
  const [quota, setQuota] = useState<QuotaInfo | null>(null)
  const [stats, setStats] = useState({
    totalArticles: 0,
    todayArticles: 0,
    yesterdayArticles: 0,
    totalSocialMessages: 0,
    activeSessions: 0,
  })
  const [runningAll, setRunningAll] = useState(false)
  const [runningScrapers, setRunningScrapers] = useState<Set<string>>(new Set())
  const [currentTime, setCurrentTime] = useState(new Date())

  // 更新当前时间
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const fetchData = useCallback(async () => {
    try {
      const [statusResponse, statsResponse, quotaResponse] = await Promise.all([
        scraperService.getStatus(),
        newsService.getStatistics(),
        quotaService.getQuota().catch(() => null),
      ])

      setScrapers(statusResponse.scrapers)
      setQuota(quotaResponse)
      setStats((prev) => ({
        ...prev,
        totalArticles: statsResponse.total_articles || 0,
        todayArticles: statsResponse.articles_today || 0,
        yesterdayArticles: statsResponse.articles_yesterday || 0,
      }))
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleRunAll = async () => {
    setRunningAll(true)
    try {
      await scraperService.runAllScrapers()
      setTimeout(fetchData, 2000)
    } catch (error) {
      console.error('Failed to run all scrapers:', error)
    } finally {
      setRunningAll(false)
    }
  }

  const handleRunScraper = async (sourceKey: string) => {
    setRunningScrapers((prev) => new Set(prev).add(sourceKey))
    try {
      await scraperService.runScraper(sourceKey)
      setTimeout(fetchData, 2000)
    } catch (error) {
      console.error(`Failed to run scraper ${sourceKey}:`, error)
    } finally {
      setRunningScrapers((prev) => {
        const newSet = new Set(prev)
        newSet.delete(sourceKey)
        return newSet
      })
    }
  }

  // 图表数据
  const sourceDistribution = scrapers.map((scraper, index) => ({
    name: scraper.source_name,
    value: scraper.last_run?.articles_scraped || 0,
    color: CHART_COLORS[index % CHART_COLORS.length],
  }))

  // 活动列表数据
  const activityItems = scrapers
    .filter((s) => s.last_run)
    .sort((a, b) => {
      const aTime = a.last_run?.completed_at || ''
      const bTime = b.last_run?.completed_at || ''
      return bTime.localeCompare(aTime)
    })
    .slice(0, 6)
    .map((scraper) => ({
      id: scraper.source_key,
      name: scraper.source_name,
      status: runningScrapers.has(scraper.source_key) || scraper.status === 'running'
        ? 'running' as const
        : scraper.last_run?.status === 'success'
        ? 'success' as const
        : 'error' as const,
      time: formatTimeAgo(scraper.last_run?.completed_at),
      value: scraper.last_run?.articles_new || 0,
    }))

  function formatTimeAgo(dateStr?: string) {
    if (!dateStr) return '从未运行'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60)
    if (diff < 1) return '刚刚'
    if (diff < 60) return `${diff}分钟前`
    if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 顶部状态栏 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">
            系统监控面板
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span>实时数据监控</span>
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* 系统时间 */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-800">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-cyan-400">
              {currentTime.toLocaleTimeString('zh-CN', { hour12: false })}
            </span>
          </div>
          <StoneButton
            variant="secondary"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={fetchData}
            disabled={loading}
          >
            刷新
          </StoneButton>
          <StoneButton
            icon={<Zap className="w-4 h-4" />}
            onClick={handleRunAll}
            loading={runningAll}
          >
            立即采集
          </StoneButton>
        </div>
      </div>

      {/* 配额警告 - 当配额不足时显示 */}
      <QuotaWarning quota={quota} className="mb-6" showDetails />

      {/* 主要统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <HUDStatCard
          title="今日新增"
          value={stats.todayArticles}
          suffix="篇"
          icon={<Calendar className="w-5 h-5" />}
          color="purple"
          trend={stats.yesterdayArticles > 0 ? {
            value: Number((((stats.todayArticles - stats.yesterdayArticles) / stats.yesterdayArticles) * 100).toFixed(1)),
            label: `较昨日 (${stats.yesterdayArticles}篇)`
          } : undefined}
          loading={loading}
        />
        <HUDStatCard
          title="文章总数"
          value={stats.totalArticles}
          suffix="篇"
          icon={<FileText className="w-5 h-5" />}
          color="cyan"
          loading={loading}
        />
        <HUDStatCard
          title="社交消息"
          value={stats.totalSocialMessages}
          suffix="条"
          icon={<MessageSquare className="w-5 h-5" />}
          color="pink"
          loading={loading}
        />
        <HUDStatCard
          title="活跃爬虫"
          value={`${scrapers.filter((s) => s.enabled).length} / ${scrapers.length}`}
          icon={<Database className="w-5 h-5" />}
          color="green"
          loading={loading}
        />
      </div>

      {/* 配额使用情况 */}
      <div className="mb-6">
        <HUDPanel title="资源配额" color="blue">
          <QuotaDisplay mode="full" />
        </HUDPanel>
      </div>

      {/* 中间区域 - 图表和活动 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 来源分布 */}
        <HUDPanel title="采集来源分布" subtitle="按数据源统计" color="purple">
          <div className="flex items-center gap-8">
            <div className="w-1/2 h-[240px]">
              <SourcePieChart data={sourceDistribution} />
            </div>
            <div className="w-1/2 space-y-3">
              {sourceDistribution.map((item) => (
                <div key={item.name} className="flex items-center gap-3">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-slate-400 flex-1 truncate">{item.name}</span>
                  <span className="font-mono text-slate-200">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </HUDPanel>

        {/* 最近活动 */}
        <HUDPanel title="采集活动" subtitle="最近运行记录" color="cyan">
          <HUDActivityList items={activityItems} maxItems={6} />
        </HUDPanel>
      </div>

      {/* 爬虫状态网格 */}
      <HUDPanel title="爬虫状态" subtitle="实时监控" color="green">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {scrapers.map((scraper) => {
            const isRunning = runningScrapers.has(scraper.source_key) || scraper.status === 'running'
            const hasError = scraper.failure_count > 0

            return (
              <button
                key={scraper.source_key}
                onClick={() => handleRunScraper(scraper.source_key)}
                disabled={isRunning}
                className={`
                  relative p-4 rounded-xl text-left
                  bg-slate-800/50 border
                  transition-all duration-300
                  ${isRunning
                    ? 'border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]'
                    : hasError
                    ? 'border-red-500/30 hover:border-red-500/50'
                    : 'border-slate-700/50 hover:border-cyan-500/50 hover:shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                  }
                  disabled:cursor-wait
                `}
              >
                {/* 状态指示灯 */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isRunning
                        ? 'bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.8)]'
                        : hasError
                        ? 'bg-red-400 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                        : 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                    }`}
                  />
                  <span className="text-xs text-slate-500 uppercase tracking-wider">
                    {isRunning ? '运行中' : hasError ? '异常' : '正常'}
                  </span>
                </div>

                {/* 爬虫名称 */}
                <h4 className="font-medium text-slate-200 truncate">
                  {scraper.source_name}
                </h4>

                {/* 统计信息 */}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-slate-500">
                    {formatTimeAgo(scraper.last_run?.completed_at)}
                  </span>
                  {scraper.last_run && (
                    <span className="font-mono text-cyan-400">
                      +{scraper.last_run.articles_new}
                    </span>
                  )}
                </div>

                {/* 运行时的扫描线效果 */}
                {isRunning && (
                  <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none">
                    <div
                      className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-400/10 to-transparent"
                      style={{
                        animation: 'scanline 1.5s linear infinite',
                      }}
                    />
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </HUDPanel>

      {/* 全局扫描线动画 CSS */}
      <style>{`
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
      `}</style>
    </div>
  )
}
