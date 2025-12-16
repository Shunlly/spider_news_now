/**
 * Telegram 管理页面
 * Telegram Management Page
 */

import { useState, useEffect, useCallback } from 'react'
import { GlassCard, GlassButton, GlassInput } from '@/components/glass'
import {
  IconSend,
  IconRefresh,
  IconPlus,
  IconDelete,
  IconMessage,
  IconUser,
  IconCheckCircle,
  IconCloseCircle,
  IconLoading,
  IconSettings,
  IconEye,
  IconLink,
} from '@arco-design/web-react/icon'
import telegramService, {
  type TelegramDialog,
  type TelegramUserInfo,
  type TelegramEntity,
  type TelegramMessage,
} from '@/services/telegramService'

type AuthStep = 'init' | 'sendCode' | 'signIn' | 'connected'

export default function TelegramPage() {
  // 认证状态
  const [authStep, setAuthStep] = useState<AuthStep>('init')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userInfo, setUserInfo] = useState<TelegramUserInfo | null>(null)

  // 认证表单
  const [apiId, setApiId] = useState('')
  const [apiHash, setApiHash] = useState('')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [phoneCodeHash, setPhoneCodeHash] = useState('')
  const [password, setPassword] = useState('')
  const [needPassword, setNeedPassword] = useState(false)
  const [stringSession, setStringSession] = useState('')
  const [savedSession, setSavedSession] = useState('')

  // 对话/频道状态
  const [dialogs, setDialogs] = useState<TelegramDialog[]>([])
  const [filterType, setFilterType] = useState<string>('')
  const [dialogsLoading, setDialogsLoading] = useState(false)

  // 搜索状态
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState<TelegramEntity | null>(null)
  const [searching, setSearching] = useState(false)

  // 消息状态
  const [selectedChannel, setSelectedChannel] = useState<TelegramDialog | null>(null)
  const [messages, setMessages] = useState<TelegramMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)

  // 初始化时检查连接状态
  useEffect(() => {
    checkStatus()
    // 从 localStorage 加载保存的配置
    const saved = localStorage.getItem('telegram_config')
    if (saved) {
      try {
        const config = JSON.parse(saved)
        setApiId(config.api_id || '')
        setApiHash(config.api_hash || '')
        setSavedSession(config.string_session || '')
      } catch (e) {
        console.error('Failed to load saved config:', e)
      }
    }
  }, [])

  const checkStatus = async () => {
    try {
      const response = await telegramService.getStatus()
      if (response.connected && response.user_info) {
        setUserInfo(response.user_info)
        setAuthStep('connected')
      }
    } catch (e) {
      console.error('Failed to check status:', e)
    }
  }

  // 初始化客户端
  const handleInit = async () => {
    if (!apiId || !apiHash) {
      setError('请填写 API ID 和 API Hash')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await telegramService.initClient({
        api_id: parseInt(apiId),
        api_hash: apiHash,
      })

      if (response.success) {
        setAuthStep('sendCode')
        // 保存配置
        localStorage.setItem('telegram_config', JSON.stringify({
          api_id: apiId,
          api_hash: apiHash,
        }))
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '初始化失败')
    } finally {
      setLoading(false)
    }
  }

  // 使用已保存的 Session 连接
  const handleConnectWithSession = async () => {
    if (!apiId || !apiHash || !savedSession) {
      setError('请填写完整信息')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await telegramService.connectWithSession({
        api_id: parseInt(apiId),
        api_hash: apiHash,
        string_session: savedSession,
      })

      if (response.success && response.user_info) {
        setUserInfo(response.user_info)
        setAuthStep('connected')
        // 更新保存的配置
        localStorage.setItem('telegram_config', JSON.stringify({
          api_id: apiId,
          api_hash: apiHash,
          string_session: savedSession,
        }))
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '连接失败')
    } finally {
      setLoading(false)
    }
  }

  // 发送验证码
  const handleSendCode = async () => {
    if (!phone) {
      setError('请填写手机号码')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await telegramService.sendCode(phone)

      if (response.success && response.phone_code_hash) {
        setPhoneCodeHash(response.phone_code_hash)
        setAuthStep('signIn')
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '发送验证码失败')
    } finally {
      setLoading(false)
    }
  }

  // 验证登录
  const handleSignIn = async () => {
    if (!code) {
      setError('请填写验证码')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await telegramService.signIn({
        phone,
        code,
        phone_code_hash: phoneCodeHash,
        password: needPassword ? password : undefined,
      })

      if (response.success && response.user_info) {
        setUserInfo(response.user_info)
        setStringSession(response.string_session || '')
        setAuthStep('connected')
        // 保存 session
        if (response.string_session) {
          localStorage.setItem('telegram_config', JSON.stringify({
            api_id: apiId,
            api_hash: apiHash,
            string_session: response.string_session,
          }))
        }
      } else if (response.need_password) {
        setNeedPassword(true)
        setError('需要两步验证密码')
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  // 断开连接
  const handleDisconnect = async () => {
    try {
      await telegramService.disconnect()
      setUserInfo(null)
      setAuthStep('init')
      setDialogs([])
      setSelectedChannel(null)
      setMessages([])
    } catch (e) {
      console.error('Disconnect failed:', e)
    }
  }

  // 获取对话列表
  const fetchDialogs = useCallback(async () => {
    setDialogsLoading(true)
    try {
      const response = await telegramService.getDialogs({
        limit: 100,
        filter_type: filterType as 'channel' | 'group' | 'user' | undefined,
      })
      if (response.success) {
        setDialogs(response.dialogs)
      }
    } catch (e) {
      console.error('Failed to fetch dialogs:', e)
    } finally {
      setDialogsLoading(false)
    }
  }, [filterType])

  useEffect(() => {
    if (authStep === 'connected') {
      fetchDialogs()
    }
  }, [authStep, fetchDialogs])

  // 添加频道（搜索 + 自动加入）
  const handleAddChannel = async () => {
    if (!searchQuery.trim()) return

    setSearching(true)
    setSearchResult(null)
    setError('')

    try {
      // 1. 先搜索频道
      const response = await telegramService.searchChannel(searchQuery.trim())
      if (!response.success || !response.entity) {
        setError(response.message || '未找到该频道')
        return
      }

      const entity = response.entity

      // 2. 检查是否已加入
      const alreadyJoined = dialogs.some(
        d => d.id === entity.id ||
             (d.username && entity.username && d.username.toLowerCase() === entity.username.toLowerCase())
      )

      if (alreadyJoined) {
        setSearchResult({ ...entity, _alreadyJoined: true } as any)
        return
      }

      // 3. 未加入则自动加入
      setSearchResult(entity)
      const joinResponse = await telegramService.joinChannel(entity.username || String(entity.id))
      if (joinResponse.success) {
        setSearchResult({ ...entity, _justJoined: true } as any)
        fetchDialogs()
        // 3秒后清除结果
        setTimeout(() => {
          setSearchResult(null)
          setSearchQuery('')
        }, 3000)
      } else {
        setError(joinResponse.message)
      }
    } catch (e: any) {
      setError(e.message || '添加失败')
    } finally {
      setSearching(false)
    }
  }

  // 手动加入频道（从搜索结果）
  const handleJoin = async (channel: string) => {
    setLoading(true)
    try {
      const response = await telegramService.joinChannel(channel)
      if (response.success) {
        fetchDialogs()
        setSearchResult(null)
        setSearchQuery('')
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '加入失败')
    } finally {
      setLoading(false)
    }
  }

  // 退出频道
  const handleLeave = async (channelId: number) => {
    if (!confirm('确定要退出该频道吗？')) return

    setLoading(true)
    try {
      const response = await telegramService.leaveChannel(channelId)
      if (response.success) {
        fetchDialogs()
        if (selectedChannel?.id === channelId) {
          setSelectedChannel(null)
          setMessages([])
        }
      } else {
        setError(response.message)
      }
    } catch (e: any) {
      setError(e.message || '退出失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取消息
  const fetchMessages = async (channel: TelegramDialog) => {
    setSelectedChannel(channel)
    setMessagesLoading(true)

    try {
      const response = await telegramService.getMessages(channel.id, { limit: 50 })
      if (response.success) {
        setMessages(response.messages)
      }
    } catch (e) {
      console.error('Failed to fetch messages:', e)
    } finally {
      setMessagesLoading(false)
    }
  }

  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 渲染认证界面
  const renderAuthUI = () => {
    if (authStep === 'connected') return null

    return (
      <GlassCard className="p-6 max-w-md mx-auto">
        <h2 className="text-lg font-semibold text-white mb-4">
          {authStep === 'init' && 'Telegram 登录'}
          {authStep === 'sendCode' && '发送验证码'}
          {authStep === 'signIn' && '验证登录'}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {authStep === 'init' && (
            <>
              <div>
                <label className="block text-sm text-white/60 mb-1">API ID</label>
                <GlassInput
                  value={apiId}
                  onChange={(e) => setApiId(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-1">API Hash</label>
                <GlassInput
                  type="password"
                  value={apiHash}
                  onChange={(e) => setApiHash(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                />
              </div>
              {savedSession && (
                <div>
                  <label className="block text-sm text-white/60 mb-1">已保存的 Session（可选）</label>
                  <GlassInput
                    value={savedSession}
                    onChange={(e) => setSavedSession(e.target.value)}
                    placeholder="之前保存的 StringSession"
                  />
                  <GlassButton
                    className="w-full mt-2"
                    onClick={handleConnectWithSession}
                    loading={loading}
                  >
                    使用 Session 连接
                  </GlassButton>
                </div>
              )}
              <div className="border-t border-white/10 pt-4">
                <GlassButton
                  className="w-full"
                  variant="primary"
                  onClick={handleInit}
                  loading={loading}
                >
                  初始化客户端
                </GlassButton>
              </div>
              <p className="text-xs text-white/40 text-center">
                请先在 <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">my.telegram.org</a> 创建应用获取 API 凭证
              </p>
            </>
          )}

          {authStep === 'sendCode' && (
            <>
              <div>
                <label className="block text-sm text-white/60 mb-1">手机号码</label>
                <GlassInput
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+86xxxxxxxxx"
                />
              </div>
              <GlassButton
                className="w-full"
                variant="primary"
                onClick={handleSendCode}
                loading={loading}
              >
                发送验证码
              </GlassButton>
            </>
          )}

          {authStep === 'signIn' && (
            <>
              <div>
                <label className="block text-sm text-white/60 mb-1">验证码</label>
                <GlassInput
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="输入收到的验证码"
                />
              </div>
              {needPassword && (
                <div>
                  <label className="block text-sm text-white/60 mb-1">两步验证密码</label>
                  <GlassInput
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="输入两步验证密码"
                  />
                </div>
              )}
              <GlassButton
                className="w-full"
                variant="primary"
                onClick={handleSignIn}
                loading={loading}
              >
                验证登录
              </GlassButton>
            </>
          )}
        </div>
      </GlassCard>
    )
  }

  // 渲染已连接界面
  const renderConnectedUI = () => {
    if (authStep !== 'connected') return null

    return (
      <div className="space-y-6">
        {/* 用户信息 */}
        <GlassCard className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
                <IconUser className="text-white text-lg" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">
                    {userInfo?.first_name} {userInfo?.last_name}
                  </span>
                  <IconCheckCircle className="text-green-400" />
                </div>
                <span className="text-sm text-white/50">
                  @{userInfo?.username || userInfo?.phone}
                </span>
              </div>
            </div>
            <GlassButton size="sm" onClick={handleDisconnect}>
              断开连接
            </GlassButton>
          </div>
        </GlassCard>

        {/* 添加频道 */}
        <GlassCard className="p-4">
          <h3 className="text-white font-medium mb-3">添加频道</h3>
          <div className="flex gap-2">
            <GlassInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入频道用户名或链接，如 @telegram 或 t.me/telegram"
              onKeyDown={(e) => e.key === 'Enter' && handleAddChannel()}
              className="flex-1"
            />
            <GlassButton
              icon={<IconPlus />}
              onClick={handleAddChannel}
              loading={searching}
              variant="primary"
            >
              添加
            </GlassButton>
          </div>

          {/* 添加结果 */}
          {searchResult && (
            <div className={`mt-4 p-3 rounded-lg flex items-center justify-between ${
              (searchResult as any)._alreadyJoined ? 'bg-yellow-500/10 border border-yellow-500/30' :
              (searchResult as any)._justJoined ? 'bg-green-500/10 border border-green-500/30' :
              'bg-white/5'
            }`}>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">{searchResult.title}</span>
                  {(searchResult as any)._alreadyJoined && (
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">已加入</span>
                  )}
                  {(searchResult as any)._justJoined && (
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">加入成功</span>
                  )}
                </div>
                <div className="text-sm text-white/50">
                  @{searchResult.username} · {searchResult.type} · {searchResult.participant_count?.toLocaleString()} 成员
                </div>
                {searchResult.description && (
                  <p className="text-sm text-white/40 mt-1 line-clamp-2">{searchResult.description}</p>
                )}
              </div>
              {!(searchResult as any)._alreadyJoined && !(searchResult as any)._justJoined && (
                <GlassButton
                  size="sm"
                  variant="primary"
                  icon={<IconPlus />}
                  onClick={() => handleJoin(searchResult.username || String(searchResult.id))}
                  loading={loading}
                >
                  加入
                </GlassButton>
              )}
            </div>
          )}
        </GlassCard>

        {/* 频道列表和消息 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 频道列表 */}
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-medium">已加入的频道</h3>
              <div className="flex items-center gap-2">
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="bg-slate-800 border border-white/20 rounded px-2 py-1 text-white text-sm"
                >
                  <option value="">全部</option>
                  <option value="channel">频道</option>
                  <option value="group">群组</option>
                </select>
                <GlassButton
                  size="sm"
                  icon={<IconRefresh />}
                  onClick={fetchDialogs}
                  loading={dialogsLoading}
                />
              </div>
            </div>

            {dialogsLoading ? (
              <div className="flex items-center justify-center py-8">
                <IconLoading className="animate-spin text-white text-2xl" />
              </div>
            ) : dialogs.length === 0 ? (
              <div className="text-center py-8 text-white/50">
                暂无频道，请搜索并加入
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {dialogs.map((dialog) => (
                  <div
                    key={dialog.id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedChannel?.id === dialog.id
                        ? 'bg-indigo-500/30 border border-indigo-500/50'
                        : 'bg-white/5 hover:bg-white/10'
                    }`}
                    onClick={() => fetchMessages(dialog)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium truncate">{dialog.title}</span>
                          {dialog.is_pinned && (
                            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-1 rounded">置顶</span>
                          )}
                        </div>
                        <div className="text-xs text-white/50 flex items-center gap-2 mt-1">
                          <span className={`px-1.5 py-0.5 rounded ${
                            dialog.type === 'channel' ? 'bg-blue-500/20 text-blue-400' :
                            dialog.type === 'group' ? 'bg-green-500/20 text-green-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {dialog.type === 'channel' ? '频道' : dialog.type === 'group' ? '群组' : '私聊'}
                          </span>
                          {dialog.participant_count && (
                            <span>{dialog.participant_count.toLocaleString()} 成员</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleLeave(dialog.id)
                          }}
                          className="p-1.5 hover:bg-red-500/20 rounded text-red-400 opacity-50 hover:opacity-100 transition-opacity"
                          title="退出"
                        >
                          <IconDelete />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>

          {/* 消息列表 */}
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-medium">
                {selectedChannel ? selectedChannel.title : '选择频道查看消息'}
              </h3>
              {selectedChannel && (
                <GlassButton
                  size="sm"
                  icon={<IconRefresh />}
                  onClick={() => fetchMessages(selectedChannel)}
                  loading={messagesLoading}
                />
              )}
            </div>

            {!selectedChannel ? (
              <div className="text-center py-12 text-white/50">
                <IconMessage className="text-4xl mb-2 mx-auto" />
                <p>点击左侧频道查看消息</p>
              </div>
            ) : messagesLoading ? (
              <div className="flex items-center justify-center py-12">
                <IconLoading className="animate-spin text-white text-2xl" />
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 text-white/50">
                暂无消息
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.map((msg) => (
                  <div key={msg.id} className="p-3 bg-white/5 rounded-lg">
                    <div className="flex items-center justify-between mb-2 text-xs text-white/40">
                      <span>{formatDate(msg.date)}</span>
                      <div className="flex items-center gap-3">
                        {msg.views && (
                          <span className="flex items-center gap-1">
                            <IconEye /> {msg.views.toLocaleString()}
                          </span>
                        )}
                        {msg.forwards && (
                          <span className="flex items-center gap-1">
                            <IconSend /> {msg.forwards}
                          </span>
                        )}
                      </div>
                    </div>
                    {msg.text && (
                      <p className="text-white/80 text-sm whitespace-pre-wrap line-clamp-4">
                        {msg.text}
                      </p>
                    )}
                    {msg.urls && msg.urls.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {msg.urls.slice(0, 3).map((url, i) => (
                          <a
                            key={i}
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-indigo-400 hover:underline flex items-center gap-1"
                          >
                            <IconLink /> 链接 {i + 1}
                          </a>
                        ))}
                      </div>
                    )}
                    {msg.media_type && (
                      <span className="inline-block mt-2 text-xs bg-white/10 text-white/50 px-2 py-0.5 rounded">
                        {msg.media_type === 'photo' ? '图片' :
                         msg.media_type === 'video' ? '视频' :
                         msg.media_type === 'document' ? '文档' : msg.media_type}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        {/* StringSession 显示 */}
        {stringSession && (
          <GlassCard className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-white font-medium flex items-center gap-2">
                <IconSettings /> StringSession
              </h3>
              <GlassButton
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(stringSession)
                  alert('已复制到剪贴板')
                }}
              >
                复制
              </GlassButton>
            </div>
            <p className="text-xs text-white/40 mb-2">
              请妥善保存此 Session，下次可直接使用它登录，无需重新验证
            </p>
            <div className="bg-black/30 rounded p-2 text-xs text-white/60 font-mono break-all max-h-20 overflow-y-auto">
              {stringSession}
            </div>
          </GlassCard>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Telegram 管理</h1>
          <p className="text-white/60 mt-1">
            {authStep === 'connected'
              ? `已连接 · ${dialogs.length} 个频道`
              : '使用 MTProto API 获取 Telegram 数据'}
          </p>
        </div>
      </div>

      {error && authStep === 'connected' && (
        <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')}>
            <IconCloseCircle />
          </button>
        </div>
      )}

      {renderAuthUI()}
      {renderConnectedUI()}
    </div>
  )
}
