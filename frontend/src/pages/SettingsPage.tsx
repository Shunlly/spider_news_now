/**
 * HUD 风格系统设置页面
 * HUD-style System Settings Page
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react'
import { HUDPanel, StoneButton, StoneInput, StoneSelect, StoneModal } from '@/components/ui'
import {
  Plus,
  RefreshCw,
  Trash2,
  Check,
  X,
  FlaskConical,
  Star,
  Shield,
  Globe,
  Activity,
} from 'lucide-react'
import {
  credentialsService,
  proxiesService,
  type Credential,
  type CredentialStatus,
  type ProxyConfig,
  type ProxyStatus,
  type ProxyProtocol,
} from '@/services'

const credentialStatusLabels: Record<CredentialStatus, string> = {
  active: '正常',
  inactive: '未激活',
  revoked: '已撤销',
  rate_limited: '限流中',
}

const credentialStatusColors: Record<CredentialStatus, string> = {
  active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  inactive: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
  revoked: 'bg-red-500/20 text-red-400 border border-red-500/30',
  rate_limited: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
}

const proxyStatusLabels: Record<ProxyStatus, string> = {
  active: '正常',
  failed: '失败',
  unknown: '未知',
}

const proxyStatusColors: Record<ProxyStatus, string> = {
  active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  failed: 'bg-red-500/20 text-red-400 border border-red-500/30',
  unknown: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
}

export default function SettingsPage() {
  // 凭证状态
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [credentialsLoading, setCredentialsLoading] = useState(false)
  const [showCredentialModal, setShowCredentialModal] = useState(false)
  const [newCredential, setNewCredential] = useState({
    name: '',
    platform: 'twitter' as 'twitter' | 'telegram',
    credentials: {} as Record<string, string>,
  })

  // 代理状态
  const [proxies, setProxies] = useState<ProxyConfig[]>([])
  const [proxiesLoading, setProxiesLoading] = useState(false)
  const [showProxyModal, setShowProxyModal] = useState(false)
  const [newProxy, setNewProxy] = useState({
    name: '',
    protocol: 'http' as ProxyProtocol,
    host: '',
    port: 80,
    username: '',
    password: '',
  })

  // 测试状态
  const [testingCredentialId, setTestingCredentialId] = useState<number | null>(null)
  const [testingProxyId, setTestingProxyId] = useState<number | null>(null)

  const fetchCredentials = useCallback(async () => {
    setCredentialsLoading(true)
    try {
      const response = await credentialsService.getCredentials()
      setCredentials(response.data)
    } catch (error) {
      console.error('Failed to fetch credentials:', error)
    } finally {
      setCredentialsLoading(false)
    }
  }, [])

  const fetchProxies = useCallback(async () => {
    setProxiesLoading(true)
    try {
      const response = await proxiesService.getProxies()
      setProxies(response.data)
    } catch (error) {
      console.error('Failed to fetch proxies:', error)
    } finally {
      setProxiesLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCredentials()
    fetchProxies()
  }, [fetchCredentials, fetchProxies])

  const handleCreateCredential = async () => {
    try {
      await credentialsService.createCredential(newCredential)
      setShowCredentialModal(false)
      setNewCredential({ name: '', platform: 'twitter', credentials: {} })
      fetchCredentials()
    } catch (error) {
      console.error('Failed to create credential:', error)
    }
  }

  const handleDeleteCredential = async (id: number) => {
    if (!confirm('确定删除此凭证？')) return
    try {
      await credentialsService.deleteCredential(id)
      fetchCredentials()
    } catch (error) {
      console.error('Failed to delete credential:', error)
    }
  }

  const handleTestCredential = async (id: number) => {
    setTestingCredentialId(id)
    try {
      await credentialsService.testCredential(id)
      fetchCredentials()
    } catch (error) {
      console.error('Failed to test credential:', error)
    } finally {
      setTestingCredentialId(null)
    }
  }

  const handleSetDefaultCredential = async (id: number) => {
    try {
      await credentialsService.setDefaultCredential(id)
      fetchCredentials()
    } catch (error) {
      console.error('Failed to set default credential:', error)
    }
  }

  const handleCreateProxy = async () => {
    try {
      await proxiesService.createProxy(newProxy)
      setShowProxyModal(false)
      setNewProxy({ name: '', protocol: 'http', host: '', port: 80, username: '', password: '' })
      fetchProxies()
    } catch (error) {
      console.error('Failed to create proxy:', error)
    }
  }

  const handleDeleteProxy = async (id: number) => {
    if (!confirm('确定删除此代理？')) return
    try {
      await proxiesService.deleteProxy(id)
      fetchProxies()
    } catch (error) {
      console.error('Failed to delete proxy:', error)
    }
  }

  const handleTestProxy = async (id: number) => {
    setTestingProxyId(id)
    try {
      await proxiesService.testProxy(id)
      fetchProxies()
    } catch (error) {
      console.error('Failed to test proxy:', error)
    } finally {
      setTestingProxyId(null)
    }
  }

  const handleToggleProxy = async (proxy: ProxyConfig) => {
    try {
      if (proxy.enabled) {
        await proxiesService.disableProxy(proxy.id)
      } else {
        await proxiesService.enableProxy(proxy.id)
      }
      fetchProxies()
    } catch (error) {
      console.error('Failed to toggle proxy:', error)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-cyan-400 tracking-wide">系统设置</h1>
        <p className="text-slate-500 mt-1 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>配置系统参数和凭证</span>
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 凭证管理 */}
        <HUDPanel
          title="API 凭证"
          subtitle="平台访问令牌"
          color="purple"
          headerAction={
            <div className="flex items-center gap-2">
              <StoneButton
                size="sm"
                variant="secondary"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={fetchCredentials}
                disabled={credentialsLoading}
              />
              <StoneButton
                size="sm"
                icon={<Plus className="w-4 h-4" />}
                onClick={() => setShowCredentialModal(true)}
              >
                添加
              </StoneButton>
            </div>
          }
        >
          {credentialsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>
            </div>
          ) : credentials.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">暂无凭证</p>
              <p className="text-slate-500 text-sm mt-1">点击添加按钮创建新凭证</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {credentials.map((credential) => (
                <div
                  key={credential.id}
                  className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-purple-500/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium text-slate-200">{credential.name}</span>
                        {credential.is_default && (
                          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded ${credentialStatusColors[credential.status]}`}>
                          {credentialStatusLabels[credential.status]}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 font-mono">
                        {credential.platform === 'twitter' ? 'TWITTER' : 'TELEGRAM'} |
                        REQ: <span className="text-cyan-400">{credential.request_count}</span> |
                        ERR: <span className="text-red-400">{credential.error_count}</span>
                      </div>
                      <div className="text-xs text-slate-600 mt-1">
                        LAST: {formatDate(credential.last_used_at)}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {!credential.is_default && (
                        <button
                          onClick={() => handleSetDefaultCredential(credential.id)}
                          className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                          title="设为默认"
                        >
                          <Star className="w-4 h-4 text-slate-500 hover:text-yellow-400" />
                        </button>
                      )}
                      <button
                        onClick={() => handleTestCredential(credential.id)}
                        disabled={testingCredentialId === credential.id}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors disabled:opacity-50"
                        title="测试"
                      >
                        {testingCredentialId === credential.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-400"></div>
                        ) : (
                          <FlaskConical className="w-4 h-4 text-slate-500 hover:text-purple-400" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteCredential(credential.id)}
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
        </HUDPanel>

        {/* 代理管理 */}
        <HUDPanel
          title="代理配置"
          subtitle="网络代理设置"
          color="cyan"
          headerAction={
            <div className="flex items-center gap-2">
              <StoneButton
                size="sm"
                variant="secondary"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={fetchProxies}
                disabled={proxiesLoading}
              />
              <StoneButton
                size="sm"
                icon={<Plus className="w-4 h-4" />}
                onClick={() => setShowProxyModal(true)}
              >
                添加
              </StoneButton>
            </div>
          }
        >
          {proxiesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400"></div>
            </div>
          ) : proxies.length === 0 ? (
            <div className="text-center py-12">
              <Globe className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">暂无代理</p>
              <p className="text-slate-500 text-sm mt-1">点击添加按钮创建新代理</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {proxies.map((proxy) => (
                <div
                  key={proxy.id}
                  className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium text-slate-200">{proxy.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${proxyStatusColors[proxy.status]}`}>
                          {proxyStatusLabels[proxy.status]}
                        </span>
                        {!proxy.enabled && (
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-500 border border-slate-600/30">
                            已禁用
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-cyan-400 font-mono">
                        {proxy.protocol.toUpperCase()}://{proxy.host}:{proxy.port}
                      </div>
                      <div className="text-xs text-slate-500 mt-1 font-mono">
                        OK: <span className="text-emerald-400">{proxy.success_count}</span> /
                        FAIL: <span className="text-red-400">{proxy.failure_count}</span>
                        {proxy.avg_response_time && (
                          <span> | RTT: <span className="text-yellow-400">{proxy.avg_response_time.toFixed(0)}ms</span></span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggleProxy(proxy)}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title={proxy.enabled ? '禁用' : '启用'}
                      >
                        {proxy.enabled ? (
                          <Check className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <X className="w-4 h-4 text-slate-500" />
                        )}
                      </button>
                      <button
                        onClick={() => handleTestProxy(proxy.id)}
                        disabled={testingProxyId === proxy.id}
                        className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors disabled:opacity-50"
                        title="测试"
                      >
                        {testingProxyId === proxy.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cyan-400"></div>
                        ) : (
                          <FlaskConical className="w-4 h-4 text-slate-500 hover:text-cyan-400" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteProxy(proxy.id)}
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
        </HUDPanel>
      </div>

      {/* 添加凭证模态框 */}
      <StoneModal
        open={showCredentialModal}
        onClose={() => setShowCredentialModal(false)}
        title="添加 API 凭证"
        width="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">凭证名称</label>
            <StoneInput
              value={newCredential.name}
              onChange={(e) => setNewCredential({ ...newCredential, name: e.target.value })}
              placeholder="例如: 主账号"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">平台</label>
            <StoneSelect
              value={newCredential.platform}
              onChange={(e) => setNewCredential({
                ...newCredential,
                platform: e.target.value as 'twitter' | 'telegram',
                credentials: {},
              })}
              className="w-full"
            >
              <option value="twitter">Twitter</option>
              <option value="telegram">Telegram</option>
            </StoneSelect>
          </div>
          {newCredential.platform === 'twitter' && (
            <div>
              <label className="block text-sm text-slate-400 mb-2">Bearer Token</label>
              <StoneInput
                type="password"
                value={newCredential.credentials.bearer_token || ''}
                onChange={(e) => setNewCredential({
                  ...newCredential,
                  credentials: { ...newCredential.credentials, bearer_token: e.target.value },
                })}
                placeholder="Twitter API Bearer Token"
              />
            </div>
          )}
          {newCredential.platform === 'telegram' && (
            <div>
              <label className="block text-sm text-slate-400 mb-2">Bot Token</label>
              <StoneInput
                type="password"
                value={newCredential.credentials.bot_token || ''}
                onChange={(e) => setNewCredential({
                  ...newCredential,
                  credentials: { ...newCredential.credentials, bot_token: e.target.value },
                })}
                placeholder="Telegram Bot Token"
              />
            </div>
          )}
          <div className="flex justify-end gap-3 mt-6">
            <StoneButton variant="secondary" onClick={() => setShowCredentialModal(false)}>取消</StoneButton>
            <StoneButton
              onClick={handleCreateCredential}
              disabled={!newCredential.name || Object.keys(newCredential.credentials).length === 0}
            >
              创建
            </StoneButton>
          </div>
        </div>
      </StoneModal>

      {/* 添加代理模态框 */}
      <StoneModal
        open={showProxyModal}
        onClose={() => setShowProxyModal(false)}
        title="添加代理"
        width="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">代理名称</label>
            <StoneInput
              value={newProxy.name}
              onChange={(e) => setNewProxy({ ...newProxy, name: e.target.value })}
              placeholder="例如: 美国代理1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">协议</label>
              <StoneSelect
                value={newProxy.protocol}
                onChange={(e) => setNewProxy({ ...newProxy, protocol: e.target.value as ProxyProtocol })}
                className="w-full"
              >
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
                <option value="socks5">SOCKS5</option>
              </StoneSelect>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">端口</label>
              <StoneInput
                type="number"
                value={newProxy.port.toString()}
                onChange={(e) => setNewProxy({ ...newProxy, port: parseInt(e.target.value) || 80 })}
                placeholder="8080"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">主机地址</label>
            <StoneInput
              value={newProxy.host}
              onChange={(e) => setNewProxy({ ...newProxy, host: e.target.value })}
              placeholder="proxy.example.com"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">用户名（可选）</label>
              <StoneInput
                value={newProxy.username}
                onChange={(e) => setNewProxy({ ...newProxy, username: e.target.value })}
                placeholder="用户名"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">密码（可选）</label>
              <StoneInput
                type="password"
                value={newProxy.password}
                onChange={(e) => setNewProxy({ ...newProxy, password: e.target.value })}
                placeholder="密码"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <StoneButton variant="secondary" onClick={() => setShowProxyModal(false)}>取消</StoneButton>
            <StoneButton
              onClick={handleCreateProxy}
              disabled={!newProxy.name || !newProxy.host}
            >
              创建
            </StoneButton>
          </div>
        </div>
      </StoneModal>
    </div>
  )
}
