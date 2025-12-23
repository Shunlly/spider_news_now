/**
 * WebSocket Hook
 * useWebSocket Hook
 * T142: Create useWebSocket hook
 *
 * 提供 WebSocket 连接管理，支持自动重连和消息处理。
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage<T = unknown> {
  type: string;
  data: T;
  timestamp?: string;
}

export interface UseWebSocketOptions<T = unknown> {
  /** WebSocket 端点路径 */
  url: string;
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** 重连间隔（毫秒） */
  reconnectInterval?: number;
  /** 最大重连次数 */
  maxReconnects?: number;
  /** 心跳间隔（毫秒） */
  heartbeatInterval?: number;
  /** 消息处理器 */
  onMessage?: (message: WebSocketMessage<T>) => void;
  /** 连接成功回调 */
  onOpen?: () => void;
  /** 连接关闭回调 */
  onClose?: () => void;
  /** 错误回调 */
  onError?: (error: Event) => void;
}

export interface UseWebSocketReturn<T = unknown> {
  /** 连接状态 */
  status: WebSocketStatus;
  /** 最后收到的消息 */
  lastMessage: WebSocketMessage<T> | null;
  /** 发送消息 */
  send: (message: WebSocketMessage) => void;
  /** 手动连接 */
  connect: () => void;
  /** 手动断开 */
  disconnect: () => void;
  /** 重连次数 */
  reconnectCount: number;
}

export function useWebSocket<T = unknown>(
  options: UseWebSocketOptions<T>
): UseWebSocketReturn<T> {
  const {
    url,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnects = 5,
    heartbeatInterval = 30000,
    onMessage,
    onOpen,
    onClose,
    onError,
  } = options;

  const { token } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage<T> | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  // 构建 WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const baseUrl = import.meta.env.VITE_WS_URL ||
      window.location.origin.replace(/^http/, 'ws');
    const wsUrl = `${baseUrl}${url}`;

    // 添加 token 作为查询参数
    if (token) {
      const separator = wsUrl.includes('?') ? '&' : '?';
      return `${wsUrl}${separator}token=${token}`;
    }
    return wsUrl;
  }, [url, token]);

  // 清理定时器
  const clearTimers = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  // 发送心跳
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return;

    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  // 连接
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    clearTimers();
    setStatus('connecting');

    try {
      const ws = new WebSocket(getWebSocketUrl());

      ws.onopen = () => {
        setStatus('connected');
        reconnectCountRef.current = 0;
        setReconnectCount(0);
        startHeartbeat();
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage<T>;

          // 忽略 pong 消息
          if (message.type === 'pong') return;

          setLastMessage(message);
          onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        clearTimers();
        onClose?.();

        // 自动重连
        if (reconnectCountRef.current < maxReconnects) {
          reconnectCountRef.current++;
          setReconnectCount(reconnectCountRef.current);

          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setStatus('error');
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setStatus('error');
    }
  }, [getWebSocketUrl, clearTimers, startHeartbeat, onOpen, onMessage, onClose, onError, maxReconnects, reconnectInterval]);

  // 断开连接
  const disconnect = useCallback(() => {
    clearTimers();
    reconnectCountRef.current = maxReconnects; // 阻止自动重连

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, [clearTimers, maxReconnects]);

  // 发送消息
  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // 自动连接
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, token, connect, disconnect]);

  return {
    status,
    lastMessage,
    send,
    connect,
    disconnect,
    reconnectCount,
  };
}

export default useWebSocket;
