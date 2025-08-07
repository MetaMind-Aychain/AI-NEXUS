"""
共享记忆系统实现

负责存储和管理多AI协作过程中的事件、知识和项目状态
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import pickle

from gpt_engineer.core.default.disk_memory import DiskMemory

from ..core.base_interfaces import BaseSharedMemory, DevelopmentEvent


class SharedMemoryManager(BaseSharedMemory):
    """
    共享记忆管理器
    
    功能：
    - 事件存储和检索
    - 知识库管理
    - 项目状态跟踪
    - 相似案例查找
    - 经验学习和积累
    """
    
    def __init__(self, base_path: str, db_name: str = "shared_memory.db"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 文件存储（基于DiskMemory）
        self.disk_memory = DiskMemory(self.base_path / "files")
        
        # SQLite数据库存储结构化数据
        self.db_path = self.base_path / db_name
        self.init_database()
        
        # 内存缓存
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        self.last_cache_cleanup = datetime.now()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT,
                    files_affected TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    project_id TEXT,
                    session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    confidence REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_states (
                    id TEXT PRIMARY KEY,
                    project_id TEXT UNIQUE NOT NULL,
                    state TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS similarity_cache (
                    id TEXT PRIMARY KEY,
                    context_hash TEXT NOT NULL,
                    similar_cases TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以优化查询性能
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge(tags)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_similarity_hash ON similarity_cache(context_hash)')
    
    def store_event(self, event: DevelopmentEvent) -> None:
        """
        存储开发事件
        
        Args:
            event: 开发事件
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO events 
                (id, timestamp, event_type, actor, description, details, 
                 files_affected, success, error_message, project_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type,
                event.actor,
                event.description,
                json.dumps(event.details),
                json.dumps(event.files_affected),
                event.success,
                event.error_message,
                event.details.get('project_id'),
                event.details.get('session_id')
            ))
        
        # 清理过期缓存
        self._cleanup_cache_if_needed()
        
        # 触发学习更新
        self._update_learning_from_event(event)
    
    def retrieve_events(self, filters: Dict[str, Any]) -> List[DevelopmentEvent]:
        """
        检索开发事件
        
        Args:
            filters: 过滤条件
                - event_type: 事件类型
                - actor: 执行者
                - project_id: 项目ID
                - success: 是否成功
                - start_time: 开始时间
                - end_time: 结束时间
                - limit: 结果数量限制
        
        Returns:
            List[DevelopmentEvent]: 事件列表
        """
        # 构建查询条件
        conditions = []
        params = []
        
        if 'event_type' in filters:
            conditions.append('event_type = ?')
            params.append(filters['event_type'])
        
        if 'actor' in filters:
            conditions.append('actor = ?')
            params.append(filters['actor'])
        
        if 'project_id' in filters:
            conditions.append('project_id = ?')
            params.append(filters['project_id'])
        
        if 'success' in filters:
            conditions.append('success = ?')
            params.append(filters['success'])
        
        if 'start_time' in filters:
            conditions.append('timestamp >= ?')
            params.append(filters['start_time'])
        
        if 'end_time' in filters:
            conditions.append('timestamp <= ?')
            params.append(filters['end_time'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        limit_clause = f"LIMIT {filters.get('limit', 100)}"
        
        query = f'''
            SELECT * FROM events 
            WHERE {where_clause} 
            ORDER BY timestamp DESC 
            {limit_clause}
        '''
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # 转换为DevelopmentEvent对象
        events = []
        for row in rows:
            event = DevelopmentEvent(
                event_id=row['id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                event_type=row['event_type'],
                actor=row['actor'],
                description=row['description'],
                details=json.loads(row['details']) if row['details'] else {},
                files_affected=json.loads(row['files_affected']) if row['files_affected'] else [],
                success=bool(row['success']),
                error_message=row['error_message']
            )
            events.append(event)
        
        return events
    
    def store_knowledge(self, key: str, knowledge: Dict[str, Any]) -> None:
        """
        存储知识
        
        Args:
            key: 知识键
            knowledge: 知识内容
        """
        knowledge_id = str(uuid.uuid4())
        category = knowledge.get('category', 'general')
        content = json.dumps(knowledge)
        tags = json.dumps(knowledge.get('tags', []))
        confidence = knowledge.get('confidence', 1.0)
        
        with sqlite3.connect(self.db_path) as conn:
            # 尝试更新现有知识
            conn.execute('''
                UPDATE knowledge 
                SET content = ?, tags = ?, confidence = ?, 
                    usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', (content, tags, confidence, key))
            
            # 如果没有更新任何行，则插入新记录
            if conn.total_changes == 0:
                conn.execute('''
                    INSERT INTO knowledge 
                    (id, key, category, content, tags, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (knowledge_id, key, category, content, tags, confidence))
        
        # 同时存储到文件系统（用于大型数据）
        if knowledge.get('large_data'):
            self.disk_memory[f"knowledge/{key}"] = pickle.dumps(knowledge['large_data'])
    
    def retrieve_knowledge(self, key: str) -> Optional[Dict[str, Any]]:
        """
        检索知识
        
        Args:
            key: 知识键
            
        Returns:
            Optional[Dict[str, Any]]: 知识内容
        """
        # 检查缓存
        cache_key = f"knowledge_{key}"
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if datetime.now() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM knowledge WHERE key = ?', (key,)
            )
            row = cursor.fetchone()
        
        if row:
            knowledge = json.loads(row['content'])
            
            # 加载大型数据
            large_data_key = f"knowledge/{key}"
            if large_data_key in self.disk_memory:
                knowledge['large_data'] = pickle.loads(self.disk_memory[large_data_key])
            
            # 更新使用计数
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'UPDATE knowledge SET usage_count = usage_count + 1 WHERE key = ?',
                    (key,)
                )
            
            # 缓存结果
            self.cache[cache_key] = {
                'data': knowledge,
                'timestamp': datetime.now()
            }
            
            return knowledge
        
        return None
    
    def find_similar_cases(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        查找相似案例
        
        Args:
            context: 上下文信息
            
        Returns:
            List[Dict[str, Any]]: 相似案例列表
        """
        # 生成上下文哈希用于缓存
        context_str = json.dumps(context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()
        
        # 检查缓存
        cached_result = self._get_cached_similarity(context_hash)
        if cached_result:
            return cached_result
        
        similar_cases = []
        
        # 基于事件历史查找相似案例
        event_similarities = self._find_similar_events(context)
        similar_cases.extend(event_similarities)
        
        # 基于知识库查找相似案例
        knowledge_similarities = self._find_similar_knowledge(context)
        similar_cases.extend(knowledge_similarities)
        
        # 按相似度排序
        similar_cases.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # 限制返回数量
        similar_cases = similar_cases[:10]
        
        # 缓存结果
        self._cache_similarity_result(context_hash, similar_cases)
        
        return similar_cases
    
    def update_project_state(self, project_id: str, state: Dict[str, Any]) -> None:
        """
        更新项目状态
        
        Args:
            project_id: 项目ID
            state: 项目状态
        """
        state_json = json.dumps(state)
        metadata = json.dumps({
            'last_updated': datetime.now().isoformat(),
            'update_count': state.get('update_count', 0) + 1
        })
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO project_states 
                (id, project_id, state, metadata, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (str(uuid.uuid4()), project_id, state_json, metadata))
    
    def get_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目状态
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict[str, Any]]: 项目状态
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM project_states WHERE project_id = ?', (project_id,)
            )
            row = cursor.fetchone()
        
        if row:
            state = json.loads(row['state'])
            metadata = json.loads(row['metadata'])
            state['_metadata'] = metadata
            return state
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            # 事件统计
            event_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_events,
                    COUNT(DISTINCT event_type) as event_types,
                    COUNT(DISTINCT actor) as actors,
                    COUNT(DISTINCT project_id) as projects
                FROM events
            ''').fetchone()
            
            # 知识库统计
            knowledge_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_knowledge,
                    COUNT(DISTINCT category) as categories,
                    AVG(confidence) as avg_confidence,
                    SUM(usage_count) as total_usage
                FROM knowledge
            ''').fetchone()
            
            # 最近活动
            recent_activity = conn.execute('''
                SELECT event_type, COUNT(*) as count
                FROM events 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 5
            ''').fetchall()
        
        return {
            'events': {
                'total': event_stats[0],
                'successful': event_stats[1],
                'types': event_stats[2],
                'actors': event_stats[3],
                'projects': event_stats[4]
            },
            'knowledge': {
                'total': knowledge_stats[0],
                'categories': knowledge_stats[1],
                'avg_confidence': knowledge_stats[2],
                'total_usage': knowledge_stats[3]
            },
            'recent_activity': [
                {'event_type': row[0], 'count': row[1]} 
                for row in recent_activity
            ]
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            # 删除旧事件
            deleted_events = conn.execute(
                'DELETE FROM events WHERE timestamp < ?',
                (cutoff_date.isoformat(),)
            ).rowcount
            
            # 删除旧的相似性缓存
            deleted_cache = conn.execute(
                'DELETE FROM similarity_cache WHERE created_at < ?',
                (cutoff_date.isoformat(),)
            ).rowcount
            
            # 删除未使用的知识
            deleted_knowledge = conn.execute(
                'DELETE FROM knowledge WHERE usage_count = 0 AND created_at < ?',
                (cutoff_date.isoformat(),)
            ).rowcount
        
        return {
            'deleted_events': deleted_events,
            'deleted_cache': deleted_cache,
            'deleted_knowledge': deleted_knowledge
        }
    
    def _find_similar_events(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于事件历史查找相似案例"""
        similar_cases = []
        
        # 查找相似的需求类型
        requirements = context.get('requirements', {})
        if requirements:
            req_keywords = self._extract_keywords(str(requirements))
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 查找包含相似关键词的成功事件
                for keyword in req_keywords[:5]:  # 限制关键词数量
                    cursor = conn.execute('''
                        SELECT * FROM events 
                        WHERE success = 1 AND description LIKE ? 
                        ORDER BY timestamp DESC LIMIT 5
                    ''', (f'%{keyword}%',))
                    
                    for row in cursor.fetchall():
                        case = {
                            'type': 'event_similarity',
                            'event_id': row['id'],
                            'description': row['description'],
                            'event_type': row['event_type'],
                            'details': json.loads(row['details']) if row['details'] else {},
                            'similarity_score': 0.7,  # 基础相似度
                            'match_keyword': keyword
                        }
                        similar_cases.append(case)
        
        return similar_cases
    
    def _find_similar_knowledge(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于知识库查找相似案例"""
        similar_cases = []
        
        # 提取上下文关键词
        context_keywords = self._extract_keywords(str(context))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 查找标签匹配的知识
            for keyword in context_keywords[:5]:
                cursor = conn.execute('''
                    SELECT * FROM knowledge 
                    WHERE tags LIKE ? OR content LIKE ?
                    ORDER BY confidence DESC, usage_count DESC 
                    LIMIT 3
                ''', (f'%{keyword}%', f'%{keyword}%'))
                
                for row in cursor.fetchall():
                    case = {
                        'type': 'knowledge_similarity',
                        'key': row['key'],
                        'category': row['category'],
                        'content': json.loads(row['content']),
                        'confidence': row['confidence'],
                        'usage_count': row['usage_count'],
                        'similarity_score': min(0.8, row['confidence']),
                        'match_keyword': keyword
                    }
                    similar_cases.append(case)
        
        return similar_cases
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        import re
        
        # 简单的关键词提取
        text = text.lower()
        words = re.findall(r'\b\w{3,}\b', text)
        
        # 过滤常用词
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
            'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        keywords = [word for word in words if word not in stopwords]
        
        # 返回最常见的关键词
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _get_cached_similarity(self, context_hash: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的相似性结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT similar_cases FROM similarity_cache 
                WHERE context_hash = ? AND created_at > datetime('now', '-1 day')
            ''', (context_hash,))
            row = cursor.fetchone()
        
        if row:
            return json.loads(row[0])
        return None
    
    def _cache_similarity_result(self, context_hash: str, similar_cases: List[Dict[str, Any]]):
        """缓存相似性结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO similarity_cache 
                (id, context_hash, similar_cases)
                VALUES (?, ?, ?)
            ''', (str(uuid.uuid4()), context_hash, json.dumps(similar_cases)))
    
    def _update_learning_from_event(self, event: DevelopmentEvent):
        """从事件中学习并更新知识库"""
        # 如果是成功的代码生成事件，提取经验
        if event.success and event.event_type == 'code_generation':
            self._extract_coding_experience(event)
        
        # 如果是测试失败事件，记录常见问题
        elif not event.success and event.event_type == 'test_failure':
            self._record_common_issue(event)
        
        # 如果是质量分析事件，更新质量模式
        elif event.event_type == 'quality_analysis':
            self._update_quality_patterns(event)
    
    def _extract_coding_experience(self, event: DevelopmentEvent):
        """从成功的代码生成中提取经验"""
        details = event.details
        if 'prompt_length' in details and 'files_count' in details:
            experience = {
                'category': 'coding_experience',
                'pattern': 'successful_generation',
                'prompt_length': details['prompt_length'],
                'files_generated': details['files_count'],
                'timestamp': event.timestamp.isoformat(),
                'tags': ['code_generation', 'success']
            }
            
            key = f"coding_exp_{event.event_id}"
            self.store_knowledge(key, experience)
    
    def _record_common_issue(self, event: DevelopmentEvent):
        """记录常见问题"""
        if event.error_message:
            issue = {
                'category': 'common_issues',
                'error_type': event.event_type,
                'error_message': event.error_message,
                'frequency': 1,
                'timestamp': event.timestamp.isoformat(),
                'tags': ['error', 'debugging', event.event_type]
            }
            
            # 检查是否已存在相似问题
            error_hash = hashlib.md5(event.error_message.encode()).hexdigest()[:8]
            key = f"issue_{error_hash}"
            
            existing = self.retrieve_knowledge(key)
            if existing:
                existing['frequency'] += 1
                self.store_knowledge(key, existing)
            else:
                self.store_knowledge(key, issue)
    
    def _update_quality_patterns(self, event: DevelopmentEvent):
        """更新质量模式"""
        details = event.details
        if 'quality_score' in details:
            pattern = {
                'category': 'quality_patterns',
                'score': details['quality_score'],
                'issues_count': len(details.get('issues', [])),
                'timestamp': event.timestamp.isoformat(),
                'tags': ['quality', 'analysis']
            }
            
            key = f"quality_pattern_{event.event_id}"
            self.store_knowledge(key, pattern)
    
    def _cleanup_cache_if_needed(self):
        """定期清理内存缓存"""
        now = datetime.now()
        if now - self.last_cache_cleanup > timedelta(hours=1):
            # 清理过期缓存
            expired_keys = [
                key for key, value in self.cache.items()
                if now - value['timestamp'] > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            self.last_cache_cleanup = now