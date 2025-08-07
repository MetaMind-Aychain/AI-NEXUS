"""
WebSocket管理器

负责管理所有WebSocket连接，实现实时通信功能
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket

from .models import WebSocketMessage, User


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 项目订阅: project_id -> Set[user_id]
        self.project_subscriptions: Dict[str, Set[str]] = {}
        
        # 用户会话: user_id -> session_info
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 消息队列: user_id -> List[message]
        self.message_queues: Dict[str, list] = {}
        
        # 连接状态监控
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        
        # 如果用户已有连接，先断开旧连接
        if user_id in self.active_connections:
            await self.disconnect(user_id)
        
        # 建立新连接
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        
        # 更新统计
        self.connection_stats["total_connections"] += 1
        self.connection_stats["active_connections"] = len(self.active_connections)
        
        # 发送欢迎消息
        await self.send_to_user(user_id, {
            "type": "connection_established",
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        })
        
        # 发送排队的消息
        await self._send_queued_messages(user_id)
        
        print(f"✅ 用户 {user_id} WebSocket连接已建立")
    
    async def disconnect(self, user_id: str):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            
            try:
                await websocket.close()
            except:
                pass  # 连接可能已经关闭
            
            # 清理连接信息
            del self.active_connections[user_id]
            
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            # 清理项目订阅
            for project_id, subscribers in self.project_subscriptions.items():
                subscribers.discard(user_id)
            
            # 更新统计
            self.connection_stats["active_connections"] = len(self.active_connections)
            
            print(f"❌ 用户 {user_id} WebSocket连接已断开")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """向特定用户发送消息"""
        if user_id not in self.active_connections:
            # 用户不在线，将消息加入队列
            await self._queue_message(user_id, message)
            return False
        
        try:
            websocket = self.active_connections[user_id]
            
            # 构建WebSocket消息
            ws_message = WebSocketMessage(
                type=message.get("type", "notification"),
                data=message,
                sender="system",
                recipient=user_id
            )
            
            # 发送消息
            await websocket.send_text(ws_message.json())
            
            # 更新统计和会话信息
            self.connection_stats["messages_sent"] += 1
            if user_id in self.user_sessions:
                self.user_sessions[user_id]["last_activity"] = datetime.now()
                self.user_sessions[user_id]["message_count"] += 1
            
            return True
            
        except Exception as e:
            print(f"发送消息到用户 {user_id} 失败: {e}")
            # 连接可能已断开，清理连接
            await self.disconnect(user_id)
            return False
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any], 
                                 exclude_user: Optional[str] = None):
        """向项目的所有订阅者广播消息"""
        if project_id not in self.project_subscriptions:
            return
        
        subscribers = self.project_subscriptions[project_id].copy()
        if exclude_user:
            subscribers.discard(exclude_user)
        
        # 并发发送消息
        send_tasks = []
        for user_id in subscribers:
            task = asyncio.create_task(self.send_to_user(user_id, message))
            send_tasks.append(task)
        
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """向所有连接的用户广播消息"""
        if not self.active_connections:
            return
        
        # 并发发送消息
        send_tasks = []
        for user_id in list(self.active_connections.keys()):
            task = asyncio.create_task(self.send_to_user(user_id, message))
            send_tasks.append(task)
        
        await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def subscribe_to_project(self, user_id: str, project_id: str):
        """订阅项目更新"""
        if project_id not in self.project_subscriptions:
            self.project_subscriptions[project_id] = set()
        
        self.project_subscriptions[project_id].add(user_id)
        
        # 发送订阅确认
        await self.send_to_user(user_id, {
            "type": "subscription_confirmed",
            "project_id": project_id,
            "message": f"已订阅项目 {project_id} 的更新"
        })
        
        print(f"📡 用户 {user_id} 订阅了项目 {project_id}")
    
    async def unsubscribe_from_project(self, user_id: str, project_id: str):
        """取消订阅项目更新"""
        if project_id in self.project_subscriptions:
            self.project_subscriptions[project_id].discard(user_id)
            
            # 如果没有订阅者了，删除项目订阅记录
            if not self.project_subscriptions[project_id]:
                del self.project_subscriptions[project_id]
        
        await self.send_to_user(user_id, {
            "type": "subscription_cancelled",
            "project_id": project_id,
            "message": f"已取消订阅项目 {project_id}"
        })
    
    async def send_progress_update(self, project_id: str, progress_data: Dict[str, Any]):
        """发送项目进度更新"""
        message = {
            "type": "progress_update",
            "project_id": project_id,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_project(project_id, message)
    
    async def send_ai_status_update(self, project_id: str, ai_type: str, status: str, details: Dict[str, Any] = None):
        """发送AI状态更新"""
        message = {
            "type": "ai_status_update",
            "project_id": project_id,
            "ai_type": ai_type,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_project(project_id, message)
    
    async def send_error_notification(self, user_id: str, error_type: str, error_message: str, 
                                    project_id: Optional[str] = None):
        """发送错误通知"""
        message = {
            "type": "error_notification",
            "error_type": error_type,
            "error_message": error_message,
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_to_user(user_id, message)
    
    async def receive_message(self, user_id: str, message_data: str):
        """接收用户消息"""
        try:
            message = json.loads(message_data)
            self.connection_stats["messages_received"] += 1
            
            # 更新用户活动时间
            if user_id in self.user_sessions:
                self.user_sessions[user_id]["last_activity"] = datetime.now()
            
            return message
            
        except json.JSONDecodeError as e:
            await self.send_error_notification(
                user_id, "invalid_message_format", f"消息格式错误: {str(e)}"
            )
            return None
    
    async def _queue_message(self, user_id: str, message: Dict[str, Any]):
        """将消息加入用户队列"""
        if user_id not in self.message_queues:
            self.message_queues[user_id] = []
        
        # 限制队列大小，避免内存溢出
        if len(self.message_queues[user_id]) >= 100:
            self.message_queues[user_id].pop(0)  # 移除最旧的消息
        
        self.message_queues[user_id].append({
            "message": message,
            "queued_at": datetime.now().isoformat()
        })
    
    async def _send_queued_messages(self, user_id: str):
        """发送排队的消息"""
        if user_id not in self.message_queues:
            return
        
        queued_messages = self.message_queues[user_id]
        del self.message_queues[user_id]
        
        for queued_item in queued_messages:
            message = queued_item["message"]
            message["queued_at"] = queued_item["queued_at"]
            message["delivered_at"] = datetime.now().isoformat()
            
            await self.send_to_user(user_id, message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            **self.connection_stats,
            "user_sessions": len(self.user_sessions),
            "project_subscriptions": len(self.project_subscriptions),
            "queued_messages": sum(len(queue) for queue in self.message_queues.values())
        }
    
    def get_user_session_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话信息"""
        return self.user_sessions.get(user_id)
    
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections
    
    def get_project_subscribers(self, project_id: str) -> Set[str]:
        """获取项目订阅者列表"""
        return self.project_subscriptions.get(project_id, set()).copy()
    
    async def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """清理不活跃的会话"""
        now = datetime.now()
        inactive_users = []
        
        for user_id, session_info in self.user_sessions.items():
            last_activity = session_info["last_activity"]
            inactive_duration = (now - last_activity).total_seconds() / 60
            
            if inactive_duration > timeout_minutes:
                inactive_users.append(user_id)
        
        # 断开不活跃的连接
        for user_id in inactive_users:
            await self.disconnect(user_id)
            print(f"🧹 清理不活跃用户连接: {user_id}")
    
    async def send_system_announcement(self, announcement: str, priority: str = "normal"):
        """发送系统公告"""
        message = {
            "type": "system_announcement",
            "announcement": announcement,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(message)


# WebSocket消息处理器
class MessageHandler:
    """WebSocket消息处理器"""
    
    def __init__(self, websocket_manager: WebSocketManager, ai_coordinator=None):
        self.websocket_manager = websocket_manager
        self.ai_coordinator = ai_coordinator
        self.message_handlers = {
            "ping": self._handle_ping,
            "subscribe_project": self._handle_subscribe_project,
            "unsubscribe_project": self._handle_unsubscribe_project,
            "ai_chat": self._handle_ai_chat,
            "request_status": self._handle_status_request,
            "user_feedback": self._handle_user_feedback
        }
    
    async def handle_message(self, user_id: str, message: Dict[str, Any]):
        """处理接收到的消息"""
        message_type = message.get("type")
        
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](user_id, message)
            except Exception as e:
                await self.websocket_manager.send_error_notification(
                    user_id, "message_handling_error", f"处理消息失败: {str(e)}"
                )
        else:
            await self.websocket_manager.send_error_notification(
                user_id, "unknown_message_type", f"未知的消息类型: {message_type}"
            )
    
    async def _handle_ping(self, user_id: str, message: Dict[str, Any]):
        """处理ping消息"""
        await self.websocket_manager.send_to_user(user_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_subscribe_project(self, user_id: str, message: Dict[str, Any]):
        """处理项目订阅"""
        project_id = message.get("project_id")
        if project_id:
            await self.websocket_manager.subscribe_to_project(user_id, project_id)
    
    async def _handle_unsubscribe_project(self, user_id: str, message: Dict[str, Any]):
        """处理取消项目订阅"""
        project_id = message.get("project_id")
        if project_id:
            await self.websocket_manager.unsubscribe_from_project(user_id, project_id)
    
    async def _handle_ai_chat(self, user_id: str, message: Dict[str, Any]):
        """处理AI对话"""
        if not self.ai_coordinator:
            await self.websocket_manager.send_error_notification(
                user_id, "ai_unavailable", "AI服务暂不可用"
            )
            return
        
        project_id = message.get("project_id")
        chat_content = message.get("content")
        ai_type = message.get("ai_type", "document")
        
        if not project_id or not chat_content:
            await self.websocket_manager.send_error_notification(
                user_id, "invalid_chat_request", "无效的对话请求"
            )
            return
        
        try:
            # 调用AI协调器处理对话
            response = await self.ai_coordinator.handle_user_chat(
                user_id, project_id, ai_type, chat_content
            )
            
            await self.websocket_manager.send_to_user(user_id, {
                "type": "ai_response",
                "project_id": project_id,
                "ai_type": ai_type,
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            await self.websocket_manager.send_error_notification(
                user_id, "ai_chat_error", f"AI对话失败: {str(e)}"
            )
    
    async def _handle_status_request(self, user_id: str, message: Dict[str, Any]):
        """处理状态请求"""
        project_id = message.get("project_id")
        
        if self.ai_coordinator:
            try:
                status = await self.ai_coordinator.get_project_status(project_id)
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "status_response",
                    "project_id": project_id,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                await self.websocket_manager.send_error_notification(
                    user_id, "status_request_error", f"获取状态失败: {str(e)}"
                )
    
    async def _handle_user_feedback(self, user_id: str, message: Dict[str, Any]):
        """处理用户反馈"""
        project_id = message.get("project_id")
        feedback_type = message.get("feedback_type")
        feedback_content = message.get("content")
        
        if self.ai_coordinator:
            try:
                await self.ai_coordinator.process_user_feedback(
                    user_id, project_id, feedback_type, feedback_content
                )
                
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "feedback_acknowledged",
                    "project_id": project_id,
                    "message": "反馈已收到并处理",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                await self.websocket_manager.send_error_notification(
                    user_id, "feedback_error", f"处理反馈失败: {str(e)}"
                )