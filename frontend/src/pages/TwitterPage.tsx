/**
 * Twitter 管理页面
 * Twitter Management Page
 *
 * 使用 Cookie 认证获取 Twitter 数据
 * Stone 色系极简设计
 */

import { useState, useEffect, useCallback } from 'react'
import { StoneCard, StoneButton, StoneInput, useToast } from '@/components/ui'
import {
  RefreshCw,
  User,
  CheckCircle,
  XCircle,
  Search,
  Heart,
  MessageCircle,
  Eye,
  Link,
  Play,
  Trash2,
  Download,
} from 'lucide-react'
import twitterService, {
  type TwitterUserInfo,
  type TwitterTweet,
} from '@/services/twitterService'
import { socialService, type SocialSession } from '@/services'
import { getApiErrorMessage } from '@/utils/errorHandler'

type AuthStep = 'init' | 'connected'

export default function TwitterPage() {
  const toast = useToast()
  // 认证状态
  const [authStep, setAuthStep] = useState<AuthStep>('init')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userInfo, setUserInfo] = useState<TwitterUserInfo | null>(null)

  // 认证表单
  const [authToken, setAuthToken] = useState('')
  const [ct0, setCt0] = useState('')
  const [proxy, setProxy] = useState('')

  // 搜索状态
  const [searchQuery, setSearchQuery] = useState('')
  const [searchedUser, setSearchedUser] = useState<TwitterUserInfo | null>(null)
  const [searching, setSearching] = useState(false)

  // 推文状态
  const [tweets, setTweets] = useState<TwitterTweet[]>([])
  const [tweetsLoading, setTweetsLoading] = useState(false)
  const [nextCursor, setNextCursor] = useState<string | undefined>()
  const [includeRetweets, setIncludeRetweets] = useState(false)

  // 搜索推文状态
  const [tweetSearchQuery, setTweetSearchQuery] = useState('')
  const [searchedTweets, setSearchedTweets] = useState<TwitterTweet[]>([])
  const [tweetSearchLoading, setTweetSearchLoading] = useState(false)

  // 订阅状态
  const [subscribing, setSubscribing] = useState(false)
  const [subscriptions, setSubscriptions] = useState<SocialSession[]>([])
  const [subsLoading, setSubsLoading] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)

  // 初始化时检查连接状态
  useEffect(() => {
    checkStatus()
    loadSubscriptions()
    // 从 localStorage 加载保存的配置
    const saved = localStorage.getItem('twitter_config')
    if (saved) {
      try {
        const config = JSON.parse(saved)
        setAuthToken(config.auth_token || '')
        setCt0(config.ct0 || '')
        setProxy(config.proxy || '')
      } catch (e) {
        console.error('Failed to load saved config:', e)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 加载 Twitter 订阅列表
  const loadSubscriptions = useCallback(async () => {
    setSubsLoading(true)
    try {
      const response = await socialService.getSessions({ platform: 'twitter', page_size: 50 })
      setSubscriptions(response.data)
    } catch (e) {
      console.error('Failed to load subscriptions:', e)
    } finally {
      setSubsLoading(false)
    }
  }, [])

  const checkStatus = async () => {
    try {
      const response = await twitterService.getStatus()
      if (response.connected && response.user_info) {
        setUserInfo(response.user_info)
        setAuthStep('connected')
      }
    } catch (e) {
      console.error('Failed to check status:', e)
    }
  }

  // 使用 Cookie 连接
  const handleConnect = async () => {
    if (!authToken || !ct0) {
      setError('请填写 auth_token 和 ct0')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await twitterService.connect({
        auth_token: authToken,
        ct0: ct0,
        proxy: proxy || undefined,
      })

      if (response.success && response.user_info) {
        setUserInfo(response.user_info)
        setAuthStep('connected')
        // 保存配置
        localStorage.setItem('twitter_config', JSON.stringify({
          auth_token: authToken,
          ct0: ct0,
          proxy: proxy,
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

  // 断开连接
  const handleDisconnect = async () => {
    try {
      await twitterService.disconnect()
      setUserInfo(null)
      setAuthStep('init')
      setSearchedUser(null)
      setTweets([])
      setSearchedTweets([])
    } catch (e) {
      console.error('Disconnect failed:', e)
    }
  }

  // 搜索用户
  const handleSearchUser = async () => {
    if (!searchQuery.trim()) return

    setSearching(true)
    setError('')
    setSearchedUser(null)
    setTweets([])

    try {
      const response = await twitterService.getUser(searchQuery.trim().replace('@', ''))

      if (response.success && response.user) {
        setSearchedUser(response.user)
      } else {
        setError(response.message || '用户不存在')
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '搜索失败'))
    } finally {
      setSearching(false)
    }
  }

  // 获取用户推文
  const fetchTweets = async (loadMore = false) => {
    if (!searchedUser) return

    setTweetsLoading(true)

    try {
      const response = await twitterService.getTweets({
        user_id: searchedUser.id,
        count: 20,
        cursor: loadMore ? nextCursor : undefined,
        include_retweets: includeRetweets,
      })

      if (response.success) {
        if (loadMore) {
          setTweets(prev => [...prev, ...response.tweets])
        } else {
          setTweets(response.tweets)
        }
        setNextCursor(response.next_cursor)
      } else {
        setError(response.message)
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '获取推文失败'))
    } finally {
      setTweetsLoading(false)
    }
  }

  // 搜索推文
  const handleSearchTweets = async () => {
    if (!tweetSearchQuery.trim()) return

    setTweetSearchLoading(true)
    setError('')
    setSearchedTweets([])

    try {
      const response = await twitterService.searchTweets({
        query: tweetSearchQuery.trim(),
        count: 30,
      })

      if (response.success) {
        setSearchedTweets(response.tweets)
      } else {
        setError(response.message || '搜索失败')
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '搜索失败'))
    } finally {
      setTweetSearchLoading(false)
    }
  }

  // 订阅用户
  const handleSubscribe = async () => {
    if (!searchedUser) return

    setSubscribing(true)
    setError('')

    try {
      const response = await socialService.subscribeTwitterUser({
        user_id: searchedUser.id,
        screen_name: searchedUser.screen_name || '',
        name: searchedUser.name || searchedUser.screen_name || '',
      })

      if (response.success) {
        toast.success(`已订阅 @${searchedUser.screen_name}，可在"社交数据"页面查看`)
        loadSubscriptions() // 刷新订阅列表
      } else {
        setError(response.message || '订阅失败')
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '订阅失败'))
    } finally {
      setSubscribing(false)
    }
  }

  // 采集订阅数据
  const handleFetchSubscription = async (id: number) => {
    setFetchingId(id)
    try {
      const result = await socialService.fetchSession(id)
      if (result.success) {
        toast.success(`采集完成：新增 ${result.new_count || 0} 条数据`)
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

  // 格式化数字
  const formatNumber = (num?: number | string) => {
    if (!num) return '0'
    const n = typeof num === 'string' ? parseInt(num) : num
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
    return n.toString()
  }

  // 渲染推文卡片
  const renderTweet = (tweet: TwitterTweet) => (
    <div key={tweet.id} className="p-4 bg-stone-50 rounded-lg hover:bg-stone-100 transition-colors">
      {/* 用户信息 */}
      {tweet.user && (
        <div className="flex items-center gap-2 mb-2">
          {tweet.user.profile_image_url ? (
            <img
              src={tweet.user.profile_image_url}
              alt=""
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
          )}
          <div>
            <div className="text-stone-900 text-sm font-medium">{tweet.user.name}</div>
            <div className="text-stone-500 text-xs">@{tweet.user.screen_name}</div>
          </div>
          {tweet.is_retweet && (
            <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
              转推
            </span>
          )}
        </div>
      )}

      {/* 推文内容 */}
      <p className="text-stone-700 text-sm whitespace-pre-wrap mb-3 line-clamp-6">
        {tweet.text}
      </p>

      {/* 媒体 */}
      {tweet.media && tweet.media.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {tweet.media.map((m, i) => (
            <div key={i} className="relative">
              {m.type === 'photo' && m.url && (
                <a href={m.url} target="_blank" rel="noopener noreferrer">
                  <img
                    src={m.url}
                    alt=""
                    className="h-24 rounded-lg object-cover"
                  />
                </a>
              )}
              {(m.type === 'video' || m.type === 'animated_gif') && (
                <a
                  href={m.video_url || m.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded"
                >
                  <Play className="w-3 h-3" />
                  {m.type === 'video' ? '视频' : 'GIF'}
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 链接 */}
      {tweet.urls && tweet.urls.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {tweet.urls.slice(0, 3).map((url, i) => (
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

      {/* 互动数据 */}
      <div className="flex items-center gap-4 text-xs text-stone-400">
        {tweet.created_at && (
          <span>{tweet.created_at}</span>
        )}
        <span className="flex items-center gap-1">
          <Heart className="w-3 h-3" /> {formatNumber(tweet.favorite_count)}
        </span>
        <span className="flex items-center gap-1">
          <RefreshCw className="w-3 h-3" /> {formatNumber(tweet.retweet_count)}
        </span>
        <span className="flex items-center gap-1">
          <MessageCircle className="w-3 h-3" /> {formatNumber(tweet.reply_count)}
        </span>
        {tweet.views_count && (
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" /> {formatNumber(tweet.views_count)}
          </span>
        )}
      </div>
    </div>
  )

  // 渲染认证界面
  const renderAuthUI = () => {
    if (authStep === 'connected') return null

    return (
      <StoneCard className="p-6 max-w-lg mx-auto">
        <h2 className="text-lg font-semibold text-stone-900 mb-4">Twitter 登录</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-stone-600 mb-1">auth_token</label>
            <StoneInput
              value={authToken}
              onChange={(e) => setAuthToken(e.target.value)}
              placeholder="从浏览器 Cookie 获取"
            />
          </div>
          <div>
            <label className="block text-sm text-stone-600 mb-1">ct0</label>
            <StoneInput
              value={ct0}
              onChange={(e) => setCt0(e.target.value)}
              placeholder="从浏览器 Cookie 获取"
            />
          </div>
          <div>
            <label className="block text-sm text-stone-600 mb-1">代理地址（可选）</label>
            <StoneInput
              value={proxy}
              onChange={(e) => setProxy(e.target.value)}
              placeholder="http://127.0.0.1:7890"
            />
          </div>

          <StoneButton
            className="w-full"
            onClick={handleConnect}
            loading={loading}
          >
            连接 Twitter
          </StoneButton>

          <div className="p-4 bg-stone-50 rounded-lg">
            <h4 className="text-sm text-stone-700 font-medium mb-2">如何获取 Cookie？</h4>
            <ol className="text-xs text-stone-500 space-y-1 list-decimal list-inside">
              <li>在浏览器中登录 <a href="https://x.com" target="_blank" rel="noopener noreferrer" className="text-stone-700 hover:underline">x.com</a></li>
              <li>按 F12 打开开发者工具</li>
              <li>切换到 Application（应用程序）选项卡</li>
              <li>在左侧找到 Cookies → https://x.com</li>
              <li>找到并复制 <code className="bg-stone-200 px-1 rounded">auth_token</code> 的值</li>
              <li>找到并复制 <code className="bg-stone-200 px-1 rounded">ct0</code> 的值</li>
            </ol>
          </div>
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
              {userInfo?.profile_image_url ? (
                <img
                  src={userInfo.profile_image_url}
                  alt=""
                  className="w-12 h-12 rounded-full"
                />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-stone-900 font-medium">{userInfo?.name}</span>
                  <CheckCircle className="w-4 h-4 text-blue-500" />
                </div>
                <span className="text-sm text-stone-500">
                  @{userInfo?.screen_name}
                </span>
                <div className="text-xs text-stone-400 mt-1 flex gap-3">
                  <span>{formatNumber(userInfo?.followers_count)} 粉丝</span>
                  <span>{formatNumber(userInfo?.friends_count)} 关注</span>
                  <span>{formatNumber(userInfo?.statuses_count)} 推文</span>
                </div>
              </div>
            </div>
            <StoneButton size="sm" variant="secondary" onClick={handleDisconnect}>
              断开连接
            </StoneButton>
          </div>
        </StoneCard>

        {/* 搜索用户并订阅 */}
        <StoneCard className="p-4">
          <h3 className="text-stone-900 font-medium mb-1">添加订阅</h3>
          <p className="text-stone-500 text-sm mb-3">搜索 Twitter 用户，订阅后自动采集其推文</p>
          <div className="flex gap-2">
            <StoneInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="输入用户名（如 elonmusk）或 @用户名"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchUser()}
              className="flex-1"
            />
            <StoneButton
              icon={<Search className="w-4 h-4" />}
              onClick={handleSearchUser}
              loading={searching}
            >
              搜索
            </StoneButton>
          </div>

          {/* 搜索到的用户 */}
          {searchedUser && (
            <div className="mt-4 p-4 bg-stone-50 rounded-lg">
              <div className="flex items-center gap-3">
                {searchedUser.profile_image_url ? (
                  <img
                    src={searchedUser.profile_image_url}
                    alt=""
                    className="w-14 h-14 rounded-full"
                  />
                ) : (
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                    <User className="w-7 h-7 text-white" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-stone-900 font-medium">{searchedUser.name}</span>
                    {searchedUser.verified && (
                      <CheckCircle className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                  <div className="text-sm text-stone-500">@{searchedUser.screen_name}</div>
                  {searchedUser.description && (
                    <p className="text-xs text-stone-400 mt-1 line-clamp-2">
                      {searchedUser.description}
                    </p>
                  )}
                  <div className="text-xs text-stone-400 mt-2 flex gap-3">
                    <span>{formatNumber(searchedUser.followers_count)} 粉丝</span>
                    <span>{formatNumber(searchedUser.friends_count)} 关注</span>
                    <span>{formatNumber(searchedUser.statuses_count)} 推文</span>
                    {searchedUser.media_count && (
                      <span>{formatNumber(searchedUser.media_count)} 媒体</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <StoneButton
                  size="sm"
                  onClick={() => fetchTweets(false)}
                  loading={tweetsLoading}
                >
                  获取推文
                </StoneButton>
                <StoneButton
                  size="sm"
                  variant="secondary"
                  onClick={handleSubscribe}
                  loading={subscribing}
                >
                  订阅此用户
                </StoneButton>
                <label className="flex items-center gap-2 text-sm text-stone-600 ml-auto">
                  <input
                    type="checkbox"
                    checked={includeRetweets}
                    onChange={(e) => setIncludeRetweets(e.target.checked)}
                    className="rounded border-stone-300"
                  />
                  包含转推
                </label>
              </div>
            </div>
          )}
        </StoneCard>

        {/* 用户推文列表 */}
        {tweets.length > 0 && (
          <StoneCard className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-stone-900 font-medium">
                {searchedUser?.name} 的推文 ({tweets.length})
              </h3>
              <StoneButton
                size="sm"
                variant="secondary"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={() => fetchTweets(false)}
                loading={tweetsLoading}
              />
            </div>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {tweets.map(tweet => renderTweet(tweet))}
            </div>
            {nextCursor && (
              <StoneButton
                className="w-full mt-4"
                variant="secondary"
                onClick={() => fetchTweets(true)}
                loading={tweetsLoading}
              >
                加载更多
              </StoneButton>
            )}
          </StoneCard>
        )}

        {/* 已订阅列表 */}
        <StoneCard className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-stone-900 font-medium">已订阅用户 ({subscriptions.length})</h3>
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
              暂无订阅，搜索用户后点击"订阅此用户"添加
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
                    <div className="text-sm text-stone-500">{sub.target_username}</div>
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
                        <div className="w-4 h-4 border-2 border-stone-300 border-t-stone-900 rounded-full animate-spin" />
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

        {/* 搜索推文 */}
        <StoneCard className="p-4">
          <h3 className="text-stone-900 font-medium mb-3">搜索推文</h3>
          <div className="flex gap-2">
            <StoneInput
              value={tweetSearchQuery}
              onChange={(e) => setTweetSearchQuery(e.target.value)}
              placeholder="输入关键词搜索推文"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchTweets()}
              className="flex-1"
            />
            <StoneButton
              icon={<Search className="w-4 h-4" />}
              onClick={handleSearchTweets}
              loading={tweetSearchLoading}
            >
              搜索
            </StoneButton>
          </div>

          {/* 搜索结果 */}
          {searchedTweets.length > 0 && (
            <div className="mt-4 space-y-3 max-h-[400px] overflow-y-auto">
              <div className="text-sm text-stone-500">找到 {searchedTweets.length} 条推文</div>
              {searchedTweets.map(tweet => renderTweet(tweet))}
            </div>
          )}
        </StoneCard>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Twitter 管理</h1>
          <p className="text-stone-500 mt-1">
            {authStep === 'connected'
              ? `已连接 @${userInfo?.screen_name}`
              : '使用 Cookie 认证获取 Twitter 数据'}
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
