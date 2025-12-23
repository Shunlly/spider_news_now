/**
 * 登录页面
 * Login Page with Stone Design
 *
 * 功能：
 * - 用户名密码表单
 * - 图形验证码
 * - Stone 极简风格
 */

import { useState, useCallback, useEffect, FormEvent } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, UserPlus } from 'lucide-react';
import ImageCaptcha from '../components/ImageCaptcha';
import { useAuthStore } from '../stores/authStore';
import { StoneButton, StoneInput } from '@/components/ui';
import './LoginPage.css';

/**
 * 登录页面组件
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Auth Store
  const { login, isAuthenticated, loading, error, clearError } = useAuthStore();

  // 表单状态
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<{ username?: string; password?: string }>({});

  // 验证码相关状态
  const [captchaVerified, setCaptchaVerified] = useState(false);
  const [verifiedToken, setVerifiedToken] = useState<string | null>(null);
  const [showCaptcha, setShowCaptcha] = useState(false);

  // 消息提示
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

  // 如果已登录，重定向到首页或来源页
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: string })?.from || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // 清除错误
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  // 显示消息
  const showMessage = (type: 'success' | 'error' | 'warning', text: string) => {
    setMessage({ type, text });
    if (type === 'success') {
      setTimeout(() => setMessage(null), 3000);
    }
  };

  /**
   * 验证表单
   */
  const validateForm = (): boolean => {
    const errors: { username?: string; password?: string } = {};

    if (!username.trim()) {
      errors.username = '请输入用户名';
    } else if (username.trim().length < 3) {
      errors.username = '用户名至少3个字符';
    }

    if (!password) {
      errors.password = '请输入密码';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * 处理验证码验证成功
   */
  const handleCaptchaSuccess = useCallback((token: string) => {
    setCaptchaVerified(true);
    setVerifiedToken(token);
    showMessage('success', '验证成功，请点击登录');
  }, []);

  /**
   * 处理验证码验证失败
   */
  const handleCaptchaFail = useCallback(() => {
    setCaptchaVerified(false);
    setVerifiedToken(null);
  }, []);

  /**
   * 处理验证码刷新
   */
  const handleCaptchaRefresh = useCallback(() => {
    setCaptchaVerified(false);
    setVerifiedToken(null);
  }, []);

  /**
   * 处理表单提交（Enter 键或按钮点击）
   */
  const handleFormSubmit = useCallback((e: FormEvent) => {
    e.preventDefault();

    // 如果还没显示验证码，先显示验证码
    if (!showCaptcha) {
      if (validateForm()) {
        setShowCaptcha(true);
      } else {
        showMessage('warning', '请先填写用户名和密码');
      }
      return;
    }

    // 如果已显示验证码但未验证，提示
    if (!captchaVerified || !verifiedToken) {
      showMessage('warning', '请先完成滑块验证');
      return;
    }

    // 执行登录
    handleLogin();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showCaptcha, captchaVerified, verifiedToken, username, password]);

  /**
   * 处理登录提交
   */
  const handleLogin = useCallback(async () => {
    if (!captchaVerified || !verifiedToken) {
      showMessage('warning', '请先完成滑块验证');
      return;
    }

    try {
      await login({
        username: username.trim(),
        password: password,
        captcha_token: verifiedToken,
      });

      showMessage('success', '登录成功');
      // 导航由 useEffect 处理
    } catch (err) {
      // 登录失败，重置验证码状态
      setCaptchaVerified(false);
      setVerifiedToken(null);
      setShowCaptcha(false);

      const errorMessage = err instanceof Error ? err.message : '登录失败';
      showMessage('error', errorMessage);
    }
  }, [captchaVerified, verifiedToken, username, password, login, setShowCaptcha]);

  return (
    <div className="login-page">
      {/* 背景装饰 */}
      <div className="login-background">
        <div className="bg-shape shape-1" />
        <div className="bg-shape shape-2" />
        <div className="bg-shape shape-3" />
      </div>

      {/* 登录卡片 - Stone 风格 */}
      <div className="login-card">
        {/* Logo 和标题 */}
        <div className="login-header">
          <h1 className="login-title">新闻爬虫系统</h1>
          <p className="login-subtitle">News Scraper Dashboard</p>
        </div>

        {/* 登录表单 */}
        <form className="login-form" onSubmit={handleFormSubmit} autoComplete="off">
          {/* 用户名 */}
          <div className="form-item mb-4">
            <StoneInput
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                setFormErrors((prev) => ({ ...prev, username: undefined }));
              }}
              placeholder="用户名"
              prefix={<User className="w-4 h-4" />}
              className={formErrors.username ? 'border-red-400' : ''}
            />
            {formErrors.username && (
              <p className="text-red-500 text-xs mt-1">{formErrors.username}</p>
            )}
          </div>

          {/* 密码 */}
          <div className="form-item mb-4">
            <div className="relative">
              <StoneInput
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setFormErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="密码"
                prefix={<Lock className="w-4 h-4" />}
                className={formErrors.password ? 'border-red-400' : ''}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-cyan-400 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {formErrors.password && (
              <p className="text-red-500 text-xs mt-1">{formErrors.password}</p>
            )}
          </div>

          {/* 错误/消息提示 */}
          {(error || message) && (
            <div className={`login-error ${
              message?.type === 'success' ? '!bg-emerald-500/10 !border-emerald-500/30 !text-emerald-400' :
              message?.type === 'warning' ? '!bg-yellow-500/10 !border-yellow-500/30 !text-yellow-400' : ''
            }`}>
              {message?.text || error}
            </div>
          )}

          {/* 图形验证码 */}
          {showCaptcha && (
            <div className="captcha-wrapper">
              <ImageCaptcha
                onSuccess={handleCaptchaSuccess}
                onFail={handleCaptchaFail}
                onRefresh={handleCaptchaRefresh}
              />
            </div>
          )}

          {/* 操作按钮 */}
          <div className="login-actions">
            {!showCaptcha ? (
              <StoneButton
                type="submit"
                className="w-full h-12 text-base"
              >
                下一步
              </StoneButton>
            ) : (
              <StoneButton
                type="submit"
                className="w-full h-12 text-base"
                loading={loading}
                disabled={!captchaVerified}
              >
                {loading ? '登录中...' : '登录'}
              </StoneButton>
            )}
          </div>

          {/* 返回按钮 */}
          {showCaptcha && (
            <StoneButton
              type="button"
              variant="ghost"
              className="w-full mt-3"
              onClick={() => {
                setShowCaptcha(false);
                setCaptchaVerified(false);
                setVerifiedToken(null);
                setMessage(null);
              }}
            >
              返回修改
            </StoneButton>
          )}
        </form>

        {/* 注册链接 */}
        <div className="login-footer">
          <Link
            to="/register"
            className="flex items-center justify-center gap-2 text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            没有账号？立即注册
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
