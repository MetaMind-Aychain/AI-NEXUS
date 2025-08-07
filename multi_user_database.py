#!/usr/bin/env python3
"""
多用户数据库管理器
支持用户认证、项目隔离、AI交互记录等功能
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("多用户数据库")

@dataclass
class User:
    """用户数据模型"""
    id: str
    username: str
    email: Optional[str] = None
    created_at: str = ""
    last_login: str = ""
    status: str = "active"
    api_usage_count: int = 0
    api_usage_limit: int = 1000
    subscription_tier: str = "basic"  # basic, pro, enterprise
    api_balance: int = 0  # API配额余额
    total_recharge: float = 0.0  # 总充值金额
    invitation_code: str = ""  # 邀请码
    inviter_id: Optional[str] = None  # 邀请人ID
    total_invitations: int = 0  # 总邀请人数
    total_rewards: int = 0  # 总奖励配额
    vip_level: int = 0  # VIP等级 (0=普通, 1=高级, 2=至尊)
    vip_expires_at: Optional[str] = None  # VIP到期时间
    vip_credits: int = 0  # VIP专属配额
    blockchain_profile_address: Optional[str] = None  # 区块链档案地址
    blockchain_profile_hash: Optional[str] = None  # 区块链档案哈希
    blockchain_profile_updated_at: Optional[str] = None  # 区块链档案更新时间

@dataclass
class Project:
    """项目数据模型"""
    id: str
    user_id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str
    project_path: str
    files_count: int = 0
    ai_generated: bool = True
    project_type: str = "web_application"
    tech_stack: str = "[]"  # JSON字符串
    completion_percentage: float = 0.0
    estimated_duration: int = 0  # 分钟
    actual_duration: int = 0  # 分钟
    deployment_status: str = "未部署"  # 未部署, 部署中, 已部署, 部署失败
    deployment_url: Optional[str] = None  # 部署链接
    document_confirmed: bool = False  # 文档是否确认
    frontend_confirmed: bool = False  # 前端是否确认
    document_content: str = ""  # 文档内容
    frontend_preview_url: Optional[str] = None  # 前端预览链接
    deployed_at: Optional[str] = None  # 部署时间
    blockchain_deployed: bool = False  # 是否已区块链部署
    blockchain_address: Optional[str] = None  # 区块链地址
    blockchain_deployed_at: Optional[str] = None  # 区块链部署时间
    blockchain_network: str = "solana"  # 区块链网络
    blockchain_transaction_hash: Optional[str] = None  # 区块链交易哈希
    document_status: str = "draft"  # 文档状态
    frontend_status: str = "draft"  # 前端状态
    document_confirmed_at: Optional[str] = None  # 文档确认时间
    frontend_confirmed_at: Optional[str] = None  # 前端确认时间
    frontend_content: Optional[str] = None  # 前端内容

@dataclass
class AIInteraction:
    """AI交互数据模型"""
    id: int = 0
    user_id: str = ""
    project_id: str = ""
    ai_name: str = ""
    action: str = ""
    input_prompt: str = ""
    ai_response: str = ""
    timestamp: str = ""
    success: bool = True
    tokens_used: int = 0
    cost: float = 0.0
    response_time: float = 0.0

@dataclass
class AICollaboration:
    """AI协作数据模型"""
    id: int = 0
    user_id: str = ""
    project_id: str = ""
    collaboration_step: str = ""
    involved_ais: str = ""  # JSON字符串
    result_summary: str = ""
    timestamp: str = ""
    quality_score: float = 0.0
    efficiency_score: float = 0.0

@dataclass
class RechargeRecord:
    """充值记录数据模型"""
    id: int = 0
    user_id: str = ""
    amount: float = 0.0
    api_quota: int = 0
    payment_method: str = ""  # wechat, alipay, other
    payment_status: str = "pending"  # pending, success, failed
    transaction_id: str = ""
    created_at: str = ""
    processed_at: str = ""

@dataclass
class InvitationRecord:
    """邀请记录数据模型"""
    id: int = 0
    inviter_id: str = ""
    invitee_id: str = ""
    invitation_code: str = ""
    reward_quota: int = 0
    bonus_percentage: float = 0.0
    status: str = "pending"  # pending, completed
    created_at: str = ""
    completed_at: str = ""

@dataclass
class ShareRecord:
    """分享记录数据模型"""
    id: int = 0
    user_id: str = ""
    share_type: str = ""  # project, platform, achievement
    share_content: str = ""
    share_platform: str = ""  # wechat, weibo, qq, etc.
    reward_quota: int = 0
    created_at: str = ""

@dataclass
class DeploymentRecord:
    """部署记录数据模型"""
    id: int = 0
    user_id: str = ""
    project_id: str = ""
    deployment_type: str = ""  # docker, static, serverless
    deployment_url: str = ""
    deployment_status: str = "deploying"  # deploying, success, failed
    error_message: str = ""
    created_at: str = ""
    deployed_at: str = ""

class MultiUserDatabaseManager:
    """多用户数据库管理器"""
    
    def __init__(self, db_path: str = "multi_user_ai_platform.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 先检查并升级数据库结构
            self._upgrade_database_schema(conn)
            # 用户表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    created_at TEXT,
                    last_login TEXT,
                    status TEXT DEFAULT 'active',
                    api_usage_count INTEGER DEFAULT 0,
                    api_usage_limit INTEGER DEFAULT 1000,
                    subscription_tier TEXT DEFAULT 'basic',
                    api_balance INTEGER DEFAULT 0,
                    total_recharge REAL DEFAULT 0.0,
                    invitation_code TEXT,
                    inviter_id TEXT,
                    total_invitations INTEGER DEFAULT 0,
                    total_rewards INTEGER DEFAULT 0
                )
            """)
            
            # 项目表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    project_path TEXT,
                    files_count INTEGER DEFAULT 0,
                    ai_generated BOOLEAN DEFAULT TRUE,
                    project_type TEXT DEFAULT 'web_application',
                    tech_stack TEXT DEFAULT '[]',
                    completion_percentage REAL DEFAULT 0.0,
                    estimated_duration INTEGER DEFAULT 0,
                    actual_duration INTEGER DEFAULT 0,
                    deployment_status TEXT DEFAULT '未部署',
                    deployment_url TEXT,
                    document_confirmed BOOLEAN DEFAULT FALSE,
                    frontend_confirmed BOOLEAN DEFAULT FALSE,
                    document_content TEXT DEFAULT '',
                    frontend_preview_url TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # AI交互表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_id TEXT,
                    ai_name TEXT,
                    action TEXT,
                    input_prompt TEXT,
                    ai_response TEXT,
                    timestamp TEXT,
                    success BOOLEAN,
                    tokens_used INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    response_time REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            # AI协作表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_collaborations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_id TEXT,
                    collaboration_step TEXT,
                    involved_ais TEXT,
                    result_summary TEXT,
                    timestamp TEXT,
                    quality_score REAL DEFAULT 0.0,
                    efficiency_score REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            # API使用统计表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT,
                    api_calls INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # 系统配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)
            
            # 充值记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recharge_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    api_quota INTEGER NOT NULL,
                    payment_method TEXT,
                    payment_status TEXT DEFAULT 'pending',
                    transaction_id TEXT,
                    created_at TEXT,
                    processed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # 邀请记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id TEXT NOT NULL,
                    invitee_id TEXT,
                    invitation_code TEXT NOT NULL,
                    reward_quota INTEGER DEFAULT 0,
                    bonus_percentage REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (inviter_id) REFERENCES users (id),
                    FOREIGN KEY (invitee_id) REFERENCES users (id)
                )
            """)
            
            # 分享记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS share_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    share_type TEXT,
                    share_content TEXT,
                    share_platform TEXT,
                    reward_quota INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # 部署记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deployment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    deployment_type TEXT,
                    deployment_url TEXT,
                    deployment_status TEXT DEFAULT 'deploying',
                    error_message TEXT,
                    created_at TEXT,
                    deployed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_user_id ON ai_interactions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_project_id ON ai_interactions(project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_collaborations_user_id ON ai_collaborations(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_stats_user_date ON api_usage_stats(user_id, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_recharge_records_user_id ON recharge_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitation_records_inviter ON invitation_records(inviter_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_deployment_records_project ON deployment_records(project_id)")
    
    def _upgrade_database_schema(self, conn):
        """升级数据库结构以支持新功能"""
        try:
            # 检查是否需要添加新列到users表
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'api_balance' not in columns:
                logger.info("升级数据库：添加新列到users表")
                conn.execute("ALTER TABLE users ADD COLUMN api_balance INTEGER DEFAULT 100")
                conn.execute("ALTER TABLE users ADD COLUMN total_recharge REAL DEFAULT 0.0")
                conn.execute("ALTER TABLE users ADD COLUMN invitation_code TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN inviter_id TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN total_invitations INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN total_rewards INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN vip_level INTEGER DEFAULT 0")  # 0=普通, 1=高级, 2=至尊
                conn.execute("ALTER TABLE users ADD COLUMN vip_expires_at TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN vip_credits INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN blockchain_profile_address TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN blockchain_profile_hash TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN blockchain_profile_updated_at TEXT")
                
            # 检查是否需要添加新列到projects表
            cursor = conn.execute("PRAGMA table_info(projects)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'deployment_status' not in columns:
                logger.info("升级数据库：添加新列到projects表")
                conn.execute("ALTER TABLE projects ADD COLUMN deployment_status TEXT DEFAULT '未部署'")
                conn.execute("ALTER TABLE projects ADD COLUMN deployment_url TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN document_confirmed BOOLEAN DEFAULT FALSE")
                conn.execute("ALTER TABLE projects ADD COLUMN frontend_confirmed BOOLEAN DEFAULT FALSE")
                conn.execute("ALTER TABLE projects ADD COLUMN document_content TEXT DEFAULT ''")
                conn.execute("ALTER TABLE projects ADD COLUMN frontend_preview_url TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN deployed_at TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN blockchain_deployed BOOLEAN DEFAULT FALSE")
                conn.execute("ALTER TABLE projects ADD COLUMN blockchain_address TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN blockchain_deployed_at TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN blockchain_network TEXT DEFAULT 'polygon'")
                conn.execute("ALTER TABLE projects ADD COLUMN blockchain_transaction_hash TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN document_status TEXT DEFAULT 'draft'")
                conn.execute("ALTER TABLE projects ADD COLUMN frontend_status TEXT DEFAULT 'draft'")
                conn.execute("ALTER TABLE projects ADD COLUMN document_confirmed_at TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN frontend_confirmed_at TEXT")
                conn.execute("ALTER TABLE projects ADD COLUMN frontend_content TEXT")
                
            # 升级users表 - 添加VIP相关字段
            cursor = conn.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
            
            if 'vip_level' not in user_columns:
                logger.info("升级数据库：添加VIP字段到users表")
                conn.execute("ALTER TABLE users ADD COLUMN vip_level INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN vip_expires_at TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN vip_credits INTEGER DEFAULT 0")
            
            logger.info("数据库结构升级完成")
            
        except Exception as e:
            logger.error(f"数据库升级失败: {e}")
    
    def create_user(self, username: str, email: str = None, subscription_tier: str = "basic", inviter_code: str = None) -> str:
        """创建用户"""
        user_id = str(uuid.uuid4())
        invitation_code = self._generate_invitation_code()
        inviter_id = None
        
        # 处理邀请关系
        if inviter_code:
            inviter_id = self._get_user_by_invitation_code(inviter_code)
        
        # 新用户福利：30配额 + 一次免费测试 + 一次充值半价
        initial_balance = 30  # 新用户配额
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO users (id, username, email, created_at, subscription_tier, 
                                 invitation_code, inviter_id, api_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, email, datetime.now().isoformat(), subscription_tier, 
                  invitation_code, inviter_id, initial_balance))
            
            # 如果有邀请人，奖励邀请人
            if inviter_id:
                self._reward_inviter(inviter_id, user_id, invitation_code)
        
        logger.info(f"创建用户: {username} (ID: {user_id})，初始配额: {initial_balance}")
        return user_id
    
    def _generate_invitation_code(self) -> str:
        """生成邀请码"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def _get_user_by_invitation_code(self, invitation_code: str) -> Optional[str]:
        """根据邀请码获取用户ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM users WHERE invitation_code = ?", (invitation_code,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def _reward_inviter(self, inviter_id: str, invitee_id: str, invitation_code: str):
        """奖励邀请人"""
        with sqlite3.connect(self.db_path) as conn:
            # 更新邀请人的邀请数量和奖励配额
            conn.execute("""
                UPDATE users 
                SET total_invitations = total_invitations + 1,
                    total_rewards = total_rewards + 30,
                    api_balance = api_balance + 30
                WHERE id = ?
            """, (inviter_id,))
            
            # 记录邀请记录
            conn.execute("""
                INSERT INTO invitation_records 
                (inviter_id, invitee_id, invitation_code, reward_quota, status, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (inviter_id, invitee_id, invitation_code, 30, 'completed', 
                  datetime.now().isoformat(), datetime.now().isoformat()))
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                # 处理可能缺失的字段，提供默认值
                user_data = dict(row)
                
                # 为可能缺失的字段提供默认值
                defaults = {
                    'vip_level': 0,
                    'vip_expires_at': None,
                    'vip_credits': 0,
                    'blockchain_profile_address': None,
                    'blockchain_profile_hash': None,
                    'blockchain_profile_updated_at': None,
                    'api_balance': 0,
                    'total_recharge': 0.0,
                    'invitation_code': '',
                    'inviter_id': None,
                    'total_invitations': 0,
                    'total_rewards': 0
                }
                
                for key, default_value in defaults.items():
                    if key not in user_data:
                        user_data[key] = default_value
                        
                return User(**user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                # 处理可能缺失的字段，提供默认值
                user_data = dict(row)
                
                # 为可能缺失的字段提供默认值
                defaults = {
                    'vip_level': 0,
                    'vip_expires_at': None,
                    'vip_credits': 0,
                    'blockchain_profile_address': None,
                    'blockchain_profile_hash': None,
                    'blockchain_profile_updated_at': None,
                    'api_balance': 0,
                    'total_recharge': 0.0,
                    'invitation_code': '',
                    'inviter_id': None,
                    'total_invitations': 0,
                    'total_rewards': 0
                }
                
                for key, default_value in defaults.items():
                    if key not in user_data:
                        user_data[key] = default_value
                        
                return User(**user_data)
        return None
    
    def update_user_login(self, user_id: str):
        """更新用户最后登录时间"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now().isoformat(), user_id))
    
    def save_project(self, project_data: Dict):
        """保存项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO projects 
                (id, user_id, name, description, status, created_at, updated_at, 
                 project_path, files_count, ai_generated, project_type, tech_stack,
                 completion_percentage, estimated_duration, actual_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data['id'],
                project_data['user_id'],
                project_data['name'],
                project_data['description'],
                project_data['status'],
                project_data['created_at'],
                project_data['updated_at'],
                project_data['project_path'],
                project_data['files_count'],
                project_data.get('ai_generated', True),
                project_data.get('project_type', 'web_application'),
                json.dumps(project_data.get('tech_stack', [])),
                project_data.get('completion_percentage', 0.0),
                project_data.get('estimated_duration', 0),
                project_data.get('actual_duration', 0)
            ))
    
    def get_user_projects(self, user_id: str) -> List[Project]:
        """获取用户项目列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM projects 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            return [Project(**dict(row)) for row in cursor.fetchall()]
    
    def log_ai_interaction(self, user_id: str, project_id: str, ai_name: str, action: str, 
                          input_prompt: str, ai_response: str, success: bool = True,
                          tokens_used: int = 0, cost: float = 0.0, response_time: float = 0.0):
        """记录AI交互"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_interactions 
                (user_id, project_id, ai_name, action, input_prompt, ai_response, 
                 timestamp, success, tokens_used, cost, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, project_id, ai_name, action, input_prompt, ai_response, 
                  datetime.now().isoformat(), success, tokens_used, cost, response_time))
            
            # 更新用户API使用统计
            conn.execute("""
                UPDATE users SET api_usage_count = api_usage_count + 1 
                WHERE id = ?
            """, (user_id,))
    
    def log_ai_collaboration(self, user_id: str, project_id: str, step: str, 
                           involved_ais: List[str], result_summary: str,
                           quality_score: float = 0.0, efficiency_score: float = 0.0):
        """记录AI协作"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_collaborations 
                (user_id, project_id, collaboration_step, involved_ais, result_summary, 
                 timestamp, quality_score, efficiency_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, project_id, step, json.dumps(involved_ais), result_summary, 
                  datetime.now().isoformat(), quality_score, efficiency_score))
    
    def get_user_api_usage(self, user_id: str, date: str = None) -> Dict[str, Any]:
        """获取用户API使用统计"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM api_usage_stats 
                WHERE user_id = ? AND date = ?
            """, (user_id, date))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                return {
                    "user_id": user_id,
                    "date": date,
                    "api_calls": 0,
                    "tokens_used": 0,
                    "total_cost": 0.0
                }
    
    def update_api_usage_stats(self, user_id: str, tokens_used: int, cost: float):
        """更新API使用统计"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已有今日记录
            cursor = conn.execute("""
                SELECT id FROM api_usage_stats 
                WHERE user_id = ? AND date = ?
            """, (user_id, date))
            
            if cursor.fetchone():
                # 更新现有记录
                conn.execute("""
                    UPDATE api_usage_stats 
                    SET api_calls = api_calls + 1, 
                        tokens_used = tokens_used + ?, 
                        total_cost = total_cost + ?
                    WHERE user_id = ? AND date = ?
                """, (tokens_used, cost, user_id, date))
            else:
                # 创建新记录
                conn.execute("""
                    INSERT INTO api_usage_stats 
                    (user_id, date, api_calls, tokens_used, total_cost)
                    VALUES (?, ?, 1, ?, ?)
                """, (user_id, date, tokens_used, cost))
    
    def check_user_api_limit(self, user_id: str) -> bool:
        """检查用户API使用限制"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        return user.api_usage_count < user.api_usage_limit
    
    def get_system_config(self, key: str, default: str = "") -> str:
        """获取系统配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def set_system_config(self, key: str, value: str, description: str = ""):
        """设置系统配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_config (key, value, description, updated_at)
                VALUES (?, ?, ?, ?)
            """, (key, value, description, datetime.now().isoformat()))
    
    # 充值相关方法
    def create_recharge_record(self, user_id: str, amount: float, api_quota: int, 
                              payment_method: str, transaction_id: str = "") -> int:
        """创建充值记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO recharge_records 
                (user_id, amount, api_quota, payment_method, transaction_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, api_quota, payment_method, transaction_id, datetime.now().isoformat()))
            return cursor.lastrowid
    
    def complete_recharge(self, record_id: int) -> bool:
        """完成充值"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取充值记录
            cursor = conn.execute("""
                SELECT user_id, api_quota, amount FROM recharge_records 
                WHERE id = ? AND payment_status = 'pending'
            """, (record_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            user_id, api_quota, amount = row
            
            # 更新充值记录状态
            conn.execute("""
                UPDATE recharge_records 
                SET payment_status = 'success', processed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), record_id))
            
            # 更新用户余额
            conn.execute("""
                UPDATE users 
                SET api_balance = api_balance + ?, total_recharge = total_recharge + ?
                WHERE id = ?
            """, (api_quota, amount, user_id))
            
            # 如果用户有邀请人，给邀请人15%奖励
            cursor = conn.execute("SELECT inviter_id FROM users WHERE id = ?", (user_id,))
            inviter_row = cursor.fetchone()
            if inviter_row and inviter_row[0]:
                inviter_id = inviter_row[0]
                bonus_quota = int(api_quota * 0.15)
                conn.execute("""
                    UPDATE users 
                    SET api_balance = api_balance + ?, total_rewards = total_rewards + ?
                    WHERE id = ?
                """, (bonus_quota, bonus_quota, inviter_id))
                
                # 记录奖励
                conn.execute("""
                    INSERT INTO invitation_records 
                    (inviter_id, invitee_id, invitation_code, reward_quota, bonus_percentage, 
                     status, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (inviter_id, user_id, 'recharge_bonus', bonus_quota, 15.0, 'completed',
                      datetime.now().isoformat(), datetime.now().isoformat()))
            
            return True
    
    def get_user_recharge_records(self, user_id: str) -> List[Dict]:
        """获取用户充值记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM recharge_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # 分享相关方法
    def create_share_record(self, user_id: str, share_type: str, share_content: str, 
                           share_platform: str, reward_quota: int = 5) -> int:
        """创建分享记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO share_records 
                (user_id, share_type, share_content, share_platform, reward_quota, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, share_type, share_content, share_platform, reward_quota, datetime.now().isoformat()))
            
            # 奖励用户配额（添加容错处理）
            try:
                conn.execute("""
                    UPDATE users 
                    SET api_balance = COALESCE(api_balance, 0) + ?, 
                        total_rewards = COALESCE(total_rewards, 0) + ?
                    WHERE id = ?
                """, (reward_quota, reward_quota, user_id))
            except Exception as e:
                logger.error(f"更新用户奖励失败: {e}")
                # 如果列不存在，尝试简单更新
                try:
                    conn.execute("UPDATE users SET api_usage_count = api_usage_count WHERE id = ?", (user_id,))
                except:
                    pass
            
            return cursor.lastrowid
    
    def get_user_share_records(self, user_id: str) -> List[Dict]:
        """获取用户分享记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM share_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # 部署相关方法
    def create_deployment_record(self, user_id: str, project_id: str, deployment_type: str) -> int:
        """创建部署记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO deployment_records 
                (user_id, project_id, deployment_type, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, project_id, deployment_type, datetime.now().isoformat()))
            return cursor.lastrowid
    
    def update_deployment_status(self, record_id: int, status: str, deployment_url: str = "", 
                                error_message: str = ""):
        """更新部署状态"""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'success':
                conn.execute("""
                    UPDATE deployment_records 
                    SET deployment_status = ?, deployment_url = ?, deployed_at = ?
                    WHERE id = ?
                """, (status, deployment_url, datetime.now().isoformat(), record_id))
                
                # 更新项目部署状态
                cursor = conn.execute("SELECT project_id FROM deployment_records WHERE id = ?", (record_id,))
                project_id = cursor.fetchone()[0]
                conn.execute("""
                    UPDATE projects 
                    SET deployment_status = '已部署', deployment_url = ?
                    WHERE id = ?
                """, (deployment_url, project_id))
            else:
                conn.execute("""
                    UPDATE deployment_records 
                    SET deployment_status = ?, error_message = ?
                    WHERE id = ?
                """, (status, error_message, record_id))
    
    def get_project_deployment_records(self, project_id: str) -> List[Dict]:
        """获取项目部署记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM deployment_records 
                WHERE project_id = ? 
                ORDER BY created_at DESC
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # 项目文档和前端确认相关方法
    def update_project_document(self, project_id: str, document_content: str, confirmed: bool = False):
        """更新项目文档"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE projects 
                SET document_content = ?, document_confirmed = ?, updated_at = ?
                WHERE id = ?
            """, (document_content, confirmed, datetime.now().isoformat(), project_id))
    
    def update_project_frontend(self, project_id: str, preview_url: str = "", confirmed: bool = False):
        """更新项目前端状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE projects 
                SET frontend_preview_url = ?, frontend_confirmed = ?, updated_at = ?
                WHERE id = ?
            """, (preview_url, confirmed, datetime.now().isoformat(), project_id))
    
    def get_user_invitation_stats(self, user_id: str) -> Dict:
        """获取用户邀请统计"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT COUNT(*) as total_invitations, 
                       COALESCE(SUM(reward_quota), 0) as total_rewards
                FROM invitation_records 
                WHERE inviter_id = ? AND status = 'completed'
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"total_invitations": 0, "total_rewards": 0}
    
    def deduct_api_balance(self, user_id: str, amount: int) -> bool:
        """扣除API配额"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("SELECT api_balance FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                current_balance = row[0] if row[0] is not None else 30  # 默认给30配额
                
                if current_balance < amount:
                    return False
                
                conn.execute("""
                    UPDATE users 
                    SET api_balance = api_balance - ?, api_usage_count = api_usage_count + 1
                    WHERE id = ?
                """, (amount, user_id))
                return True
            except Exception as e:
                logger.error(f"扣除API配额失败: {e}")
                # 如果api_balance列不存在，暂时返回True（兼容老版本）
                return True
    
    def check_first_time_discount(self, user_id: str) -> bool:
        """检查用户是否有首次充值优惠"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT total_recharge FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0] > 0:
                return False  # 已经充值过
            return True  # 首次充值，可享受半价
    
    def has_free_test_used(self, user_id: str) -> bool:
        """检查用户是否已使用免费测试"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM projects 
                WHERE user_id = ? AND ai_generated = TRUE
            """, (user_id,))
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_project(self, project_id: str) -> Project:
        """根据ID获取项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM projects WHERE id = ?
            """, (project_id,))
            row = cursor.fetchone()
            
            if row:
                # 处理可能缺失的字段，提供默认值
                project_data = dict(row)
                
                # 为可能缺失的字段提供默认值
                defaults = {
                    'deployed_at': None,
                    'blockchain_deployed': False,
                    'blockchain_address': None,
                    'blockchain_deployed_at': None,
                    'blockchain_network': 'solana',
                    'blockchain_transaction_hash': None,
                    'document_status': 'draft',
                    'frontend_status': 'draft',
                    'document_confirmed_at': None,
                    'frontend_confirmed_at': None,
                    'frontend_content': None
                }
                
                for key, default_value in defaults.items():
                    if key not in project_data:
                        project_data[key] = default_value
                        
                return Project(**project_data)
            return None 