#!/usr/bin/env python3
"""
API使用优化管理器
实现智能缓存、请求去重、批量处理等功能，减少LLM API调用次数
"""

import hashlib
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict, deque
import threading

logger = logging.getLogger("API优化管理器")

@dataclass
class CachedResponse:
    """缓存响应数据"""
    response: str
    timestamp: float
    usage_count: int = 0
    quality_score: float = 0.0

@dataclass
class APIRequest:
    """API请求数据"""
    prompt: str
    user_id: str
    project_id: str
    ai_name: str
    action: str
    timestamp: float
    priority: int = 1  # 1-5，5为最高优先级

class APIOptimizationManager:
    """API使用优化管理器"""
    
    def __init__(self, cache_ttl: int = 3600, max_cache_size: int = 1000):
        self.cache_ttl = cache_ttl  # 缓存生存时间（秒）
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CachedResponse] = {}
        self.request_queue: deque = deque()
        self.batch_requests: Dict[str, List[APIRequest]] = defaultdict(list)
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # 启动清理任务
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动缓存清理任务"""
        def cleanup_loop():
            while True:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_expired_cache()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        with self.lock:
            for key, cached_response in self.cache.items():
                if current_time - cached_response.timestamp > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            # 如果缓存仍然过大，删除最少使用的条目
            if len(self.cache) > self.max_cache_size:
                sorted_items = sorted(
                    self.cache.items(), 
                    key=lambda x: (x[1].usage_count, x[1].timestamp)
                )
                items_to_remove = len(self.cache) - self.max_cache_size
                for i in range(items_to_remove):
                    del self.cache[sorted_items[i][0]]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _generate_cache_key(self, prompt: str, ai_name: str, action: str) -> str:
        """生成缓存键"""
        # 标准化提示内容（去除多余空格、换行等）
        normalized_prompt = " ".join(prompt.split())
        content = f"{normalized_prompt}|{ai_name}|{action}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, prompt: str, ai_name: str, action: str) -> Optional[str]:
        """获取缓存的响应"""
        cache_key = self._generate_cache_key(prompt, ai_name, action)
        
        with self.lock:
            if cache_key in self.cache:
                cached_response = self.cache[cache_key]
                # 检查是否过期
                if time.time() - cached_response.timestamp <= self.cache_ttl:
                    cached_response.usage_count += 1
                    logger.info(f"使用缓存响应: {ai_name} - {action}")
                    return cached_response.response
        
        return None
    
    def cache_response(self, prompt: str, ai_name: str, action: str, response: str, 
                      quality_score: float = 0.0):
        """缓存响应"""
        cache_key = self._generate_cache_key(prompt, ai_name, action)
        
        with self.lock:
            self.cache[cache_key] = CachedResponse(
                response=response,
                timestamp=time.time(),
                usage_count=1,
                quality_score=quality_score
            )
        
        logger.info(f"缓存响应: {ai_name} - {action}")
    
    def add_request_to_batch(self, request: APIRequest):
        """添加请求到批处理队列"""
        batch_key = f"{request.ai_name}_{request.action}"
        
        with self.lock:
            self.batch_requests[batch_key].append(request)
        
        logger.info(f"添加批处理请求: {request.ai_name} - {request.action}")
    
    def get_batch_requests(self, ai_name: str, action: str, max_batch_size: int = 5) -> List[APIRequest]:
        """获取批处理请求"""
        batch_key = f"{ai_name}_{action}"
        
        with self.lock:
            requests = self.batch_requests[batch_key][:max_batch_size]
            self.batch_requests[batch_key] = self.batch_requests[batch_key][max_batch_size:]
        
        return requests
    
    def check_rate_limit(self, user_id: str, max_requests_per_minute: int = 60) -> bool:
        """检查用户速率限制"""
        current_time = time.time()
        one_minute_ago = current_time - 60
        
        with self.lock:
            # 清理过期的请求记录
            self.rate_limits[user_id] = [
                req_time for req_time in self.rate_limits[user_id] 
                if req_time > one_minute_ago
            ]
            
            # 检查是否超过限制
            if len(self.rate_limits[user_id]) >= max_requests_per_minute:
                return False
            
            # 添加当前请求
            self.rate_limits[user_id].append(current_time)
        
        return True
    
    def should_use_cache(self, prompt: str, ai_name: str, action: str, 
                        cache_threshold: float = 0.8) -> bool:
        """判断是否应该使用缓存"""
        cache_key = self._generate_cache_key(prompt, ai_name, action)
        
        with self.lock:
            if cache_key in self.cache:
                cached_response = self.cache[cache_key]
                # 如果缓存质量高且使用次数多，优先使用缓存
                if (cached_response.quality_score > cache_threshold and 
                    cached_response.usage_count > 2):
                    return True
        
        return False
    
    def optimize_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """优化提示词，减少token使用"""
        # 移除多余的空格和换行
        optimized = " ".join(prompt.split())
        
        # 如果上下文中有重复信息，进行去重
        if context:
            # 简单的重复检测和移除
            lines = optimized.split('.')
            unique_lines = []
            seen_lines = set()
            
            for line in lines:
                line = line.strip()
                if line and line not in seen_lines:
                    unique_lines.append(line)
                    seen_lines.add(line)
            
            optimized = '. '.join(unique_lines)
        
        return optimized
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（粗略估算）"""
        # 简单的token估算：英文约4字符1token，中文约2字符1token
        english_chars = sum(1 for c in text if ord(c) < 128)
        chinese_chars = len(text) - english_chars
        
        return (english_chars // 4) + (chinese_chars // 2)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_items = len(self.cache)
            total_usage = sum(item.usage_count for item in self.cache.values())
            avg_quality = sum(item.quality_score for item in self.cache.values()) / total_items if total_items > 0 else 0
            
            return {
                "total_items": total_items,
                "total_usage": total_usage,
                "average_quality": avg_quality,
                "cache_hit_rate": self._calculate_cache_hit_rate()
            }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        # 这里需要维护命中统计，简化实现
        return 0.0  # 实际实现中需要维护命中统计
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """获取批处理统计信息"""
        with self.lock:
            batch_counts = {key: len(requests) for key, requests in self.batch_requests.items()}
            return {
                "batch_queues": batch_counts,
                "total_batched_requests": sum(batch_counts.values())
            }
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """获取速率限制统计信息"""
        with self.lock:
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            user_stats = {}
            for user_id, requests in self.rate_limits.items():
                recent_requests = [req for req in requests if req > one_minute_ago]
                user_stats[user_id] = len(recent_requests)
            
            return {
                "user_rate_limits": user_stats,
                "total_active_users": len(user_stats)
            }

class SmartRequestBatcher:
    """智能请求批处理器"""
    
    def __init__(self, optimization_manager: APIOptimizationManager):
        self.optimization_manager = optimization_manager
        self.batch_interval = 2.0  # 批处理间隔（秒）
        self.max_batch_size = 5
        self.batch_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_request(self, request: APIRequest):
        """添加请求到批处理器"""
        batch_key = f"{request.ai_name}_{request.action}"
        
        # 检查是否已有批处理任务
        if batch_key not in self.batch_tasks or self.batch_tasks[batch_key].done():
            # 创建新的批处理任务
            self.batch_tasks[batch_key] = asyncio.create_task(
                self._process_batch(batch_key)
            )
        
        # 添加请求到批处理队列
        self.optimization_manager.add_request_to_batch(request)
    
    async def _process_batch(self, batch_key: str):
        """处理批处理请求"""
        await asyncio.sleep(self.batch_interval)
        
        # 获取批处理请求
        requests = self.optimization_manager.get_batch_requests(
            batch_key.split('_')[0],  # ai_name
            batch_key.split('_')[1],  # action
            self.max_batch_size
        )
        
        if requests:
            logger.info(f"处理批处理请求: {batch_key}, 数量: {len(requests)}")
            # 这里可以调用实际的AI处理函数
            await self._process_requests_batch(requests)
    
    async def _process_requests_batch(self, requests: List[APIRequest]):
        """批量处理请求"""
        # 这里实现批量处理逻辑
        # 可以将多个相似请求合并为一个请求
        pass

class RequestDeduplicator:
    """请求去重器"""
    
    def __init__(self):
        self.recent_requests: Dict[str, float] = {}
        self.duplicate_threshold = 5.0  # 5秒内的重复请求被认为是重复
    
    def is_duplicate(self, prompt: str, user_id: str) -> bool:
        """检查是否为重复请求"""
        request_key = f"{user_id}_{hashlib.md5(prompt.encode()).hexdigest()}"
        current_time = time.time()
        
        if request_key in self.recent_requests:
            if current_time - self.recent_requests[request_key] < self.duplicate_threshold:
                return True
        
        self.recent_requests[request_key] = current_time
        return False
    
    def cleanup_old_requests(self):
        """清理旧的请求记录"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.recent_requests.items()
            if current_time - timestamp > self.duplicate_threshold
        ]
        
        for key in expired_keys:
            del self.recent_requests[key] 