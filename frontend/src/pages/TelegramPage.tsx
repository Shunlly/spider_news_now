/**
 * HUD 风格 Telegram 管理页面
 * HUD-style Telegram Management Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react'
import { HUDPanel, StoneButton, StoneSelect, useToast } from '@/components/ui'
import {
  Send,
  RefreshCw,
  Plus,
  Trash2,
  MessageSquare,
  User,
  CheckCircle,
  XCircle,
  Settings,
  Eye,
  Link,
  Search,
  Download,
  Activity,
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
      <HUDPanel title="Telegram 登录" subtitle="MTProto API" color="cyan" className="max-w-lg mx-auto">
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {authStep === 'init' && (
            <>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">API ID</label>
                <input
                  value={apiId}
                  onChange={(e) => setApiId(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">API Hash</label>
                <input
                  type="password"
                  value={apiHash}
                  onChange={(e) => setApiHash(e.target.value)}
                  placeholder="从 my.telegram.org 获取"
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              {savedSession && (
                <div>
                  <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">已保存的 Session</label>
                  <input
                    value={savedSession}
                    onChange={(e) => setSavedSession(e.target.value)}
                    placeholder="之前保存的 StringSession"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
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
              <div className="border-t border-slate-700/50 pt-4">
                <StoneButton
                  className="w-full"
                  onClick={handleInit}
                  loading={loading}
                >
                  <Send className="w-4 h-4 mr-2" />初始化客户端
                </StoneButton>
              </div>
              <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
                <h4 className="text-sm text-slate-300 font-medium mb-2">如何获取 API 凭证？</h4>
                <ol className="text-xs text-slate-500 space-y-1 list-decimal list-inside">
                  <li>访问 <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">my.telegram.org</a></li>
                  <li>登录你的 Telegram 账号</li>
                  <li>进入 API development tools</li>
                  <li>创建应用并获取 <code className="bg-slate-700 px-1 rounded text-cyan-400">api_id</code> 和 <code className="bg-slate-700 px-1 rounded text-cyan-400">api_hash</code></li>
                </ol>
              </div>
            </>
          )}

          {authStep === 'sendCode' && (
            <>
              <div>
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">手机号码</label>
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+86xxxxxxxxx"
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
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
                <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">验证码</label>
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="输入收到的验证码"
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              {needPassword && (
                <div>
                  <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">两步验证密码</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="输入两步验证密码"
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
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
      </HUDPanel>
    )
  }

  // 渲染已连接界面
  const renderConnectedUI = () => {
    if (authStep !== 'connected') return null

    return (
      <div className="space-y-6">
        {/* 用户信息 */}
        <HUDPanel color="cyan">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/30 to-blue-500/30 rounded-full flex items-center justify-center border border-cyan-500/30">
                <User className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-200 font-medium">
                    {userInfo?.first_name} {userInfo?.last_name}
                  </span>
                  <CheckCircle className="w-4 h-4 text-cyan-400" />
                </div>
                <span className="text-sm text-slate-500 font-mono">
                  @{userInfo?.username || userInfo?.phone}
                </span>
              </div>
            </div>
            <StoneButton size="sm" variant="secondary" onClick={handleDisconnect}>
              断开连接
            </StoneButton>
          </div>
        </HUDPanel>

        {/* 已订阅列表 */}
        <HUDPanel title="已订阅频道" subtitle={`${subscriptions.length} 个`} color="green"
          headerAction={<StoneButton size="sm" variant="secondary" icon={<RefreshCw className="w-4 h-4" />} onClick={loadSubscriptions} loading={subsLoading} />}>
          {subsLoading ? (
            <div className="text-center py-4"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-400 mx-auto"></div></div>
          ) : subscriptions.length === 0 ? (
            <div className="text-center py-8 text-slate-500">暂无订阅，在下方已加入的频道列表中点击 + 按钮添加</div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50 flex items-center justify-between hover:border-emerald-500/30 transition-all"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-medium truncate">{sub.target_name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        sub.status === 'active' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                      }`}>
                        {sub.status === 'active' ? 'ACTIVE' : 'PAUSED'}
                      </span>
                    </div>
                    <div className="text-sm text-slate-500 font-mono">{sub.target_username || `ID: ${sub.target_id}`}</div>
                    <div className="text-xs text-slate-600 mt-1 font-mono">
                      {sub.message_count} MSG · {sub.fetch_interval / 60}m INTERVAL
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => handleFetchSubscription(sub.id)}
                      disabled={fetchingId === sub.id}
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="立即采集"
                    >
                      {fetchingId === sub.id ? (
                        <div className="w-4 h-4 border-2 border-slate-600 border-t-emerald-400 rounded-full animate-spin" />
                      ) : (
                        <Download className="w-4 h-4 text-slate-500 hover:text-emerald-400" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteSubscription(sub.id, sub.target_name)}
                      className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                      title="删除订阅"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </HUDPanel>

        {/* 搜索频道 */}
        <HUDPanel title="添加订阅" subtitle="搜索并加入频道" color="purple">
          <div className="flex gap-2">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入关键词（如 香港、财经）或用户名（如 @telegram）"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50"
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
              <div className="text-sm text-slate-500">找到 <span className="text-purple-400 font-mono">{searchResults.length}</span> 个结果：</div>
              {searchResults.map((entity, index) => (
                <div
                  key={entity.id}
                  className={`p-3 rounded-lg flex items-center justify-between border ${
                    entity._justJoined ? 'bg-emerald-500/10 border-emerald-500/30' :
                    entity._alreadyJoined ? 'bg-yellow-500/10 border-yellow-500/30' :
                    'bg-slate-800/30 border-slate-700/50 hover:border-purple-500/30'
                  }`}
                  style={{ animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both` }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-medium truncate">{entity.title}</span>
                      {entity._justJoined && (
                        <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded flex-shrink-0">SUCCESS</span>
                      )}
                      {entity._alreadyJoined && !entity._justJoined && (
                        <span className="text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded flex-shrink-0">JOINED</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 truncate font-mono">
                      {entity.username ? `@${entity.username}` : ''} · {entity.type === 'channel' ? 'CHANNEL' : entity.type === 'group' ? 'GROUP' : entity.type?.toUpperCase()}
                      {entity.participant_count && ` · ${entity.participant_count.toLocaleString()} MEMBERS`}
                    </div>
                    {entity.description && (
                      <p className="text-sm text-slate-600 mt-1 line-clamp-1">{entity.description}</p>
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

          {/* 推荐提示 */}
          {searchResults.length === 0 && searchQuery && !searching && (
            <div className="mt-4 p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
              <div className="text-sm text-slate-400 mb-3">
                未找到相关频道？试试直接输入频道用户名添加：
              </div>
              <div className="space-y-2">
                <div className="text-xs text-slate-500">
                  示例格式：<code className="bg-slate-700 px-1 rounded text-cyan-400">@channelname</code> 或 <code className="bg-slate-700 px-1 rounded text-cyan-400">t.me/channelname</code>
                </div>
              </div>
            </div>
          )}
        </HUDPanel>

        {/* 频道列表和消息 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 频道列表 */}
          <HUDPanel title="已加入的频道" subtitle={`${dialogs.length} 个`} color="blue"
            headerAction={
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
            }>
            {dialogsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
              </div>
            ) : dialogs.length === 0 ? (
              <div className="text-center py-8 text-slate-500">暂无频道，请搜索并加入</div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {dialogs.map((dialog, index) => (
                  <div
                    key={dialog.id}
                    className={`p-3 rounded-lg cursor-pointer transition-all border ${
                      selectedChannel?.id === dialog.id
                        ? 'bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                        : 'bg-slate-800/30 border-slate-700/50 hover:border-blue-500/30'
                    }`}
                    onClick={() => fetchMessages(dialog)}
                    style={{ animation: `fadeInUp 0.3s ease-out ${index * 0.03}s both` }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-200 font-medium truncate">{dialog.title}</span>
                          {dialog.is_pinned && (
                            <span className="text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-1 rounded">PIN</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-2 mt-1 font-mono">
                          <span className={`px-1.5 py-0.5 rounded ${
                            dialog.type === 'channel' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                            dialog.type === 'group' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                            'bg-slate-700/50 text-slate-400'
                          }`}>
                            {dialog.type === 'channel' ? 'CH' : dialog.type === 'group' ? 'GP' : 'DM'}
                          </span>
                          {dialog.participant_count && (
                            <span>{dialog.participant_count.toLocaleString()} MEMBERS</span>
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
                          className="p-1.5 hover:bg-slate-700/50 rounded text-slate-500 hover:text-cyan-400 transition-colors"
                          title="订阅到社交数据"
                        >
                          {subscribing === dialog.id ? (
                            <div className="w-4 h-4 border-2 border-slate-600 border-t-cyan-400 rounded-full animate-spin" />
                          ) : (
                            <Plus className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleLeave(dialog.id)
                          }}
                          className="p-1.5 hover:bg-red-500/20 rounded text-red-400 opacity-50 hover:opacity-100 transition-opacity"
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
          </HUDPanel>

          {/* 消息列表 */}
          <HUDPanel
            title={selectedChannel ? selectedChannel.title : '消息预览'}
            subtitle="实时数据"
            color="purple"
            headerAction={selectedChannel && (
              <StoneButton
                size="sm"
                variant="secondary"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={() => fetchMessages(selectedChannel)}
                loading={messagesLoading}
              />
            )}>
            {!selectedChannel ? (
              <div className="text-center py-12 text-slate-500">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 text-slate-700" />
                <p>点击左侧频道查看消息</p>
              </div>
            ) : messagesLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-400"></div>
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 text-slate-500">暂无消息</div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.map((msg, index) => (
                  <div
                    key={msg.id}
                    className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50"
                    style={{ animation: `fadeInUp 0.3s ease-out ${index * 0.02}s both` }}
                  >
                    <div className="flex items-center justify-between mb-2 text-xs text-slate-500 font-mono">
                      <span>{formatDate(msg.date)}</span>
                      <div className="flex items-center gap-3">
                        {msg.views && (
                          <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3 text-purple-400" /> <span className="text-purple-400">{msg.views.toLocaleString()}</span>
                          </span>
                        )}
                        {msg.forwards && (
                          <span className="flex items-center gap-1">
                            <Send className="w-3 h-3 text-cyan-400" /> <span className="text-cyan-400">{msg.forwards}</span>
                          </span>
                        )}
                      </div>
                    </div>
                    {msg.text && (
                      <p className="text-slate-300 text-sm whitespace-pre-wrap line-clamp-4">
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
                            className="text-xs text-cyan-400 hover:underline flex items-center gap-1"
                          >
                            <Link className="w-3 h-3" /> LINK
                          </a>
                        ))}
                      </div>
                    )}
                    {msg.media_type && (
                      <span className="inline-block mt-2 text-xs bg-slate-700/50 text-slate-400 px-2 py-0.5 rounded border border-slate-600/50">
                        {msg.media_type === 'photo' ? 'PHOTO' :
                         msg.media_type === 'video' ? 'VIDEO' :
                         msg.media_type === 'document' ? 'DOC' : msg.media_type.toUpperCase()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </HUDPanel>
        </div>

        {/* StringSession 显示 */}
        {stringSession && (
          <HUDPanel title="StringSession" color="cyan"
            headerAction={
              <StoneButton
                size="sm"
                variant="secondary"
                icon={<Settings className="w-4 h-4" />}
                onClick={() => {
                  navigator.clipboard.writeText(stringSession)
                  toast.success('已复制到剪贴板')
                }}
              >
                复制
              </StoneButton>
            }>
            <p className="text-xs text-slate-500 mb-2">
              请妥善保存此 Session，下次可直接使用它登录，无需重新验证
            </p>
            <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-cyan-400 font-mono break-all max-h-20 overflow-y-auto border border-slate-700/50">
              {stringSession}
            </div>
          </HUDPanel>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wide flex items-center gap-2">
            <Send className="w-6 h-6" /> Telegram 管理
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>{authStep === 'connected'
              ? `已连接 · ${dialogs.length} 个频道`
              : 'MTProto API 获取数据'}</span>
          </p>
        </div>
      </div>

      {error && authStep === 'connected' && (
        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')}>
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {renderAuthUI()}
      {renderConnectedUI()}

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
