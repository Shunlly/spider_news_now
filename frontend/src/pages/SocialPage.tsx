/**
 * 社交数据页面
 * Social Data Page
 */

import { useState, useEffect, useCallback } from 'react'
import { GlassCard, GlassButton, GlassInput } from '@/components/glass'
import {
  IconPlus,
  IconRefresh,
  IconPause,
  IconPlayArrow,
  IconDelete,
  IconMessage,
  IconTwitter,
  IconLeft,
  IconRight,
  IconClose,
} from '@arco-design/web-react/icon'
import {
  socialService,
  type SocialSession,
  type SocialMessage,
  type Platform,
  type SessionStatus,
} from '@/services'

const platformLabels: Record<Platform, string> = {
  twitter: 'Twitter',
  telegram: 'Telegram',
}

const statusLabels: Record<SessionStatus, string> = {
  active: '运行中',
  paused: '已暂停',
  completed: '已完成',
  error: '错误',
}

const statusColors: Record<SessionStatus, string> = {
  active: 'bg-green-500/20 text-green-400',
  paused: 'bg-yellow-500/20 text-yellow-400',
  completed: 'bg-blue-500/20 text-blue-400',
  error: 'bg-red-500/20 text-red-400',
}

export default function SocialPage() {
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

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">社交数据</h1>
          <p className="text-white/60 mt-1">
            共 {total} 个会话
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GlassButton icon={<IconRefresh />} onClick={fetchSessions} disabled={loading}>
            刷新
          </GlassButton>
          <GlassButton variant="primary" icon={<IconPlus />} onClick={() => setShowCreateModal(true)}>
            添加会话
          </GlassButton>
        </div>
      </div>

      {/* 过滤器 */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-4">
          <select
            value={platformFilter}
            onChange={(e) => {
              setPlatformFilter(e.target.value as Platform | '')
              setPage(1)
            }}
            className="bg-slate-800 border border-white/20 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="" className="bg-slate-800 text-white">全部平台</option>
            <option value="twitter" className="bg-slate-800 text-white">Twitter</option>
            <option value="telegram" className="bg-slate-800 text-white">Telegram</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as SessionStatus | '')
              setPage(1)
            }}
            className="bg-slate-800 border border-white/20 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="" className="bg-slate-800 text-white">全部状态</option>
            <option value="active" className="bg-slate-800 text-white">运行中</option>
            <option value="paused" className="bg-slate-800 text-white">已暂停</option>
            <option value="completed" className="bg-slate-800 text-white">已完成</option>
            <option value="error" className="bg-slate-800 text-white">错误</option>
          </select>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 会话列表 */}
        <GlassCard className="overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h3 className="font-semibold text-white">会话列表</h3>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-white/60">暂无会话</p>
            </div>
          ) : (
            <div className="divide-y divide-white/10 max-h-[600px] overflow-y-auto">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSessionClick(session)}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedSession?.id === session.id ? 'bg-white/10' : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <IconTwitter className="text-white/60 text-sm" />
                        <span className="text-xs text-white/40">
                          {platformLabels[session.platform]}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded ${statusColors[session.status]}`}>
                          {statusLabels[session.status]}
                        </span>
                      </div>
                      <h4 className="text-white font-medium truncate">{session.target_name}</h4>
                      <p className="text-sm text-white/50">@{session.target_username || session.target_id}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                        <span>{session.message_count} 条消息</span>
                        <span>最后采集: {formatDate(session.last_fetch_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); handlePauseResume(session) }}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                        title={session.status === 'active' ? '暂停' : '恢复'}
                      >
                        {session.status === 'active' ? (
                          <IconPause className="text-white/60" />
                        ) : (
                          <IconPlayArrow className="text-white/60" />
                        )}
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(session) }}
                        className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                        title="删除"
                      >
                        <IconDelete className="text-red-400" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 p-4 border-t border-white/10">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30"
              >
                <IconLeft className="text-white" />
              </button>
              <span className="text-sm text-white/50">{page} / {totalPages}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 hover:bg-white/10 rounded-lg disabled:opacity-30"
              >
                <IconRight className="text-white" />
              </button>
            </div>
          )}
        </GlassCard>

        {/* 消息预览 */}
        <GlassCard className="overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h3 className="font-semibold text-white">
              {selectedSession ? `${selectedSession.target_name} 的消息` : '消息预览'}
            </h3>
          </div>
          {!selectedSession ? (
            <div className="flex flex-col items-center justify-center py-12">
              <IconMessage className="text-4xl text-white/20 mb-4" />
              <p className="text-white/40">选择一个会话查看消息</p>
            </div>
          ) : messagesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-white/60">暂无消息</p>
            </div>
          ) : (
            <div className="divide-y divide-white/10 max-h-[600px] overflow-y-auto">
              {messages.map((message) => (
                <div key={message.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm text-white/60">
                        {message.author_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-white">{message.author_name}</span>
                        {message.author_username && (
                          <span className="text-sm text-white/40">@{message.author_username}</span>
                        )}
                      </div>
                      <p className="text-white/80 text-sm whitespace-pre-wrap break-words">
                        {message.content}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                        <span>{message.like_count} 赞</span>
                        <span>{message.repost_count} 转发</span>
                        <span>{message.reply_count} 回复</span>
                        <span>{formatDate(message.posted_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* 创建会话模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <GlassCard className="w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">添加采集会话</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg"
              >
                <IconClose className="text-white/60" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">平台</label>
                <select
                  value={newSession.platform}
                  onChange={(e) => setNewSession({ ...newSession, platform: e.target.value as Platform })}
                  className="w-full bg-slate-800 border border-white/20 rounded-lg px-3 py-2 text-white"
                >
                  <option value="twitter" className="bg-slate-800 text-white">Twitter</option>
                  <option value="telegram" className="bg-slate-800 text-white">Telegram</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">目标 ID</label>
                <GlassInput
                  value={newSession.target_id}
                  onChange={(e) => setNewSession({ ...newSession, target_id: e.target.value })}
                  placeholder="用户 ID 或频道 ID"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">显示名称</label>
                <GlassInput
                  value={newSession.target_name}
                  onChange={(e) => setNewSession({ ...newSession, target_name: e.target.value })}
                  placeholder="显示名称"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">描述（可选）</label>
                <GlassInput
                  value={newSession.description}
                  onChange={(e) => setNewSession({ ...newSession, description: e.target.value })}
                  placeholder="会话描述"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <GlassButton onClick={() => setShowCreateModal(false)}>取消</GlassButton>
                <GlassButton
                  variant="primary"
                  onClick={handleCreateSession}
                  disabled={!newSession.target_id || !newSession.target_name}
                >
                  创建
                </GlassButton>
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
