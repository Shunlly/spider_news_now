/**
 * HUD 风格 Twitter 管理页面
 * HUD-style Twitter Management Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react'
import { HUDPanel, StoneButton, useToast } from '@/components/ui'
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
  Activity,
  Twitter,
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
  const [authStep, setAuthStep] = useState<AuthStep>('init')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userInfo, setUserInfo] = useState<TwitterUserInfo | null>(null)

  const [authToken, setAuthToken] = useState('')
  const [ct0, setCt0] = useState('')
  const [proxy, setProxy] = useState('')

  const [searchQuery, setSearchQuery] = useState('')
  const [searchedUser, setSearchedUser] = useState<TwitterUserInfo | null>(null)
  const [searching, setSearching] = useState(false)

  const [tweets, setTweets] = useState<TwitterTweet[]>([])
  const [tweetsLoading, setTweetsLoading] = useState(false)
  const [nextCursor, setNextCursor] = useState<string | undefined>()
  const [includeRetweets, setIncludeRetweets] = useState(false)

  const [tweetSearchQuery, setTweetSearchQuery] = useState('')
  const [searchedTweets, setSearchedTweets] = useState<TwitterTweet[]>([])
  const [tweetSearchLoading, setTweetSearchLoading] = useState(false)

  const [subscribing, setSubscribing] = useState(false)
  const [subscriptions, setSubscriptions] = useState<SocialSession[]>([])
  const [subsLoading, setSubsLoading] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)

  useEffect(() => {
    checkStatus()
    loadSubscriptions()
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
        localStorage.setItem('twitter_config', JSON.stringify({ auth_token: authToken, ct0, proxy }))
      } else {
        setError(response.message)
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '连接失败'))
    } finally {
      setLoading(false)
    }
  }

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

  const handleSearchTweets = async () => {
    if (!tweetSearchQuery.trim()) return
    setTweetSearchLoading(true)
    setError('')
    setSearchedTweets([])
    try {
      const response = await twitterService.searchTweets({ query: tweetSearchQuery.trim(), count: 30 })
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
        toast.success(`已订阅 @${searchedUser.screen_name}`)
        loadSubscriptions()
      } else {
        setError(response.message || '订阅失败')
      }
    } catch (e) {
      setError(getApiErrorMessage(e, '订阅失败'))
    } finally {
      setSubscribing(false)
    }
  }

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

  const handleDeleteSubscription = async (id: number, name: string) => {
    if (!confirm(`确定删除订阅 "${name}"？`)) return
    try {
      await socialService.deleteSession(id)
      loadSubscriptions()
    } catch (e) {
      toast.error(`删除失败：${getApiErrorMessage(e)}`)
    }
  }

  const formatNumber = (num?: number | string) => {
    if (!num) return '0'
    const n = typeof num === 'string' ? parseInt(num) : num
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
    return n.toString()
  }

  const renderTweet = (tweet: TwitterTweet, index: number) => (
    <div
      key={tweet.id}
      className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50 hover:border-blue-500/30 transition-all"
      style={{ animation: `fadeInUp 0.3s ease-out ${index * 0.02}s both` }}
    >
      {tweet.user && (
        <div className="flex items-center gap-2 mb-3">
          {tweet.user.profile_image_url ? (
            <img src={tweet.user.profile_image_url} alt="" className="w-8 h-8 rounded-full" />
          ) : (
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
          )}
          <div>
            <div className="text-slate-200 text-sm font-medium">{tweet.user.name}</div>
            <div className="text-slate-500 text-xs font-mono">@{tweet.user.screen_name}</div>
          </div>
          {tweet.is_retweet && (
            <span className="ml-auto text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">
              RT
            </span>
          )}
        </div>
      )}
      <p className="text-slate-300 text-sm whitespace-pre-wrap mb-3 line-clamp-6">{tweet.text}</p>
      {tweet.media && tweet.media.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {tweet.media.map((m, i) => (
            <div key={i}>
              {m.type === 'photo' && m.url && (
                <a href={m.url} target="_blank" rel="noopener noreferrer">
                  <img src={m.url} alt="" className="h-20 rounded-lg object-cover opacity-80 hover:opacity-100 transition-opacity" />
                </a>
              )}
              {(m.type === 'video' || m.type === 'animated_gif') && (
                <a href={m.video_url || m.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-1 rounded">
                  <Play className="w-3 h-3" />
                  {m.type === 'video' ? 'VIDEO' : 'GIF'}
                </a>
              )}
            </div>
          ))}
        </div>
      )}
      {tweet.urls && tweet.urls.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {tweet.urls.slice(0, 3).map((url, i) => (
            <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
              <Link className="w-3 h-3" /> LINK
            </a>
          ))}
        </div>
      )}
      <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
        {tweet.created_at && <span>{tweet.created_at}</span>}
        <span className="flex items-center gap-1"><Heart className="w-3 h-3 text-pink-400" /> {formatNumber(tweet.favorite_count)}</span>
        <span className="flex items-center gap-1"><RefreshCw className="w-3 h-3 text-emerald-400" /> {formatNumber(tweet.retweet_count)}</span>
        <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3 text-blue-400" /> {formatNumber(tweet.reply_count)}</span>
        {tweet.views_count && <span className="flex items-center gap-1"><Eye className="w-3 h-3 text-purple-400" /> {formatNumber(tweet.views_count)}</span>}
      </div>
    </div>
  )

  const renderAuthUI = () => {
    if (authStep === 'connected') return null
    return (
      <HUDPanel title="Twitter 登录" subtitle="Cookie 认证" color="blue" className="max-w-lg mx-auto">
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">auth_token</label>
            <input value={authToken} onChange={(e) => setAuthToken(e.target.value)} placeholder="从浏览器 Cookie 获取"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">ct0</label>
            <input value={ct0} onChange={(e) => setCt0(e.target.value)} placeholder="从浏览器 Cookie 获取"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-2 uppercase tracking-wider">代理地址（可选）</label>
            <input value={proxy} onChange={(e) => setProxy(e.target.value)} placeholder="http://127.0.0.1:7890"
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50" />
          </div>
          <StoneButton className="w-full" onClick={handleConnect} loading={loading}>
            <Twitter className="w-4 h-4 mr-2" />连接 Twitter
          </StoneButton>
          <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <h4 className="text-sm text-slate-300 font-medium mb-2">如何获取 Cookie？</h4>
            <ol className="text-xs text-slate-500 space-y-1 list-decimal list-inside">
              <li>在浏览器中登录 <a href="https://x.com" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">x.com</a></li>
              <li>按 F12 打开开发者工具</li>
              <li>切换到 Application 选项卡</li>
              <li>找到 Cookies → https://x.com</li>
              <li>复制 <code className="bg-slate-700 px-1 rounded text-cyan-400">auth_token</code> 和 <code className="bg-slate-700 px-1 rounded text-cyan-400">ct0</code></li>
            </ol>
          </div>
        </div>
      </HUDPanel>
    )
  }

  const renderConnectedUI = () => {
    if (authStep !== 'connected') return null
    return (
      <div className="space-y-6">
        <HUDPanel color="blue">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {userInfo?.profile_image_url ? (
                <img src={userInfo.profile_image_url} alt="" className="w-12 h-12 rounded-full border-2 border-blue-500/30" />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-200 font-medium">{userInfo?.name}</span>
                  <CheckCircle className="w-4 h-4 text-blue-400" />
                </div>
                <span className="text-sm text-slate-500 font-mono">@{userInfo?.screen_name}</span>
                <div className="text-xs text-slate-600 mt-1 flex gap-3 font-mono">
                  <span><span className="text-cyan-400">{formatNumber(userInfo?.followers_count)}</span> 粉丝</span>
                  <span><span className="text-purple-400">{formatNumber(userInfo?.friends_count)}</span> 关注</span>
                  <span><span className="text-pink-400">{formatNumber(userInfo?.statuses_count)}</span> 推文</span>
                </div>
              </div>
            </div>
            <StoneButton size="sm" variant="secondary" onClick={handleDisconnect}>断开</StoneButton>
          </div>
        </HUDPanel>

        <HUDPanel title="添加订阅" subtitle="搜索用户自动采集" color="purple">
          <div className="flex gap-2">
            <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="输入用户名（如 elonmusk）"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchUser()}
              className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50" />
            <StoneButton icon={<Search className="w-4 h-4" />} onClick={handleSearchUser} loading={searching}>搜索</StoneButton>
          </div>
          {searchedUser && (
            <div className="mt-4 p-4 bg-slate-800/30 rounded-lg border border-purple-500/30">
              <div className="flex items-center gap-3">
                {searchedUser.profile_image_url ? (
                  <img src={searchedUser.profile_image_url} alt="" className="w-14 h-14 rounded-full" />
                ) : (
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                    <User className="w-7 h-7 text-white" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-200 font-medium">{searchedUser.name}</span>
                    {searchedUser.verified && <CheckCircle className="w-4 h-4 text-blue-400" />}
                  </div>
                  <div className="text-sm text-slate-500 font-mono">@{searchedUser.screen_name}</div>
                  {searchedUser.description && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{searchedUser.description}</p>}
                  <div className="text-xs text-slate-600 mt-2 flex gap-3 font-mono">
                    <span><span className="text-cyan-400">{formatNumber(searchedUser.followers_count)}</span> 粉丝</span>
                    <span><span className="text-purple-400">{formatNumber(searchedUser.friends_count)}</span> 关注</span>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex gap-2 items-center">
                <StoneButton size="sm" onClick={() => fetchTweets(false)} loading={tweetsLoading}>获取推文</StoneButton>
                <StoneButton size="sm" variant="secondary" onClick={handleSubscribe} loading={subscribing}>订阅用户</StoneButton>
                <label className="flex items-center gap-2 text-xs text-slate-500 ml-auto">
                  <input type="checkbox" checked={includeRetweets} onChange={(e) => setIncludeRetweets(e.target.checked)} className="rounded border-slate-600 bg-slate-800" />
                  包含转推
                </label>
              </div>
            </div>
          )}
        </HUDPanel>

        {tweets.length > 0 && (
          <HUDPanel title={`${searchedUser?.name} 的推文`} subtitle={`${tweets.length} 条`} color="cyan"
            headerAction={<StoneButton size="sm" variant="secondary" icon={<RefreshCw className="w-4 h-4" />} onClick={() => fetchTweets(false)} loading={tweetsLoading} />}>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {tweets.map((tweet, i) => renderTweet(tweet, i))}
            </div>
            {nextCursor && <StoneButton className="w-full mt-4" variant="secondary" onClick={() => fetchTweets(true)} loading={tweetsLoading}>加载更多</StoneButton>}
          </HUDPanel>
        )}

        <HUDPanel title="已订阅用户" subtitle={`${subscriptions.length} 个`} color="green"
          headerAction={<StoneButton size="sm" variant="secondary" icon={<RefreshCw className="w-4 h-4" />} onClick={loadSubscriptions} loading={subsLoading} />}>
          {subsLoading ? (
            <div className="text-center py-4"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-400 mx-auto"></div></div>
          ) : subscriptions.length === 0 ? (
            <div className="text-center py-8 text-slate-500">暂无订阅，搜索用户后点击"订阅用户"添加</div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {subscriptions.map((sub) => (
                <div key={sub.id} className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50 flex items-center justify-between hover:border-emerald-500/30 transition-all">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-200 font-medium truncate">{sub.target_name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${sub.status === 'active' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'}`}>
                        {sub.status === 'active' ? 'ACTIVE' : 'PAUSED'}
                      </span>
                    </div>
                    <div className="text-sm text-slate-500 font-mono">@{sub.target_username}</div>
                    <div className="text-xs text-slate-600 mt-1 font-mono">{sub.message_count} MSG · {sub.fetch_interval / 60}m INTERVAL</div>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button onClick={() => handleFetchSubscription(sub.id)} disabled={fetchingId === sub.id} className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors" title="立即采集">
                      {fetchingId === sub.id ? <div className="w-4 h-4 border-2 border-slate-600 border-t-emerald-400 rounded-full animate-spin" /> : <Download className="w-4 h-4 text-slate-500 hover:text-emerald-400" />}
                    </button>
                    <button onClick={() => handleDeleteSubscription(sub.id, sub.target_name)} className="p-2 hover:bg-red-500/20 rounded-lg transition-colors" title="删除">
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </HUDPanel>

        <HUDPanel title="搜索推文" color="cyan">
          <div className="flex gap-2">
            <input value={tweetSearchQuery} onChange={(e) => setTweetSearchQuery(e.target.value)} placeholder="输入关键词搜索推文"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchTweets()}
              className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50" />
            <StoneButton icon={<Search className="w-4 h-4" />} onClick={handleSearchTweets} loading={tweetSearchLoading}>搜索</StoneButton>
          </div>
          {searchedTweets.length > 0 && (
            <div className="mt-4 space-y-3 max-h-[400px] overflow-y-auto">
              <div className="text-sm text-slate-500">找到 <span className="text-cyan-400 font-mono">{searchedTweets.length}</span> 条推文</div>
              {searchedTweets.map((tweet, i) => renderTweet(tweet, i))}
            </div>
          )}
        </HUDPanel>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-blue-400 tracking-wide flex items-center gap-2">
            <Twitter className="w-6 h-6" /> Twitter 管理
          </h1>
          <p className="text-slate-500 mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>{authStep === 'connected' ? `已连接 @${userInfo?.screen_name}` : 'Cookie 认证获取数据'}</span>
          </p>
        </div>
      </div>

      {error && authStep === 'connected' && (
        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')}><XCircle className="w-4 h-4" /></button>
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
