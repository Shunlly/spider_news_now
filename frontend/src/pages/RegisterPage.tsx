/**
 * 注册页面
 * Register Page with Stone Design
 *
 * 功能：
 * - 用户名、邮箱、密码表单
 * - 图形验证码
 * - Stone 极简风格
 */

import { useState, useCallback, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import ImageCaptcha from '../components/ImageCaptcha';
import { StoneButton, StoneInput } from '@/components/ui';
import api from '@/services/api';
import './LoginPage.css';

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

/**
 * 注册页面组件
 */
const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  // 表单状态
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  // 验证码相关状态
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [captchaCode, setCaptchaCode] = useState('');
  const [showCaptcha, setShowCaptcha] = useState(false);

  // 消息提示
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

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
  const validateForm = useCallback((): boolean => {
    const errors: FormErrors = {};

    if (!username.trim()) {
      errors.username = '请输入用户名';
    } else if (username.trim().length < 3) {
      errors.username = '用户名至少3个字符';
    } else if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(username)) {
      errors.username = '用户名需以字母开头，只能包含字母、数字、下划线';
    }

    if (!email.trim()) {
      errors.email = '请输入邮箱';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = '请输入有效的邮箱地址';
    }

    if (!password) {
      errors.password = '请输入密码';
    } else if (password.length < 8) {
      errors.password = '密码至少8位';
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = '两次密码输入不一致';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [username, email, password, confirmPassword]);

  /**
   * 处理验证码生成成功
   */
  const handleCaptchaSuccess = useCallback((token: string) => {
    setCaptchaToken(token);
  }, []);

  /**
   * 处理表单提交
   */
  const handleFormSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // 如果还没显示验证码，先显示验证码
    if (!showCaptcha) {
      setShowCaptcha(true);
      return;
    }

    // 验证验证码
    if (!captchaToken || !captchaCode) {
      showMessage('warning', '请输入验证码');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/register', {
        username: username.trim(),
        email: email.trim(),
        password,
        captcha_token: captchaToken,
        captcha_code: captchaCode,
      });

      showMessage('success', '注册成功，即将跳转到登录页面');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '注册失败';
      showMessage('error', errorMessage);
      // 重置验证码
      setShowCaptcha(false);
      setCaptchaToken(null);
      setCaptchaCode('');
    } finally {
      setLoading(false);
    }
  }, [username, email, password, showCaptcha, captchaToken, captchaCode, navigate, validateForm]);

  return (
    <div className="login-page">
      {/* 背景装饰 */}
      <div className="login-background">
        <div className="bg-shape shape-1" />
        <div className="bg-shape shape-2" />
        <div className="bg-shape shape-3" />
      </div>

      {/* 注册卡片 - Stone 风格 */}
      <div className="login-card">
        {/* Logo 和标题 */}
        <div className="login-header">
          <h1 className="login-title">用户注册</h1>
          <p className="login-subtitle">Create your account</p>
        </div>

        {/* 注册表单 */}
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
              disabled={showCaptcha}
            />
            {formErrors.username && (
              <p className="text-red-500 text-xs mt-1">{formErrors.username}</p>
            )}
          </div>

          {/* 邮箱 */}
          <div className="form-item mb-4">
            <StoneInput
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setFormErrors((prev) => ({ ...prev, email: undefined }));
              }}
              placeholder="邮箱"
              prefix={<Mail className="w-4 h-4" />}
              className={formErrors.email ? 'border-red-400' : ''}
              disabled={showCaptcha}
            />
            {formErrors.email && (
              <p className="text-red-500 text-xs mt-1">{formErrors.email}</p>
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
                disabled={showCaptcha}
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

          {/* 确认密码 */}
          <div className="form-item mb-4">
            <StoneInput
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setFormErrors((prev) => ({ ...prev, confirmPassword: undefined }));
              }}
              placeholder="确认密码"
              prefix={<Lock className="w-4 h-4" />}
              className={formErrors.confirmPassword ? 'border-red-400' : ''}
              disabled={showCaptcha}
            />
            {formErrors.confirmPassword && (
              <p className="text-red-500 text-xs mt-1">{formErrors.confirmPassword}</p>
            )}
          </div>

          {/* 错误/消息提示 */}
          {message && (
            <div className={`login-error ${
              message.type === 'success' ? '!bg-emerald-500/10 !border-emerald-500/30 !text-emerald-400' :
              message.type === 'warning' ? '!bg-yellow-500/10 !border-yellow-500/30 !text-yellow-400' : ''
            }`}>
              {message.text}
            </div>
          )}

          {/* 图形验证码 */}
          {showCaptcha && (
            <div className="captcha-wrapper flex-col gap-3">
              <ImageCaptcha
                onSuccess={handleCaptchaSuccess}
                onFail={() => setCaptchaToken(null)}
                onRefresh={() => {
                  setCaptchaToken(null);
                  setCaptchaCode('');
                }}
              />
              <StoneInput
                value={captchaCode}
                onChange={(e) => setCaptchaCode(e.target.value)}
                placeholder="请输入验证码"
                className="mt-3"
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
                disabled={!captchaToken || !captchaCode}
              >
                {loading ? '注册中...' : '注册'}
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
                setCaptchaToken(null);
                setCaptchaCode('');
                setMessage(null);
              }}
            >
              返回修改
            </StoneButton>
          )}
        </form>

        {/* 登录链接 */}
        <div className="login-footer">
          <Link
            to="/login"
            className="flex items-center justify-center gap-2 text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            已有账号？返回登录
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
