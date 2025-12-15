/**
 * Dashboard 页面
 * Dashboard Page
 *
 * 遵循宪法 III.B Bento Grid 布局规范
 * 展示系统核心指标和最近活动
 */

import { useEffect, useState, useCallback } from 'react'
import {
  IconFile,
  IconMessage,
  IconCalendar,
  IconStorage,
  IconThunderbolt,
  IconCheckCircle,
  IconCloseCircle,
  IconLoading,
  IconRefresh,
} from '@arco-design/web-react/icon'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts'
import { BentoGrid, BentoItem, GlassCard, StatCard, GlassButton } from '@/components/glass'
import { scraperService, newsService, type ScraperStatus } from '@/services'

// 颜色配置
const COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#f472b6', '#fb7185']

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [scrapers, setScrapers] = useState<ScraperStatus[]>([])
  const [stats, setStats] = useState({
    totalArticles: 0,
    todayArticles: 0,
    totalSocialMessages: 0,
    activeSessions: 0,
  })
  const [runningAll, setRunningAll] = useState(false)
  const [runningScrapers, setRunningScrapers] = useState<Set<string>>(new Set())

  const fetchData = useCallback(async () => {
    try {
      // 获取爬虫状态
      const statusResponse = await scraperService.getStatus()
      setScrapers(statusResponse.scrapers)

      // 获取真实的统计数据（从数据库）
      const statsResponse = await newsService.getStatistics()

      setStats((prev) => ({
        ...prev,
        totalArticles: statsResponse.total_articles || 0,
        todayArticles: statsResponse.articles_today || 0,
      }))
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    // 每30秒刷新一次状态
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleRunAll = async () => {
    setRunningAll(true)
    try {
      await scraperService.runAllScrapers()
      // 延迟刷新状态
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
      // 延迟刷新状态
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

  // 准备图表数据
  const sourceDistribution = scrapers.map((scraper, index) => ({
    name: scraper.source_name,
    value: scraper.last_run?.articles_scraped || 0,
    color: COLORS[index % COLORS.length],
  }))

  const getStatusIcon = (scraper: ScraperStatus) => {
    if (scraper.status === 'running' || runningScrapers.has(scraper.source_key)) {
      return <IconLoading className="text-blue-400 animate-spin" />
    }
    if (scraper.failure_count > 0) {
      return <IconCloseCircle className="text-red-400" />
    }
    if (scraper.last_run?.status === 'success') {
      return <IconCheckCircle className="text-green-400" />
    }
    return <span className="w-2 h-2 rounded-full bg-gray-400" />
  }

  const getStatusDot = (scraper: ScraperStatus) => {
    if (scraper.status === 'running' || runningScrapers.has(scraper.source_key)) {
      return 'status-dot-active'
    }
    if (scraper.failure_count > 0) {
      return 'status-dot-error'
    }
    return 'status-dot-idle'
  }

  const formatLastRun = (scraper: ScraperStatus) => {
    if (!scraper.last_run?.completed_at) return '从未运行'
    const date = new Date(scraper.last_run.completed_at)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60)
    if (diff < 1) return '刚刚'
    if (diff < 60) return `${diff}分钟前`
    if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">仪表盘</h1>
          <p className="text-white/60 mt-1">系统运行状态概览</p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton icon={<IconRefresh />} onClick={fetchData} disabled={loading}>
            刷新
          </GlassButton>
          <GlassButton
            variant="primary"
            icon={<IconThunderbolt />}
            onClick={handleRunAll}
            loading={runningAll}
          >
            立即采集
          </GlassButton>
        </div>
      </div>

      {/* Bento Grid 布局 */}
      <BentoGrid>
        {/* 核心指标卡片 */}
        <BentoItem>
          <StatCard
            title="今日新增"
            value={stats.todayArticles}
            suffix="篇"
            icon={<IconCalendar />}
            iconBg="bg-purple-500/30"
            loading={loading}
          />
        </BentoItem>

        <BentoItem>
          <StatCard
            title="本次采集"
            value={stats.totalArticles}
            suffix="篇"
            icon={<IconFile />}
            iconBg="bg-indigo-500/30"
            loading={loading}
          />
        </BentoItem>

        <BentoItem>
          <StatCard
            title="社交消息"
            value={stats.totalSocialMessages}
            suffix="条"
            icon={<IconMessage />}
            iconBg="bg-pink-500/30"
            loading={loading}
          />
        </BentoItem>

        <BentoItem>
          <StatCard
            title="活跃爬虫"
            value={scrapers.filter((s) => s.enabled).length}
            suffix={`/ ${scrapers.length}`}
            icon={<IconStorage />}
            iconBg="bg-cyan-500/30"
            loading={loading}
          />
        </BentoItem>

        {/* 来源分布饼图 */}
        <BentoItem colSpan={2} rowSpan={2}>
          <GlassCard className="h-full p-6">
            <h3 className="text-lg font-semibold text-white mb-4">来源分布</h3>
            <div className="h-[280px] flex items-center">
              <div className="w-1/2">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={sourceDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {sourceDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        border: '1px solid rgba(255,255,255,0.3)',
                        borderRadius: '12px',
                        color: '#fff',
                      }}
                      itemStyle={{ color: '#fff' }}
                      labelStyle={{ color: '#fff', fontWeight: 'bold', marginBottom: '4px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="w-1/2 space-y-2">
                {sourceDistribution.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-white/70 text-sm flex-1 truncate">{item.name}</span>
                    <span className="text-white font-medium">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        </BentoItem>

        {/* 爬虫状态列表 */}
        <BentoItem colSpan={2} rowSpan={2}>
          <GlassCard className="h-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">爬虫状态</h3>
              <span className="text-sm text-white/50">
                {scrapers.filter((s) => s.status === 'running').length} 运行中
              </span>
            </div>
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
              {scrapers.map((scraper) => (
                <div
                  key={scraper.source_key}
                  className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className={`status-dot ${getStatusDot(scraper)}`} />
                    <div>
                      <span className="text-white font-medium">{scraper.source_name}</span>
                      <div className="text-xs text-white/40">
                        {formatLastRun(scraper)}
                        {scraper.last_run && (
                          <span className="ml-2">
                            新增 {scraper.last_run.articles_new} / 共 {scraper.last_run.articles_scraped}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(scraper)}
                    <button
                      onClick={() => handleRunScraper(scraper.source_key)}
                      disabled={runningScrapers.has(scraper.source_key) || scraper.status === 'running'}
                      className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      title="立即运行"
                    >
                      <IconThunderbolt className="text-white/60" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </BentoItem>

        {/* 最近采集活动 */}
        <BentoItem colSpan={2}>
          <GlassCard className="h-full p-6">
            <h3 className="text-lg font-semibold text-white mb-4">最近采集活动</h3>
            <div className="space-y-2">
              {scrapers
                .filter((s) => s.last_run)
                .sort((a, b) => {
                  const aTime = a.last_run?.completed_at || ''
                  const bTime = b.last_run?.completed_at || ''
                  return bTime.localeCompare(aTime)
                })
                .slice(0, 5)
                .map((scraper) => (
                  <div
                    key={scraper.source_key}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-white/70">{scraper.source_name}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-white/40">{formatLastRun(scraper)}</span>
                      <span
                        className={
                          scraper.last_run?.status === 'success'
                            ? 'text-green-400'
                            : 'text-red-400'
                        }
                      >
                        {scraper.last_run?.status === 'success' ? '成功' : '失败'}
                      </span>
                      <span className="text-white">
                        +{scraper.last_run?.articles_new || 0}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </GlassCard>
        </BentoItem>

        {/* 下次采集计划 */}
        <BentoItem colSpan={2}>
          <GlassCard className="h-full p-6">
            <h3 className="text-lg font-semibold text-white mb-4">下次采集计划</h3>
            <div className="space-y-2">
              {scrapers
                .filter((s) => s.next_run_at)
                .sort((a, b) => (a.next_run_at || '').localeCompare(b.next_run_at || ''))
                .slice(0, 5)
                .map((scraper) => {
                  const nextRun = new Date(scraper.next_run_at)
                  const now = new Date()
                  const diff = Math.floor((nextRun.getTime() - now.getTime()) / 1000 / 60)
                  const timeStr =
                    diff < 1
                      ? '即将开始'
                      : diff < 60
                      ? `${diff}分钟后`
                      : `${Math.floor(diff / 60)}小时后`

                  return (
                    <div
                      key={scraper.source_key}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-white/70">{scraper.source_name}</span>
                      <span className="text-white/40">{timeStr}</span>
                    </div>
                  )
                })}
            </div>
          </GlassCard>
        </BentoItem>
      </BentoGrid>
    </div>
  )
}
