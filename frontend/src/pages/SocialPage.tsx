/**
 * HUD 风格社交数据页面
 * HUD-style Social Data Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react'
import { HUDPanel, StoneButton, StoneSelect, StoneModal, useToast } from '@/components/ui'
import {
  Plus,
  RefreshCw,
  Pause,
  Play,
  Trash2,
  MessageSquare,
  Twitter,
  Send,
  ChevronLeft,
  ChevronRight,
  Download,
  Activity,
  Users,
} from 'lucide-react'
import {
  socialService,
  type SocialSession,
  type SocialMessage,
  type Platform,
  type SessionStatus,
} from '@/services'
import { getApiErrorMessage } from '@/utils/errorHandler'

const platformLabels: Record<Platform, string> = {
  twitter: 'TWITTER',
  telegram: 'TELEGRAM',
}

const statusLabels: Record<SessionStatus, string> = {
  active: '运行中',
  paused: '已暂停',
  completed: '已完成',
  error: '错误',
}

const statusColors: Record<SessionStatus, string> = {
  active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  paused: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  completed: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  error: 'bg-red-500/20 text-red-400 border border-red-500/30',
}

export default function SocialPage() {
  const toast = useToast()
  const [sessions, setSessions] = useState<SocialSession[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [platformFilter, setPlatformFilter] = useState<Platform | ''>('')
  const [statusFilter, setStatusFilter] = useState<SessionStatus | ''>('')

  // 消息面板
  const [selectedSession, setSelectedSession] = useState<SocialSession | null>(null)
  const [messages, setMessages] = useState<SocialMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)

  // 创建会话模态框
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newSession, setNewSession] = useState({
    platform: 'twitter' as Platform,
    target_id: '',
    target_name: '',
    description: '',
  })

  // 采集状态
  const [fetching, setFetching] = useState(false)
  const [fetchingSession, setFetchingSession] = useState<number | null>(null)

  const fetchSessions = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      }
      if (platformFilter) params.platform = platformFilter
      if (statusFilter) params.status = statusFilter

      const response = await socialService.getSessions(params)
      setSessions(response.data)
      setTotal(response.total)
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, platformFilter, statusFilter])

  const fetchMessages = async (session: SocialSession) => {
    setMessagesLoading(true)
    try {
      const response = await socialService.getMessages(session.id, { page_size: 50 })
      setMessages(response.data)
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    } finally {
      setMessagesLoading(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const handleSessionClick = (session: SocialSession) => {
    setSelectedSession(session)
    fetchMessages(session)
  }

  const handlePauseResume = async (session: SocialSession) => {
    try {
      if (session.status === 'active') {
        await socialService.pauseSession(session.id)
      } else {
        await socialService.resumeSession(session.id)
      }
      fetchSessions()
    } catch (error) {
      console.error('Failed to pause/resume session:', error)
    }
  }

  const handleDelete = async (session: SocialSession) => {
    if (!confirm(`确定删除会话 "${session.target_name}"？`)) return
    try {
      await socialService.deleteSession(session.id)
      fetchSessions()
      if (selectedSession?.id === session.id) {
        setSelectedSession(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const handleCreateSession = async () => {
    try {
      await socialService.createSession(newSession)
      setShowCreateModal(false)
      setNewSession({ platform: 'twitter', target_id: '', target_name: '', description: '' })
      fetchSessions()
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  // 采集单个会话
  const handleFetchSession = async (session: SocialSession) => {
    setFetchingSession(session.id)
    try {
      const result = await socialService.fetchSession(session.id)
      if (result.success) {
        toast.success(`采集完成：${result.message}`)
        fetchSessions()
        if (selectedSession?.id === session.id) {
          fetchMessages(session)
        }
      } else {
        toast.error(`采集失败：${result.message}`)
      }
    } catch (error) {
      toast.error(`采集失败：${getApiErrorMessage(error)}`)
    } finally {
      setFetchingSession(null)
    }
  }

  // 采集所有活跃会话
  const handleFetchAll = async () => {
    setFetching(true)
    try {
      const result = await socialService.fetchAllActive()
      toast.success(`采集完成：${result.message}`)
      fetchSessions()
    } catch (error) {
      toast.error(`采集失败：${getApiErrorMessage(error)}`)
    } finally {
      setFetching(false)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">社交数据</h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>共 <span className="text-cyan-400 font-mono">{total}</span> 个会话</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StoneButton variant="secondary" icon={<RefreshCw className="w-4 h-4" />} onClick={fetchSessions} disabled={loading}>
            刷新
          </StoneButton>
          <StoneButton variant="secondary" icon={<Download className="w-4 h-4" />} onClick={handleFetchAll} disabled={fetching} loading={fetching}>
            采集全部
          </StoneButton>
          <StoneButton icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
            添加会话
          </StoneButton>
        </div>
      </div>

      {/* 过滤器 */}
      <HUDPanel color="purple" className="mb-6">
        <div className="flex items-center gap-4">
          <select
            value={platformFilter}
            onChange={(e) => {
              setPlatformFilter(e.target.value as Platform | '')
              setPage(1)
            }}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
          >
            <option value="">全部平台</option>
            <option value="twitter">Twitter</option>
            <option value="telegram">Telegram</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as SessionStatus | '')
              setPage(1)
            }}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-slate-300 focus:outline-none focus:border-purple-500/50"
          >
            <option value="">全部状态</option>
            <option value="active">运行中</option>
            <option value="paused">已暂停</option>
            <option value="completed">已完成</option>
            <option value="error">错误</option>
          </select>
        </div>
      </HUDPanel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 会话列表 */}
        <HUDPanel title="会话列表" subtitle="采集目标" color="cyan">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Users className="w-12 h-12 text-slate-700 mb-3" />
              <p className="text-slate-400">暂无会话</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {sessions.map((session, index) => (
                <div
                  key={session.id}
                  onClick={() => handleSessionClick(session)}
                  className={`p-4 rounded-lg cursor-pointer transition-all border ${
                    selectedSession?.id === session.id
                      ? 'bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                      : 'bg-slate-800/30 border-slate-700/50 hover:border-cyan-500/30'
                  }`}
                  style={{
                    animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both`,
                  }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {session.platform === 'twitter' ? (
                          <Twitter className="w-4 h-4 text-blue-400" />
                        ) : (
                          <Send className="w-4 h-4 text-cyan-400" />
                        )}
                        <span className="text-xs text-slate-500 font-mono">
                          {platformLabels[session.platform]}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded ${statusColors[session.status]}`}>
                          {statusLabels[session.status]}
                        </span>
                      </div>
                      <h4 className="text-slate-200 font-medium truncate">{session.target_name}</h4>
                      <p className="text-sm text-slate-500 font-mono">@{session.target_username || session.target_id}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-600">
                        <span><span className="text-cyan-400">{session.message_count}</span> 条消息</span>
                        <span>LAST: {formatDate(session.last_fetch_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleFetchSession(session) }}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="立即采集"
                        disabled={fetchingSession === session.id}
                      >
                        {fetchingSession === session.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cyan-400"></div>
                        ) : (
                          <Download className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                        )}
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handlePauseResume(session) }}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title={session.status === 'active' ? '暂停' : '恢复'}
                      >
                        {session.status === 'active' ? (
                          <Pause className="w-4 h-4 text-slate-500 hover:text-yellow-400" />
                        ) : (
                          <Play className="w-4 h-4 text-slate-500 hover:text-emerald-400" />
                        )}
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(session) }}
                        className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t border-slate-700/50">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 transition-colors"
              >
                <ChevronLeft className="w-4 h-4 text-slate-400" />
              </button>
              <span className="text-sm text-slate-500 font-mono">
                <span className="text-cyan-400">{page}</span> / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 hover:bg-slate-700/50 rounded-lg disabled:opacity-30 transition-colors"
              >
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          )}
        </HUDPanel>

        {/* 消息预览 */}
        <HUDPanel
          title={selectedSession ? `${selectedSession.target_name} 的消息` : '消息预览'}
          subtitle="实时数据"
          color="green"
        >
          {!selectedSession ? (
            <div className="flex flex-col items-center justify-center py-12">
              <MessageSquare className="w-12 h-12 text-slate-700 mb-4" />
              <p className="text-slate-400">选择一个会话查看消息</p>
            </div>
          ) : messagesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400"></div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <MessageSquare className="w-12 h-12 text-slate-700 mb-3" />
              <p className="text-slate-400">暂无消息</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50"
                  style={{
                    animation: `fadeInUp 0.3s ease-out ${index * 0.02}s both`,
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500/30 to-cyan-500/30 flex items-center justify-center flex-shrink-0 border border-emerald-500/30">
                      <span className="text-sm text-emerald-400 font-bold">
                        {message.author_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-slate-200">{message.author_name}</span>
                        {message.author_username && (
                          <span className="text-sm text-slate-500 font-mono">@{message.author_username}</span>
                        )}
                      </div>
                      <p className="text-slate-300 text-sm whitespace-pre-wrap break-words">
                        {message.content}
                      </p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-slate-600 font-mono">
                        <span><span className="text-pink-400">{message.like_count}</span> LIKES</span>
                        <span><span className="text-cyan-400">{message.repost_count}</span> RT</span>
                        <span><span className="text-purple-400">{message.reply_count}</span> REPLY</span>
                        <span className="text-slate-500">{formatDate(message.posted_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </HUDPanel>
      </div>

      {/* 创建会话模态框 */}
      <StoneModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="添加采集会话"
        width="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">平台</label>
            <StoneSelect
              value={newSession.platform}
              onChange={(e) => setNewSession({ ...newSession, platform: e.target.value as Platform })}
              className="w-full"
            >
              <option value="twitter">Twitter</option>
              <option value="telegram">Telegram</option>
            </StoneSelect>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">目标 ID</label>
            <input
              value={newSession.target_id}
              onChange={(e) => setNewSession({ ...newSession, target_id: e.target.value })}
              placeholder="用户 ID 或频道 ID"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">显示名称</label>
            <input
              value={newSession.target_name}
              onChange={(e) => setNewSession({ ...newSession, target_name: e.target.value })}
              placeholder="显示名称"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">描述（可选）</label>
            <input
              value={newSession.description}
              onChange={(e) => setNewSession({ ...newSession, description: e.target.value })}
              placeholder="会话描述"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <StoneButton variant="secondary" onClick={() => setShowCreateModal(false)}>取消</StoneButton>
            <StoneButton
              onClick={handleCreateSession}
              disabled={!newSession.target_id || !newSession.target_name}
            >
              创建
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
