/**
 * WebSocket上下文 - 实时通信管理
 * 
 * 管理与后端的WebSocket连接，处理实时消息
 */

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useAuth } from './AuthContext';
import { useNotification } from './NotificationContext';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  
  const websocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  
  const { user, isAuthenticated } = useAuth();
  const { showNotification } = useNotification();
  
  // WebSocket连接配置
  const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
  const RECONNECT_INTERVAL = 5000; // 5秒重连间隔
  const HEARTBEAT_INTERVAL = 30000; // 30秒心跳间隔
  const MAX_RECONNECT_ATTEMPTS = 10;
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // 消息处理器
  const messageHandlers = useRef({});

  const connect = () => {
    if (!isAuthenticated || !user?.id) {
      console.log('用户未认证，跳过WebSocket连接');
      return;
    }

    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接');
      return;
    }

    try {
      setConnectionStatus('connecting');
      const wsUrl = `${WS_URL}/${user.id}`;
      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        console.log('✅ WebSocket连接已建立');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        
        // 启动心跳
        startHeartbeat();
        
        showNotification('实时连接已建立', 'success');
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 收到WebSocket消息:', message);
          
          setLastMessage(message);
          setMessageHistory(prev => [...prev.slice(-99), message]); // 保留最近100条消息
          
          // 处理特定类型的消息
          handleMessage(message);
          
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      websocketRef.current.onclose = (event) => {
        console.log('❌ WebSocket连接已关闭:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // 停止心跳
        stopHeartbeat();
        
        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          scheduleReconnect();
        }
      };

      websocketRef.current.onerror = (error) => {
        console.error('🔥 WebSocket错误:', error);
        setConnectionStatus('error');
        showNotification('连接发生错误', 'error');
      };

    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
      setConnectionStatus('error');
    }
  };

  const disconnect = () => {
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'User initiated disconnect');
      websocketRef.current = null;
    }
    
    stopHeartbeat();
    clearReconnectTimeout();
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const scheduleReconnect = () => {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log('🚫 达到最大重连次数，停止重连');
      showNotification('连接失败，请刷新页面重试', 'error');
      return;
    }

    setConnectionStatus('reconnecting');
    setReconnectAttempts(prev => prev + 1);
    
    const delay = Math.min(RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts), 30000); // 指数退避，最大30秒
    
    console.log(`🔄 ${delay/1000}秒后尝试重连 (第${reconnectAttempts + 1}次)`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  };

  const clearReconnectTimeout = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const startHeartbeat = () => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
      }
    }, HEARTBEAT_INTERVAL);
  };

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  };

  const sendMessage = (message) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      try {
        const messageStr = JSON.stringify(message);
        websocketRef.current.send(messageStr);
        console.log('📤 发送WebSocket消息:', message);
        return true;
      } catch (error) {
        console.error('发送WebSocket消息失败:', error);
        return false;
      }
    } else {
      console.warn('WebSocket未连接，无法发送消息');
      showNotification('连接断开，消息发送失败', 'warning');
      return false;
    }
  };

  const handleMessage = (message) => {
    const { type, data } = message;
    
    // 调用注册的消息处理器
    const handler = messageHandlers.current[type];
    if (handler) {
      try {
        handler(data || message);
      } catch (error) {
        console.error(`处理消息类型 ${type} 失败:`, error);
      }
    }
    
    // 内置消息处理
    switch (type) {
      case 'pong':
        // 心跳响应，无需处理
        break;
        
      case 'connection_established':
        console.log('✅ 连接确认:', message.message);
        break;
        
      case 'error_notification':
        showNotification(`错误: ${message.error_message}`, 'error');
        break;
        
      case 'system_announcement':
        showNotification(message.announcement, message.priority === 'high' ? 'warning' : 'info');
        break;
        
      case 'progress_update':
        // 进度更新会由具体页面组件处理
        break;
        
      case 'ai_status_update':
        showNotification(`AI状态更新: ${message.ai_type} - ${message.status}`, 'info');
        break;
        
      case 'ai_response':
        // AI响应会由聊天组件处理
        break;
        
      case 'frontend_preview_ready':
        showNotification('前端预览已生成', 'success');
        break;
        
      case 'project_created':
        showNotification('项目创建成功', 'success');
        break;
        
      case 'development_started':
        showNotification('开发流程已启动', 'success');
        break;
        
      case 'final_test_completed':
        showNotification('最终测试完成', 'success');
        break;
        
      default:
        console.log('未处理的消息类型:', type);
    }
  };

  // 注册消息处理器
  const registerMessageHandler = (messageType, handler) => {
    messageHandlers.current[messageType] = handler;
    
    // 返回取消注册函数
    return () => {
      delete messageHandlers.current[messageType];
    };
  };

  // 订阅项目更新
  const subscribeToProject = (projectId) => {
    return sendMessage({
      type: 'subscribe_project',
      project_id: projectId
    });
  };

  // 取消订阅项目
  const unsubscribeFromProject = (projectId) => {
    return sendMessage({
      type: 'unsubscribe_project', 
      project_id: projectId
    });
  };

  // 发送AI聊天消息
  const sendAIChat = (projectId, content, aiType = 'document') => {
    return sendMessage({
      type: 'ai_chat',
      project_id: projectId,
      content: content,
      ai_type: aiType
    });
  };

  // 请求项目状态
  const requestProjectStatus = (projectId) => {
    return sendMessage({
      type: 'request_status',
      project_id: projectId
    });
  };

  // 发送用户反馈
  const sendUserFeedback = (projectId, feedbackType, content) => {
    return sendMessage({
      type: 'user_feedback',
      project_id: projectId,
      feedback_type: feedbackType,
      content: content
    });
  };

  // 生命周期管理
  useEffect(() => {
    if (isAuthenticated && user?.id) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, user?.id]);

  // 清理资源
  useEffect(() => {
    return () => {
      disconnect();
      clearReconnectTimeout();
    };
  }, []);

  const contextValue = {
    // 连接状态
    isConnected,
    connectionStatus,
    reconnectAttempts,
    
    // 消息相关
    lastMessage,
    messageHistory,
    
    // 基础方法
    connect,
    disconnect,
    sendMessage,
    registerMessageHandler,
    
    // 业务方法
    subscribeToProject,
    unsubscribeFromProject,
    sendAIChat,
    requestProjectStatus,
    sendUserFeedback,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};