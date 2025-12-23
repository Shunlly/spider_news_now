/**
 * HUD 风格图形验证码组件
 * HUD-style Image Captcha Component
 *
 * 深色主题 + 发光效果
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { RefreshCw, Loader2, Check } from 'lucide-react';
import type { CaptchaData } from '../../types/auth';
import authService from '../../services/authService';
import { StoneInput } from '@/components/ui';

const CAPTCHA_LENGTH = 4;

interface ImageCaptchaProps {
  onSuccess: (verifiedToken: string) => void;
  onFail?: () => void;
  onRefresh?: () => void;
}

const ImageCaptcha: React.FC<ImageCaptchaProps> = ({
  onSuccess,
  onFail,
  onRefresh,
}) => {
  const [captchaData, setCaptchaData] = useState<CaptchaData | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [code, setCode] = useState('');
  const [verifyResult, setVerifyResult] = useState<'success' | 'fail' | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const showMessage = (type: 'success' | 'error' | 'warning', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const fetchCaptcha = useCallback(async () => {
    setLoading(true);
    setCode('');
    setVerifyResult(null);
    setMessage(null);
    try {
      const data = await authService.getCaptcha();
      setCaptchaData(data);
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (error) {
      showMessage('error', '获取验证码失败，请重试');
      console.error('Failed to fetch captcha:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCaptcha();
  }, [fetchCaptcha]);

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

        if (msg.includes('请刷新') || msg.includes('已过期')) {
          setTimeout(() => {
            fetchCaptcha();
            onRefresh?.();
          }, 1000);
        } else {
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

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newCode = e.target.value.replace(/\s/g, '');
    setCode(newCode);

    if (newCode.length === CAPTCHA_LENGTH && !verifying && verifyResult !== 'success') {
      handleVerify(newCode);
    }
  }, [verifying, verifyResult, handleVerify]);

  const handleRefresh = useCallback(() => {
    fetchCaptcha();
    onRefresh?.();
  }, [fetchCaptcha, onRefresh]);

  return (
    <div className="image-captcha-container">
      {/* 消息提示 */}
      {message && (
        <div className={`mb-3 p-2 rounded-lg text-sm text-center backdrop-blur-xl ${
          message.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
          message.type === 'warning' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
          'bg-red-500/10 text-red-400 border border-red-500/30'
        }`}>
          {message.text}
        </div>
      )}

      {/* 验证码图片 */}
      <div className="flex items-center gap-3 mb-3">
        <div className="relative flex-shrink-0 w-[150px] h-[50px] bg-slate-800/50 rounded-lg overflow-hidden border border-slate-700/50">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
            </div>
          ) : captchaData ? (
            <img
              src={`data:image/png;base64,${captchaData.image}`}
              alt="验证码"
              className="w-full h-full object-cover"
              draggable={false}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm">
              加载失败
            </div>
          )}
        </div>

        {/* 刷新按钮 */}
        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading || verifying}
          className="p-2 text-slate-500 hover:text-cyan-400 hover:bg-slate-800/50 rounded-lg transition-colors disabled:opacity-50"
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
          className={`flex-1 text-center tracking-widest font-mono ${
            verifyResult === 'success' ? '!border-emerald-500/50 !bg-emerald-500/10' :
            verifyResult === 'fail' ? '!border-red-500/50' : ''
          }`}
          autoComplete="off"
        />

        {/* 状态指示器 */}
        <div className="w-10 h-10 flex items-center justify-center">
          {verifying ? (
            <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
          ) : verifyResult === 'success' ? (
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center shadow-[0_0_10px_rgba(16,185,129,0.3)]">
              <Check className="w-5 h-5 text-emerald-400" />
            </div>
          ) : (
            <span className="text-sm text-slate-500 font-mono">{code.length}/{CAPTCHA_LENGTH}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImageCaptcha;
