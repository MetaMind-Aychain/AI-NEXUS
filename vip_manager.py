#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIP会员管理系统
实现三级会员体系：普通、高级、至尊
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VIPLevel:
    """VIP等级配置"""
    level: int
    name: str
    monthly_fee: float
    credits: int
    benefits: list
    commission_bonus: float  # 佣金率加成
    
class VIPManager:
    """VIP会员管理器"""
    
    VIP_LEVELS = {
        0: VIPLevel(0, "常规会员", 0, 0, ["基础AI开发"], 0.0),
        1: VIPLevel(1, "高级会员", 100, 200, [
            "免费一键上云", "免费一键上链", "月赠200配额", 
            "佣金率+5%", "VIP专属分享链接", "邀请用户+20配额"
        ], 0.05),
        2: VIPLevel(2, "至尊会员", 1000, 2000, [
            "高级会员所有权益", "所有功能半折", "特殊要求部署", 
            "月赠2000配额", "专属客服", "优先技术支持"
        ], 0.05)
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_vip_tables()
    
    def init_vip_tables(self):
        """初始化VIP相关表和字段"""
        with sqlite3.connect(self.db_path) as conn:
            # 检查users表是否存在VIP字段
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 添加VIP字段
            if 'vip_level' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN vip_level INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN vip_expires_at TEXT")
                conn.execute("ALTER TABLE users ADD COLUMN vip_credits INTEGER DEFAULT 0")
                logger.info("VIP字段已添加到users表")
            
            # 创建VIP记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vip_records (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    old_level INTEGER DEFAULT 0,
                    new_level INTEGER DEFAULT 0,
                    amount REAL DEFAULT 0.0,
                    credits_granted INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                )
            """)
            
            conn.commit()
            logger.info("VIP表初始化完成")

    def get_user_vip_info(self, user_id: str) -> Dict:
        """获取用户VIP信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute("""
                    SELECT vip_level, vip_expires_at, vip_credits 
                    FROM users WHERE id = ?
                """, (user_id,))
                row = cursor.fetchone()
            except sqlite3.OperationalError as e:
                if "no such column" in str(e):
                    # VIP字段还未添加，返回默认值
                    logger.warning(f"VIP字段缺失: {e}")
                    return {"level": 0, "name": "常规会员", "expired": True}
                else:
                    raise
            
            if not row:
                return {"level": 0, "name": "常规会员", "expired": True}
            
            vip_level = row["vip_level"] or 0
            expires_at = row["vip_expires_at"]
            credits = row["vip_credits"] or 0
            
            # 检查是否过期
            is_expired = True
            if expires_at:
                expire_date = datetime.fromisoformat(expires_at)
                is_expired = datetime.now() > expire_date
            
            if is_expired and vip_level > 0:
                # VIP已过期，降级为普通会员
                self._downgrade_to_basic(user_id)
                vip_level = 0
            
            level_info = self.VIP_LEVELS[vip_level]
            
            return {
                "level": vip_level,
                "name": level_info.name,
                "expires_at": expires_at,
                "expired": is_expired,
                "credits": credits,
                "benefits": level_info.benefits,
                "commission_bonus": level_info.commission_bonus
            }
    
    def upgrade_vip(self, user_id: str, target_level: int, payment_amount: float) -> Dict:
        """升级VIP"""
        if target_level not in self.VIP_LEVELS or target_level == 0:
            raise ValueError("无效的VIP级别")
        
        level_info = self.VIP_LEVELS[target_level]
        
        # 验证支付金额
        if payment_amount < level_info.monthly_fee:
            raise ValueError("支付金额不足")
        
        # 计算到期时间（一个月后）
        expires_at = datetime.now() + timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            # 更新用户VIP状态
            conn.execute("""
                UPDATE users 
                SET vip_level = ?, 
                    vip_expires_at = ?, 
                    vip_credits = vip_credits + ?,
                    api_balance = api_balance + ?
                WHERE id = ?
            """, (target_level, expires_at.isoformat(), level_info.credits, level_info.credits, user_id))
            
            # 记录VIP购买记录
            conn.execute("""
                INSERT INTO vip_records (id, user_id, vip_level, amount, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self._generate_id(), user_id, target_level, payment_amount,
                expires_at.isoformat(), datetime.now().isoformat()
            ))
        
        logger.info(f"用户 {user_id} 升级到 {level_info.name}")
        
        return {
            "status": "success",
            "level": target_level,
            "level_name": level_info.name,
            "expires_at": expires_at.isoformat(),
            "credits_granted": level_info.credits,
            "benefits": level_info.benefits
        }
    
    def renew_vip(self, user_id: str, payment_amount: float) -> Dict:
        """续费VIP"""
        vip_info = self.get_user_vip_info(user_id)
        current_level = vip_info["level"]
        
        if current_level == 0:
            raise ValueError("当前不是VIP会员")
        
        level_info = self.VIP_LEVELS[current_level]
        
        if payment_amount < level_info.monthly_fee:
            raise ValueError("支付金额不足")
        
        # 计算新的到期时间
        current_expires = vip_info.get("expires_at")
        if current_expires and not vip_info["expired"]:
            # 从当前到期时间延长
            base_time = datetime.fromisoformat(current_expires)
        else:
            # 从现在开始
            base_time = datetime.now()
        
        new_expires = base_time + timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            # 续费并赠送配额
            conn.execute("""
                UPDATE users 
                SET vip_expires_at = ?,
                    vip_credits = vip_credits + ?,
                    api_balance = api_balance + ?
                WHERE id = ?
            """, (new_expires.isoformat(), level_info.credits, level_info.credits, user_id))
            
            # 记录续费记录
            conn.execute("""
                INSERT INTO vip_records (id, user_id, vip_level, amount, expires_at, created_at, is_renewal)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                self._generate_id(), user_id, current_level, payment_amount,
                new_expires.isoformat(), datetime.now().isoformat()
            ))
        
        logger.info(f"用户 {user_id} VIP续费成功")
        
        return {
            "status": "success",
            "level": current_level,
            "level_name": level_info.name,
            "expires_at": new_expires.isoformat(),
            "credits_granted": level_info.credits
        }
    
    def check_vip_benefits(self, user_id: str, action: str) -> Dict:
        """检查VIP权益"""
        vip_info = self.get_user_vip_info(user_id)
        level = vip_info["level"]
        
        benefits = {
            "free_deployment": level >= 1,  # 高级会员及以上免费部署
            "free_blockchain": level >= 1,  # 高级会员及以上免费上链
            "half_price": level >= 2,       # 至尊会员半价
            "custom_deployment": level >= 2, # 至尊会员特殊部署
            "commission_bonus": self.VIP_LEVELS[level].commission_bonus,
            "invitation_bonus": 20 if level >= 1 else 0  # VIP邀请额外奖励
        }
        
        return {
            "vip_level": level,
            "vip_name": self.VIP_LEVELS[level].name,
            "benefits": benefits,
            "expired": vip_info["expired"]
        }
    
    def get_vip_pricing(self) -> Dict:
        """获取VIP定价信息"""
        return {
            level: {
                "name": info.name,
                "monthly_fee": info.monthly_fee,
                "credits": info.credits,
                "benefits": info.benefits,
                "commission_bonus": f"+{info.commission_bonus*100}%" if info.commission_bonus > 0 else "无"
            }
            for level, info in self.VIP_LEVELS.items()
            if level > 0  # 排除普通会员
        }
    
    def _downgrade_to_basic(self, user_id: str):
        """降级到普通会员"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users 
                SET vip_level = 0, vip_expires_at = NULL 
                WHERE id = ?
            """, (user_id,))
        
        logger.info(f"用户 {user_id} VIP已过期，降级为普通会员")
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
    
    def init_vip_tables(self):
        """初始化VIP相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # VIP购买/续费记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vip_records (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    vip_level INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_renewal BOOLEAN DEFAULT 0
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_records_user_id ON vip_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_records_created_at ON vip_records(created_at)")
            
        logger.info("VIP相关表初始化完成")

# VIP专属界面样式
VIP_STYLES = {
    1: {  # 高级会员
        "theme": "premium",
        "colors": {
            "primary": "#FFD700",  # 金色
            "secondary": "#FFA500",
            "background": "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)"
        },
        "effects": ["金色光晕", "高级动画", "专属徽章"]
    },
    2: {  # 至尊会员
        "theme": "ultimate",
        "colors": {
            "primary": "#8A2BE2",  # 紫色
            "secondary": "#9370DB",
            "background": "linear-gradient(135deg, #8A2BE2 0%, #9370DB 100%)"
        },
        "effects": ["紫色光晕", "顶级动画", "至尊徽章", "粒子特效"]
    }
}

def get_vip_theme(vip_level: int) -> Dict:
    """获取VIP主题样式"""
    return VIP_STYLES.get(vip_level, {
        "theme": "standard",
        "colors": {
            "primary": "#00f5ff",
            "secondary": "#764ba2",
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        },
        "effects": []
    })