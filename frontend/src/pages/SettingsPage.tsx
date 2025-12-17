/**
 * 系统设置页面
 * System Settings Page
 *
 * Stone 色系极简设计
 */

import { useState, useEffect, useCallback } from 'react'
import { StoneCard, StoneButton, StoneInput, StoneSelect, StoneModal } from '@/components/ui'
import {
  Plus,
  RefreshCw,
  Trash2,
  Check,
  X,
  FlaskConical,
  Star,
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
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-stone-100 text-stone-600',
  revoked: 'bg-red-100 text-red-700',
  rate_limited: 'bg-yellow-100 text-yellow-700',
}

const proxyStatusLabels: Record<ProxyStatus, string> = {
  active: '正常',
  failed: '失败',
  unknown: '未知',
}

const proxyStatusColors: Record<ProxyStatus, string> = {
  active: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  unknown: 'bg-stone-100 text-stone-600',
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
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-stone-900">系统设置</h1>
        <p className="text-stone-500 mt-1">配置系统参数和凭证</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 凭证管理 */}
        <StoneCard className="overflow-hidden">
          <div className="p-4 border-b border-stone-200 flex items-center justify-between">
            <h3 className="font-semibold text-stone-900">API 凭证</h3>
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
          </div>

          {credentialsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-stone-900"></div>
            </div>
          ) : credentials.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-stone-500">暂无凭证</p>
              <p className="text-stone-400 text-sm mt-1">点击添加按钮创建新凭证</p>
            </div>
          ) : (
            <div className="divide-y divide-stone-100 max-h-[400px] overflow-y-auto">
              {credentials.map((credential) => (
                <div key={credential.id} className="p-4 hover:bg-stone-50">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-stone-900">{credential.name}</span>
                        {credential.is_default && (
                          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded ${credentialStatusColors[credential.status]}`}>
                          {credentialStatusLabels[credential.status]}
                        </span>
                      </div>
                      <div className="text-xs text-stone-400">
                        {credential.platform === 'twitter' ? 'Twitter' : 'Telegram'} |
                        请求 {credential.request_count} |
                        错误 {credential.error_count}
                      </div>
                      <div className="text-xs text-stone-400 mt-1">
                        最后使用: {formatDate(credential.last_used_at)}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {!credential.is_default && (
                        <button
                          onClick={() => handleSetDefaultCredential(credential.id)}
                          className="p-2 hover:bg-stone-100 rounded-lg"
                          title="设为默认"
                        >
                          <Star className="w-4 h-4 text-stone-400" />
                        </button>
                      )}
                      <button
                        onClick={() => handleTestCredential(credential.id)}
                        disabled={testingCredentialId === credential.id}
                        className="p-2 hover:bg-stone-100 rounded-lg disabled:opacity-50"
                        title="测试"
                      >
                        {testingCredentialId === credential.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-stone-900"></div>
                        ) : (
                          <FlaskConical className="w-4 h-4 text-stone-500" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteCredential(credential.id)}
                        className="p-2 hover:bg-red-50 rounded-lg"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StoneCard>

        {/* 代理管理 */}
        <StoneCard className="overflow-hidden">
          <div className="p-4 border-b border-stone-200 flex items-center justify-between">
            <h3 className="font-semibold text-stone-900">代理配置</h3>
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
          </div>

          {proxiesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-stone-900"></div>
            </div>
          ) : proxies.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-stone-500">暂无代理</p>
              <p className="text-stone-400 text-sm mt-1">点击添加按钮创建新代理</p>
            </div>
          ) : (
            <div className="divide-y divide-stone-100 max-h-[400px] overflow-y-auto">
              {proxies.map((proxy) => (
                <div key={proxy.id} className="p-4 hover:bg-stone-50">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-stone-900">{proxy.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${proxyStatusColors[proxy.status]}`}>
                          {proxyStatusLabels[proxy.status]}
                        </span>
                        {!proxy.enabled && (
                          <span className="text-xs px-2 py-0.5 rounded bg-stone-100 text-stone-500">
                            已禁用
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-stone-400">
                        {proxy.protocol}://{proxy.host}:{proxy.port}
                      </div>
                      <div className="text-xs text-stone-400 mt-1">
                        成功 {proxy.success_count} / 失败 {proxy.failure_count}
                        {proxy.avg_response_time && (
                          <span> | 平均响应 {proxy.avg_response_time.toFixed(0)}ms</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggleProxy(proxy)}
                        className="p-2 hover:bg-stone-100 rounded-lg"
                        title={proxy.enabled ? '禁用' : '启用'}
                      >
                        {proxy.enabled ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <X className="w-4 h-4 text-stone-400" />
                        )}
                      </button>
                      <button
                        onClick={() => handleTestProxy(proxy.id)}
                        disabled={testingProxyId === proxy.id}
                        className="p-2 hover:bg-stone-100 rounded-lg disabled:opacity-50"
                        title="测试"
                      >
                        {testingProxyId === proxy.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-stone-900"></div>
                        ) : (
                          <FlaskConical className="w-4 h-4 text-stone-500" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteProxy(proxy.id)}
                        className="p-2 hover:bg-red-50 rounded-lg"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StoneCard>
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
            <label className="block text-sm text-stone-600 mb-2">凭证名称</label>
            <StoneInput
              value={newCredential.name}
              onChange={(e) => setNewCredential({ ...newCredential, name: e.target.value })}
              placeholder="例如: 主账号"
            />
          </div>
          <div>
            <label className="block text-sm text-stone-600 mb-2">平台</label>
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
              <label className="block text-sm text-stone-600 mb-2">Bearer Token</label>
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
              <label className="block text-sm text-stone-600 mb-2">Bot Token</label>
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
            <label className="block text-sm text-stone-600 mb-2">代理名称</label>
            <StoneInput
              value={newProxy.name}
              onChange={(e) => setNewProxy({ ...newProxy, name: e.target.value })}
              placeholder="例如: 美国代理1"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-stone-600 mb-2">协议</label>
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
              <label className="block text-sm text-stone-600 mb-2">端口</label>
              <StoneInput
                type="number"
                value={newProxy.port.toString()}
                onChange={(e) => setNewProxy({ ...newProxy, port: parseInt(e.target.value) || 80 })}
                placeholder="8080"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-stone-600 mb-2">主机地址</label>
            <StoneInput
              value={newProxy.host}
              onChange={(e) => setNewProxy({ ...newProxy, host: e.target.value })}
              placeholder="proxy.example.com"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-stone-600 mb-2">用户名（可选）</label>
              <StoneInput
                value={newProxy.username}
                onChange={(e) => setNewProxy({ ...newProxy, username: e.target.value })}
                placeholder="用户名"
              />
            </div>
            <div>
              <label className="block text-sm text-stone-600 mb-2">密码（可选）</label>
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
