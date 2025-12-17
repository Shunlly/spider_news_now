/**
 * 图形验证码组件
 * Image Captcha Component
 *
 * 功能：
 * - 显示验证码图片
 * - 输入框输入验证码
 * - 输入满4位后自动验证
 * - 刷新验证码
 * - Stone 极简样式
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { RefreshCw, Loader2, Check } from 'lucide-react';
import type { CaptchaData } from '../../types/auth';
import authService from '../../services/authService';
import { StoneInput } from '@/components/ui';

// 验证码长度
const CAPTCHA_LENGTH = 4;

interface ImageCaptchaProps {
  /**
   * 验证成功回调
   * @param verifiedToken 验证成功后的令牌
   */
  onSuccess: (verifiedToken: string) => void;
  /**
   * 验证失败回调
   */
  onFail?: () => void;
  /**
   * 验证码过期或需要刷新回调
   */
  onRefresh?: () => void;
}

/**
 * 图形验证码组件
 */
const ImageCaptcha: React.FC<ImageCaptchaProps> = ({
  onSuccess,
  onFail,
  onRefresh,
}) => {
  // 验证码数据
  const [captchaData, setCaptchaData] = useState<CaptchaData | null>(null);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 验证中状态
  const [verifying, setVerifying] = useState(false);
  // 用户输入的验证码
  const [code, setCode] = useState('');
  // 验证结果
  const [verifyResult, setVerifyResult] = useState<'success' | 'fail' | null>(null);
  // 消息提示
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

  // 输入框引用
  const inputRef = useRef<HTMLInputElement>(null);

  // 显示消息
  const showMessage = (type: 'success' | 'error' | 'warning', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  /**
   * 获取验证码
   */
  const fetchCaptcha = useCallback(async () => {
    setLoading(true);
    setCode('');
    setVerifyResult(null);
    setMessage(null);
    try {
      const data = await authService.getCaptcha();
      setCaptchaData(data);
      // 聚焦到输入框
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (error) {
      showMessage('error', '获取验证码失败，请重试');
      console.error('Failed to fetch captcha:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 组件挂载时获取验证码
  useEffect(() => {
    fetchCaptcha();
  }, [fetchCaptcha]);

  /**
   * 验证验证码
   */
  const handleVerify = useCallback(async (inputCode: string) => {
    if (!captchaData || !inputCode.trim()) {
      return;
    }

    if (verifying) return;

    setVerifying(true);
    try {
      const response = await authService.verifyCaptcha({
        token: captchaData.token,
        code: inputCode.trim(),
      });

      if (response.success && response.verified_token) {
        setVerifyResult('success');
        showMessage('success', '验证成功');
        onSuccess(response.verified_token);
      } else {
        setVerifyResult('fail');
        const msg = response.message || '验证码错误';
        showMessage('warning', msg);
        onFail?.();

        // 如果需要刷新验证码
        if (msg.includes('请刷新') || msg.includes('已过期')) {
          setTimeout(() => {
            fetchCaptcha();
            onRefresh?.();
          }, 1000);
        } else {
          // 清空输入，让用户重新输入
          setCode('');
          setTimeout(() => {
            setVerifyResult(null);
            inputRef.current?.focus();
          }, 500);
        }
      }
    } catch {
      setVerifyResult('fail');
      showMessage('error', '验证失败，请重试');
      onFail?.();
      setCode('');
      setTimeout(() => {
        setVerifyResult(null);
        inputRef.current?.focus();
      }, 500);
    } finally {
      setVerifying(false);
    }
  }, [captchaData, verifying, onSuccess, onFail, onRefresh, fetchCaptcha]);

  /**
   * 处理输入变化 - 输入满4位自动验证
   */
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newCode = e.target.value.replace(/\s/g, '');
    setCode(newCode);

    // 输入满4位后自动验证
    if (newCode.length === CAPTCHA_LENGTH && !verifying && verifyResult !== 'success') {
      handleVerify(newCode);
    }
  }, [verifying, verifyResult, handleVerify]);

  /**
   * 刷新验证码
   */
  const handleRefresh = useCallback(() => {
    fetchCaptcha();
    onRefresh?.();
  }, [fetchCaptcha, onRefresh]);

  return (
    <div className="image-captcha-container">
      {/* 消息提示 */}
      {message && (
        <div className={`mb-3 p-2 rounded-lg text-sm text-center ${
          message.type === 'success' ? 'bg-green-50 text-green-600 border border-green-200' :
          message.type === 'warning' ? 'bg-yellow-50 text-yellow-600 border border-yellow-200' :
          'bg-red-50 text-red-600 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* 验证码图片 */}
      <div className="flex items-center gap-3 mb-3">
        <div className="relative flex-shrink-0 w-[150px] h-[50px] bg-stone-100 rounded-lg overflow-hidden border border-stone-200">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-stone-400" />
            </div>
          ) : captchaData ? (
            <img
              src={`data:image/png;base64,${captchaData.image}`}
              alt="验证码"
              className="w-full h-full object-cover"
              draggable={false}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-stone-400 text-sm">
              加载失败
            </div>
          )}
        </div>

        {/* 刷新按钮 */}
        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading || verifying}
          className="p-2 text-stone-400 hover:text-stone-600 hover:bg-stone-100 rounded-lg transition-colors disabled:opacity-50"
          title="刷新验证码"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* 验证码输入框 */}
      <div className="flex items-center gap-3">
        <StoneInput
          ref={inputRef}
          type="text"
          value={code}
          onChange={handleInputChange}
          placeholder="输入4位验证码"
          maxLength={CAPTCHA_LENGTH}
          disabled={verifying || verifyResult === 'success'}
          className={`flex-1 text-center tracking-widest ${
            verifyResult === 'success' ? 'border-green-400 bg-green-50' :
            verifyResult === 'fail' ? 'border-red-400' : ''
          }`}
          autoComplete="off"
        />

        {/* 状态指示器 */}
        <div className="w-10 h-10 flex items-center justify-center">
          {verifying ? (
            <Loader2 className="w-5 h-5 animate-spin text-stone-400" />
          ) : verifyResult === 'success' ? (
            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
              <Check className="w-5 h-5 text-white" />
            </div>
          ) : (
            <span className="text-sm text-stone-400">{code.length}/{CAPTCHA_LENGTH}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImageCaptcha;
