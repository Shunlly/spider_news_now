/**
 * Telegram 管理页面
 * Telegram Management Page
 *
 * Stone 色系极简设计
 */

import { useState, useEffect, useCallback } from 'react'
import { StoneCard, StoneButton, StoneInput, StoneSelect, useToast } from '@/components/ui'
import {
  Send,
  RefreshCw,
  Plus,
  Trash2,
  MessageSquare,
  User,
  CheckCircle,
  XCircle,
  Loader2,
  Settings,
  Eye,
  Link,
  Search,
  Download,
} from 'lucide-react'
import telegramService, {
  type TelegramDialog,
  type TelegramUserInfo,
  type TelegramEntity,
  type TelegramMessage,
} from '@/services/telegramService'
import { socialService, type SocialSession } from '@/services'
import { getApiErrorMessage } from '@/utils/errorHandler'

type AuthStep = 'init' | 'sendCode' | 'signIn' | 'connected'

// 扩展搜索结果类型，包含 UI 状态
interface SearchResultEntity extends TelegramEntity {
  _alreadyJoined?: boolean
  _justJoined?: boolean
}

export default function TelegramPage() {
  const toast = useToast()
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
  const [searchResults, setSearchResults] = useState<SearchResultEntity[]>([])
  const [searching, setSearching] = useState(false)

  // 消息状态
  const [selectedChannel, setSelectedChannel] = useState<TelegramDialog | null>(null)
  const [messages, setMessages] = useState<TelegramMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)

  // 订阅状态
  const [subscribing, setSubscribing] = useState<number | null>(null)
  const [subscriptions, setSubscriptions] = useState<SocialSession[]>([])
  const [subsLoading, setSubsLoading] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)

  // 加载 Telegram 订阅列表
  const loadSubscriptions = useCallback(async () => {
    setSubsLoading(true)
    try {
      const response = await socialService.getSessions({ platform: 'telegram', page_size: 50 })
      setSubscriptions(response.data)
    } catch (e) {
      console.error('Failed to load subscriptions:', e)
    } finally {
      setSubsLoading(false)
    }
  }, [])

  // 初始化时检查连接状态
  useEffect(() => {
    checkStatus()
    loadSubscriptions()
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    } catch (e) {
      setError(getApiErrorMessage(e, '初始化失败'))
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
    } catch (e) {
      setError(getApiErrorMessage(e, '连接失败'))
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
    } catch (e) {
      setError(getApiErrorMessage(e, '发送验证码失败'))
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
    } catch (e) {
      setError(getApiErrorMessage(e, '登录失败'))
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

  // 搜索频道（支持关键词和用户名）
  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setSearching(true)
    setSearchResults([])
    setError('')

    try {
      const query = searchQuery.trim()

      // 判断是否为用户名格式（以@开头或包含t.me/）
      const isUsername = query.startsWith('@') || query.includes('t.me/') || /^[a-zA-Z][a-zA-Z0-9_]{3,30}$/.test(query)

      if (isUsername) {
        // 精确匹配用户名
        const response = await telegramService.searchChannel(query)
        if (response.success && response.entity) {
          // 标记是否已加入
          const entity = response.entity
          const alreadyJoined = dialogs.some(
            d => d.id === entity.id ||
                 (d.username && entity.username && d.username.toLowerCase() === entity.username.toLowerCase())
          )
          setSearchResults([{ ...entity, _alreadyJoined: alreadyJoined }])
        } else {
          // 用户名搜索失败，尝试关键词搜索
          const publicResponse = await telegramService.searchPublic(query)
          if (publicResponse.success && publicResponse.entities.length > 0) {
            // 标记已加入的频道
            const results = publicResponse.entities.map(entity => {
              const alreadyJoined = dialogs.some(
                d => d.id === entity.id ||
                     (d.username && entity.username && d.username.toLowerCase() === entity.username.toLowerCase())
              )
              return { ...entity, _alreadyJoined: alreadyJoined }
            })
            setSearchResults(results)
          } else {
            setError('未找到相关频道')
          }
        }
      } else {
        // 关键词搜索（支持中文）
        const response = await telegramService.searchPublic(query)
        if (response.success && response.entities.length > 0) {
          // 标记已加入的频道
          const results: SearchResultEntity[] = response.entities.map(entity => {
            const alreadyJoined = dialogs.some(
              d => d.id === entity.id ||
                   (d.username && entity.username && d.username.toLowerCase() === entity.username.toLowerCase())
            )
            return { ...entity, _alreadyJoined: alreadyJoined }
          })
          setSearchResults(results)
        } else {
          setError(response.message || '未找到相关频道')
        }
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '搜索失败'))
    } finally {
      setSearching(false)
    }
  }

  // 加入频道（从搜索结果）
  const handleJoinFromResult = async (entity: TelegramEntity) => {
    setLoading(true)
    setError('')
    try {
      const channel = entity.username || String(entity.id)
      const response = await telegramService.joinChannel(channel)
      if (response.success) {
        // 更新结果列表中的状态
        setSearchResults(prev => prev.map(e =>
          e.id === entity.id ? { ...e, _alreadyJoined: true, _justJoined: true } : e
        ))
        fetchDialogs()
      } else {
        setError(response.message)
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '加入失败'))
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
    } catch (e) {
      setError(getApiErrorMessage(e, '退出失败'))
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

  // 订阅频道
  const handleSubscribe = async (dialog: TelegramDialog) => {
    setSubscribing(dialog.id)
    try {
      const response = await socialService.subscribeTelegramChannel({
        channel_id: dialog.id,
        title: dialog.title,
        username: dialog.username,
        target_type: dialog.type || 'channel',
      })
      if (response.success) {
        toast.success(`已订阅 ${dialog.title}，可在"社交数据"页面查看`)
        loadSubscriptions() // 刷新订阅列表
      } else {
        toast.error(`订阅失败：${response.message || '未知错误'}`)
      }
    } catch (e) {
      toast.error(`订阅失败：${getApiErrorMessage(e)}`)
    } finally {
      setSubscribing(null)
    }
  }

  // 采集订阅数据
  const handleFetchSubscription = async (id: number) => {
    setFetchingId(id)
    try {
      const result = await socialService.fetchSession(id)
      if (result.success) {
        toast.success(`采集完成：新增 ${result.new_count || 0} 条消息`)
        loadSubscriptions()
      } else {
        toast.error(`采集失败：${result.message}`)
      }
    } catch (e) {
      toast.error(`采集失败：${getApiErrorMessage(e)}`)
    } finally {
      setFetchingId(null)
    }
  }

  // 删除订阅
  const handleDeleteSubscription = async (id: number, name: string) => {
    if (!confirm(`确定删除订阅 "${name}"？`)) return
    try {
      await socialService.deleteSession(id)
      loadSubscriptions()
    } catch (e) {
      toast.error(`删除失败：${getApiErrorMessage(e)}`)
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
      <StoneCard className="p-6 max-w-md mx-auto">
        <h2 className="text-lg font-semibold text-stone-900 mb-4">
          {authStep === 'init' && 'Telegram 登录'}
          {authStep === 'sendCode' && '发送验证码'}
          {authStep === 'signIn' && '验证登录'}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {authStep === 'init' && (
            <>
              <div>
                <label className="block text-sm text-stone-600 mb-1">API ID</label>
                <StoneInput
                  value={apiId}
                  onChange={(e) => setApiId(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                />
              </div>
              <div>
                <label className="block text-sm text-stone-600 mb-1">API Hash</label>
                <StoneInput
                  type="password"
                  value={apiHash}
                  onChange={(e) => setApiHash(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                />
              </div>
              {savedSession && (
                <div>
                  <label className="block text-sm text-stone-600 mb-1">已保存的 Session（可选）</label>
                  <StoneInput
                    value={savedSession}
                    onChange={(e) => setSavedSession(e.target.value)}
                    placeholder="之前保存的 StringSession"
                  />
                  <StoneButton
                    className="w-full mt-2"
                    variant="secondary"
                    onClick={handleConnectWithSession}
                    loading={loading}
                  >
                    使用 Session 连接
                  </StoneButton>
                </div>
              )}
              <div className="border-t border-stone-200 pt-4">
                <StoneButton
                  className="w-full"
                  onClick={handleInit}
                  loading={loading}
                >
                  初始化客户端
                </StoneButton>
              </div>
              <p className="text-xs text-stone-400 text-center">
                请先在 <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" className="text-stone-600 hover:underline">my.telegram.org</a> 创建应用获取 API 凭证
              </p>
            </>
          )}

          {authStep === 'sendCode' && (
            <>
              <div>
                <label className="block text-sm text-stone-600 mb-1">手机号码</label>
                <StoneInput
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+86xxxxxxxxx"
                />
              </div>
              <StoneButton
                className="w-full"
                onClick={handleSendCode}
                loading={loading}
              >
                发送验证码
              </StoneButton>
            </>
          )}

          {authStep === 'signIn' && (
            <>
              <div>
                <label className="block text-sm text-stone-600 mb-1">验证码</label>
                <StoneInput
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="输入收到的验证码"
                />
              </div>
              {needPassword && (
                <div>
                  <label className="block text-sm text-stone-600 mb-1">两步验证密码</label>
                  <StoneInput
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="输入两步验证密码"
                  />
                </div>
              )}
              <StoneButton
                className="w-full"
                onClick={handleSignIn}
                loading={loading}
              >
                验证登录
              </StoneButton>
            </>
          )}
        </div>
      </StoneCard>
    )
  }

  // 渲染已连接界面
  const renderConnectedUI = () => {
    if (authStep !== 'connected') return null

    return (
      <div className="space-y-6">
        {/* 用户信息 */}
        <StoneCard className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-stone-900 font-medium">
                    {userInfo?.first_name} {userInfo?.last_name}
                  </span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <span className="text-sm text-stone-500">
                  @{userInfo?.username || userInfo?.phone}
                </span>
              </div>
            </div>
            <StoneButton size="sm" variant="secondary" onClick={handleDisconnect}>
              断开连接
            </StoneButton>
          </div>
        </StoneCard>

        {/* 已订阅列表 */}
        <StoneCard className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-stone-900 font-medium">已订阅频道 ({subscriptions.length})</h3>
            <StoneButton
              size="sm"
              variant="secondary"
              icon={<RefreshCw className="w-4 h-4" />}
              onClick={loadSubscriptions}
              loading={subsLoading}
            />
          </div>
          {subsLoading ? (
            <div className="text-center py-4 text-stone-500">加载中...</div>
          ) : subscriptions.length === 0 ? (
            <div className="text-center py-4 text-stone-500">
              暂无订阅，在下方已加入的频道列表中点击 + 按钮添加
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-3 bg-stone-50 rounded-lg flex items-center justify-between hover:bg-stone-100"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-stone-900 font-medium truncate">{sub.target_name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        sub.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {sub.status === 'active' ? '运行中' : '已暂停'}
                      </span>
                    </div>
                    <div className="text-sm text-stone-500">{sub.target_username || `ID: ${sub.target_id}`}</div>
                    <div className="text-xs text-stone-400 mt-1">
                      {sub.message_count} 条消息 · 采集间隔 {sub.fetch_interval / 60} 分钟
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => handleFetchSubscription(sub.id)}
                      disabled={fetchingId === sub.id}
                      className="p-2 hover:bg-stone-200 rounded-lg transition-colors"
                      title="立即采集"
                    >
                      {fetchingId === sub.id ? (
                        <Loader2 className="w-4 h-4 animate-spin text-stone-500" />
                      ) : (
                        <Download className="w-4 h-4 text-stone-500" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteSubscription(sub.id, sub.target_name)}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除订阅"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StoneCard>

        {/* 搜索频道 */}
        <StoneCard className="p-4">
          <h3 className="text-stone-900 font-medium mb-1">添加订阅</h3>
          <p className="text-stone-500 text-sm mb-3">搜索频道/群组，加入后可在下方列表中点击 + 订阅</p>
          <div className="flex gap-2">
            <StoneInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入关键词（如 香港、财经）或用户名（如 @telegram）"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <StoneButton
              icon={<Search className="w-4 h-4" />}
              onClick={handleSearch}
              loading={searching}
            >
              搜索
            </StoneButton>
          </div>

          {/* 搜索结果列表 */}
          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2 max-h-64 overflow-y-auto">
              <div className="text-sm text-stone-500 mb-2">找到 {searchResults.length} 个结果：</div>
              {searchResults.map((entity) => (
                <div
                  key={entity.id}
                  className={`p-3 rounded-lg flex items-center justify-between ${
                    entity._justJoined ? 'bg-green-50 border border-green-200' :
                    entity._alreadyJoined ? 'bg-yellow-50 border border-yellow-200' :
                    'bg-stone-50 hover:bg-stone-100'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-stone-900 font-medium truncate">{entity.title}</span>
                      {entity._justJoined && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded flex-shrink-0">加入成功</span>
                      )}
                      {entity._alreadyJoined && !entity._justJoined && (
                        <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded flex-shrink-0">已加入</span>
                      )}
                    </div>
                    <div className="text-sm text-stone-500 truncate">
                      {entity.username ? `@${entity.username}` : ''} · {entity.type === 'channel' ? '频道' : entity.type === 'group' ? '群组' : entity.type}
                      {entity.participant_count && ` · ${entity.participant_count.toLocaleString()} 成员`}
                    </div>
                    {entity.description && (
                      <p className="text-sm text-stone-400 mt-1 line-clamp-1">{entity.description}</p>
                    )}
                  </div>
                  {!entity._alreadyJoined && (
                    <StoneButton
                      size="sm"
                      icon={<Plus className="w-4 h-4" />}
                      onClick={() => handleJoinFromResult(entity)}
                      loading={loading}
                      className="ml-2 flex-shrink-0"
                    >
                      加入
                    </StoneButton>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* 推荐频道（搜索无结果时显示） */}
          {searchResults.length === 0 && searchQuery && !searching && (
            <div className="mt-4 p-4 bg-stone-50 rounded-lg">
              <div className="text-sm text-stone-600 mb-3">
                未找到相关频道？试试直接输入频道用户名添加：
              </div>
              <div className="space-y-2">
                <div className="text-xs text-stone-400">
                  示例格式：<code className="bg-stone-200 px-1 rounded">@channelname</code> 或 <code className="bg-stone-200 px-1 rounded">t.me/channelname</code>
                </div>
                <div className="text-xs text-stone-400">
                  可以在 Telegram 应用中找到频道，复制用户名或分享链接粘贴到搜索框
                </div>
              </div>
            </div>
          )}
        </StoneCard>

        {/* 频道列表和消息 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 频道列表 */}
          <StoneCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-stone-900 font-medium">已加入的频道</h3>
              <div className="flex items-center gap-2">
                <StoneSelect
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-24"
                >
                  <option value="">全部</option>
                  <option value="channel">频道</option>
                  <option value="group">群组</option>
                </StoneSelect>
                <StoneButton
                  size="sm"
                  variant="secondary"
                  icon={<RefreshCw className="w-4 h-4" />}
                  onClick={fetchDialogs}
                  loading={dialogsLoading}
                />
              </div>
            </div>

            {dialogsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
              </div>
            ) : dialogs.length === 0 ? (
              <div className="text-center py-8 text-stone-500">
                暂无频道，请搜索并加入
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {dialogs.map((dialog) => (
                  <div
                    key={dialog.id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedChannel?.id === dialog.id
                        ? 'bg-stone-200 border border-stone-300'
                        : 'bg-stone-50 hover:bg-stone-100'
                    }`}
                    onClick={() => fetchMessages(dialog)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-stone-900 font-medium truncate">{dialog.title}</span>
                          {dialog.is_pinned && (
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-1 rounded">置顶</span>
                          )}
                        </div>
                        <div className="text-xs text-stone-500 flex items-center gap-2 mt-1">
                          <span className={`px-1.5 py-0.5 rounded ${
                            dialog.type === 'channel' ? 'bg-blue-100 text-blue-700' :
                            dialog.type === 'group' ? 'bg-green-100 text-green-700' :
                            'bg-stone-100 text-stone-600'
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
                            handleSubscribe(dialog)
                          }}
                          disabled={subscribing === dialog.id}
                          className="p-1.5 hover:bg-stone-200 rounded text-stone-500 opacity-50 hover:opacity-100 transition-opacity"
                          title="订阅到社交数据"
                        >
                          {subscribing === dialog.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Plus className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleLeave(dialog.id)
                          }}
                          className="p-1.5 hover:bg-red-50 rounded text-red-500 opacity-50 hover:opacity-100 transition-opacity"
                          title="退出"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </StoneCard>

          {/* 消息列表 */}
          <StoneCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-stone-900 font-medium">
                {selectedChannel ? selectedChannel.title : '选择频道查看消息'}
              </h3>
              {selectedChannel && (
                <StoneButton
                  size="sm"
                  variant="secondary"
                  icon={<RefreshCw className="w-4 h-4" />}
                  onClick={() => fetchMessages(selectedChannel)}
                  loading={messagesLoading}
                />
              )}
            </div>

            {!selectedChannel ? (
              <div className="text-center py-12 text-stone-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 text-stone-200" />
                <p>点击左侧频道查看消息</p>
              </div>
            ) : messagesLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 text-stone-500">
                暂无消息
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.map((msg) => (
                  <div key={msg.id} className="p-3 bg-stone-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2 text-xs text-stone-400">
                      <span>{formatDate(msg.date)}</span>
                      <div className="flex items-center gap-3">
                        {msg.views && (
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" /> {msg.views.toLocaleString()}
                          </span>
                        )}
                        {msg.forwards && (
                          <span className="flex items-center gap-1">
                            <Send className="w-3 h-3" /> {msg.forwards}
                          </span>
                        )}
                      </div>
                    </div>
                    {msg.text && (
                      <p className="text-stone-700 text-sm whitespace-pre-wrap line-clamp-4">
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
                            className="text-xs text-stone-600 hover:underline flex items-center gap-1"
                          >
                            <Link className="w-3 h-3" /> 链接 {i + 1}
                          </a>
                        ))}
                      </div>
                    )}
                    {msg.media_type && (
                      <span className="inline-block mt-2 text-xs bg-stone-200 text-stone-600 px-2 py-0.5 rounded">
                        {msg.media_type === 'photo' ? '图片' :
                         msg.media_type === 'video' ? '视频' :
                         msg.media_type === 'document' ? '文档' : msg.media_type}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </StoneCard>
        </div>

        {/* StringSession 显示 */}
        {stringSession && (
          <StoneCard className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-stone-900 font-medium flex items-center gap-2">
                <Settings className="w-4 h-4" /> StringSession
              </h3>
              <StoneButton
                size="sm"
                variant="secondary"
                onClick={() => {
                  navigator.clipboard.writeText(stringSession)
                  toast.success('已复制到剪贴板')
                }}
              >
                复制
              </StoneButton>
            </div>
            <p className="text-xs text-stone-400 mb-2">
              请妥善保存此 Session，下次可直接使用它登录，无需重新验证
            </p>
            <div className="bg-stone-100 rounded p-2 text-xs text-stone-600 font-mono break-all max-h-20 overflow-y-auto">
              {stringSession}
            </div>
          </StoneCard>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Telegram 管理</h1>
          <p className="text-stone-500 mt-1">
            {authStep === 'connected'
              ? `已连接 · ${dialogs.length} 个频道`
              : '使用 MTProto API 获取 Telegram 数据'}
          </p>
        </div>
      </div>

      {error && authStep === 'connected' && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')}>
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {renderAuthUI()}
      {renderConnectedUI()}
    </div>
  )
}
