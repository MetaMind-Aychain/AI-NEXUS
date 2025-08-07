#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强邀请分享管理系统
支持VIP专属链接、严格验证、分享奖励等功能
"""

import sqlite3
import logging
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import random
import urllib.parse

logger = logging.getLogger(__name__)

@dataclass
class InvitationLink:
    """邀请链接"""
    link_id: str
    user_id: str
    invite_code: str
    link_type: str  # standard, vip_premium, vip_ultimate
    is_active: bool
    max_uses: int
    current_uses: int
    bonus_quota: int
    commission_rate: float
    created_at: str
    expires_at: str
    custom_message: str

@dataclass
class ShareRecord:
    """分享记录"""
    share_id: str
    user_id: str
    platform: str  # wechat, qq, weibo, telegram, etc.
    share_type: str  # invite_link, project_showcase, platform_promotion
    content: str
    target_audience: str
    created_at: str
    clicks: int
    conversions: int
    rewards_earned: int

class EnhancedInvitationManager:
    """增强邀请管理器"""
    
    # VIP邀请链接配置
    INVITATION_CONFIGS = {
        "standard": {
            "name": "标准邀请",
            "bonus_quota": 30,
            "commission_rate": 0.15,
            "max_uses": 100,
            "expires_days": 30,
            "style": "standard"
        },
        "vip_premium": {
            "name": "高级会员专属",
            "bonus_quota": 50,  # 额外奖励
            "commission_rate": 0.20,  # VIP加成
            "max_uses": 500,
            "expires_days": 90,
            "style": "premium"
        },
        "vip_ultimate": {
            "name": "至尊会员专属",
            "bonus_quota": 80,
            "commission_rate": 0.25,
            "max_uses": 1000,
            "expires_days": 180,
            "style": "ultimate"
        }
    }
    
    # 分享平台配置
    SHARE_PLATFORMS = {
        "wechat": {
            "name": "微信",
            "icon": "fab fa-weixin",
            "color": "#07C160",
            "bonus_multiplier": 1.2
        },
        "qq": {
            "name": "QQ",
            "icon": "fab fa-qq", 
            "color": "#12B7F5",
            "bonus_multiplier": 1.1
        },
        "weibo": {
            "name": "微博",
            "icon": "fab fa-weibo",
            "color": "#E6162D",
            "bonus_multiplier": 1.3
        },
        "telegram": {
            "name": "Telegram",
            "icon": "fab fa-telegram",
            "color": "#0088CC",
            "bonus_multiplier": 1.4
        },
        "twitter": {
            "name": "Twitter",
            "icon": "fab fa-twitter",
            "color": "#1DA1F2",
            "bonus_multiplier": 1.5
        },
        "discord": {
            "name": "Discord",
            "icon": "fab fa-discord",
            "color": "#5865F2",
            "bonus_multiplier": 1.3
        }
    }
    
    def __init__(self, db_path: str, vip_manager=None):
        self.db_path = db_path
        self.vip_manager = vip_manager
        self.init_invitation_tables()
    
    def init_invitation_tables(self):
        """初始化邀请相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # 邀请链接表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_links (
                    link_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    invite_code TEXT UNIQUE NOT NULL,
                    link_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_uses INTEGER NOT NULL,
                    current_uses INTEGER DEFAULT 0,
                    bonus_quota INTEGER NOT NULL,
                    commission_rate REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    custom_message TEXT DEFAULT '',
                    click_count INTEGER DEFAULT 0,
                    conversion_count INTEGER DEFAULT 0
                )
            """)
            
            # 分享记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_share_records (
                    share_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    invitation_link_id TEXT,
                    platform TEXT NOT NULL,
                    share_type TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    target_audience TEXT DEFAULT 'public',
                    created_at TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    rewards_earned INTEGER DEFAULT 0,
                    last_activity_at TEXT
                )
            """)
            
            # 邀请验证记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_verifications (
                    verification_id TEXT PRIMARY KEY,
                    invite_code TEXT NOT NULL,
                    invited_user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    device_fingerprint TEXT,
                    verification_status TEXT DEFAULT 'pending',
                    fraud_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    verified_at TEXT,
                    rejection_reason TEXT
                )
            """)
            
            # 奖励发放记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_rewards (
                    reward_id TEXT PRIMARY KEY,
                    inviter_id TEXT NOT NULL,
                    invited_user_id TEXT NOT NULL,
                    invite_code TEXT NOT NULL,
                    reward_type TEXT NOT NULL,
                    reward_amount INTEGER NOT NULL,
                    commission_amount REAL DEFAULT 0.0,
                    issued_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitation_links_user_id ON invitation_links(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitation_links_code ON invitation_links(invite_code)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_share_records_user_id ON enhanced_share_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invitation_verifications_code ON invitation_verifications(invite_code)")
            
        logger.info("增强邀请表初始化完成")
    
    def create_invitation_link(self, user_id: str, link_type: str = "standard", 
                             custom_message: str = "", max_uses: int = None) -> Dict:
        """创建邀请链接"""
        if self.vip_manager:
            vip_info = self.vip_manager.get_user_vip_info(user_id)
            vip_level = vip_info.get("level", 0)
            
            # 根据VIP等级确定链接类型
            if link_type == "standard" and vip_level >= 1:
                link_type = "vip_premium" if vip_level == 1 else "vip_ultimate"
        
        if link_type not in self.INVITATION_CONFIGS:
            raise ValueError(f"不支持的邀请链接类型: {link_type}")
        
        config = self.INVITATION_CONFIGS[link_type]
        
        # 生成邀请码
        invite_code = self._generate_invite_code(user_id, link_type)
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(days=config["expires_days"])
        
        link_id = self._generate_id()
        max_uses = max_uses or config["max_uses"]
        
        invitation_link = {
            "link_id": link_id,
            "user_id": user_id,
            "invite_code": invite_code,
            "link_type": link_type,
            "is_active": True,
            "max_uses": max_uses,
            "current_uses": 0,
            "bonus_quota": config["bonus_quota"],
            "commission_rate": config["commission_rate"],
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "custom_message": custom_message
        }
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO invitation_links 
                (link_id, user_id, invite_code, link_type, is_active, max_uses, 
                 current_uses, bonus_quota, commission_rate, created_at, expires_at, custom_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                link_id, user_id, invite_code, link_type, True, max_uses,
                0, config["bonus_quota"], config["commission_rate"],
                datetime.now().isoformat(), expires_at.isoformat(), custom_message
            ))
        
        # 生成分享链接
        share_url = self._generate_share_url(invite_code, link_type)
        
        logger.info(f"创建邀请链接: {invite_code} (类型: {link_type})")
        
        return {
            "link_id": link_id,
            "invite_code": invite_code,
            "link_type": link_type,
            "config": config,
            "share_url": share_url,
            "qr_code_url": f"/api/invitation/qr/{invite_code}",
            "expires_at": expires_at.isoformat(),
            "max_uses": max_uses,
            "bonus_quota": config["bonus_quota"]
        }
    
    def verify_invitation(self, invite_code: str, invited_user_id: str, 
                         ip_address: str, user_agent: str) -> Dict:
        """验证邀请（严格反作弊）"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取邀请链接信息
            cursor = conn.execute("""
                SELECT * FROM invitation_links WHERE invite_code = ? AND is_active = 1
            """, (invite_code,))
            
            link = cursor.fetchone()
            if not link:
                return {"valid": False, "reason": "邀请码不存在或已失效"}
            
            link_data = dict(zip([col[0] for col in cursor.description], link))
            
            # 检查过期时间
            if datetime.now() > datetime.fromisoformat(link_data["expires_at"]):
                return {"valid": False, "reason": "邀请链接已过期"}
            
            # 检查使用次数
            if link_data["current_uses"] >= link_data["max_uses"]:
                return {"valid": False, "reason": "邀请链接使用次数已达上限"}
            
            # 设备指纹生成
            device_fingerprint = self._generate_device_fingerprint(ip_address, user_agent)
            
            # 反作弊检查
            fraud_score = self._calculate_fraud_score(
                invite_code, invited_user_id, ip_address, device_fingerprint
            )
            
            verification_id = self._generate_id()
            verification_status = "approved" if fraud_score < 0.5 else "suspicious"
            
            if fraud_score >= 0.8:
                verification_status = "rejected"
            
            # 记录验证
            conn.execute("""
                INSERT INTO invitation_verifications 
                (verification_id, invite_code, invited_user_id, ip_address, 
                 user_agent, device_fingerprint, verification_status, fraud_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                verification_id, invite_code, invited_user_id, ip_address,
                user_agent, device_fingerprint, verification_status, fraud_score,
                datetime.now().isoformat()
            ))
            
            if verification_status == "approved":
                # 更新使用次数
                conn.execute("""
                    UPDATE invitation_links 
                    SET current_uses = current_uses + 1,
                        conversion_count = conversion_count + 1
                    WHERE invite_code = ?
                """, (invite_code,))
                
                # 发放奖励
                self._issue_invitation_reward(link_data, invited_user_id)
            
            return {
                "valid": verification_status == "approved",
                "verification_id": verification_id,
                "fraud_score": fraud_score,
                "status": verification_status,
                "bonus_quota": link_data["bonus_quota"] if verification_status == "approved" else 0
            }
    
    def create_share_record(self, user_id: str, platform: str, share_type: str = "invite_link", 
                           content: str = "", target_audience: str = "public") -> Dict:
        """创建分享记录"""
        # 检查每日分享限制
        today = datetime.now().date().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查今日分享次数
            daily_shares = conn.execute("""
                SELECT COUNT(*) FROM enhanced_share_records 
                WHERE user_id = ? AND DATE(created_at) = ? AND platform = ?
            """, (user_id, today, platform)).fetchone()[0]
            
            platform_config = self.SHARE_PLATFORMS.get(platform, {})
            max_daily_shares = 5  # 每日每平台最大分享次数
            
            if daily_shares >= max_daily_shares:
                return {
                    "success": False,
                    "reason": f"今日在{platform_config.get('name', platform)}的分享次数已达上限"
                }
            
            # 获取用户的邀请链接
            cursor = conn.execute("""
                SELECT invite_code, link_type FROM invitation_links 
                WHERE user_id = ? AND is_active = 1 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            invitation_link = cursor.fetchone()
            invitation_link_id = invitation_link[0] if invitation_link else None
            
            # 计算奖励
            base_reward = 5  # 基础分享奖励
            platform_bonus = platform_config.get("bonus_multiplier", 1.0)
            total_reward = int(base_reward * platform_bonus)
            
            # VIP加成
            if self.vip_manager:
                vip_info = self.vip_manager.get_user_vip_info(user_id)
                if vip_info.get("level", 0) >= 1:
                    total_reward = int(total_reward * 1.5)  # VIP 50%加成
            
            share_id = self._generate_id()
            
            # 创建分享记录
            conn.execute("""
                INSERT INTO enhanced_share_records 
                (share_id, user_id, invitation_link_id, platform, share_type, 
                 content, target_audience, created_at, rewards_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                share_id, user_id, invitation_link_id, platform, share_type,
                content, target_audience, datetime.now().isoformat(), total_reward
            ))
            
            # 发放分享奖励
            conn.execute("""
                UPDATE users 
                SET api_balance = COALESCE(api_balance, 0) + ?
                WHERE id = ?
            """, (total_reward, user_id))
        
        logger.info(f"用户 {user_id} 在 {platform} 分享，获得 {total_reward} 配额")
        
        return {
            "success": True,
            "share_id": share_id,
            "platform": platform_config.get("name", platform),
            "reward_earned": total_reward,
            "daily_shares_left": max_daily_shares - daily_shares - 1
        }
    
    def get_invitation_statistics(self, user_id: str) -> Dict:
        """获取邀请统计"""
        with sqlite3.connect(self.db_path) as conn:
            # 邀请链接统计
            cursor = conn.execute("""
                SELECT link_type, COUNT(*) as count, SUM(current_uses) as total_uses,
                       SUM(conversion_count) as total_conversions
                FROM invitation_links 
                WHERE user_id = ? 
                GROUP BY link_type
            """, (user_id,))
            
            link_stats = {}
            for row in cursor.fetchall():
                link_stats[row[0]] = {
                    "count": row[1],
                    "total_uses": row[2],
                    "total_conversions": row[3]
                }
            
            # 分享统计
            cursor = conn.execute("""
                SELECT platform, COUNT(*) as shares, SUM(rewards_earned) as total_rewards
                FROM enhanced_share_records 
                WHERE user_id = ? 
                GROUP BY platform
            """, (user_id,))
            
            share_stats = {}
            for row in cursor.fetchall():
                share_stats[row[0]] = {
                    "shares": row[1],
                    "total_rewards": row[2]
                }
            
            # 总奖励统计
            total_rewards = conn.execute("""
                SELECT SUM(reward_amount) FROM invitation_rewards WHERE inviter_id = ?
            """, (user_id,)).fetchone()[0] or 0
            
            total_share_rewards = conn.execute("""
                SELECT SUM(rewards_earned) FROM enhanced_share_records WHERE user_id = ?
            """, (user_id,)).fetchone()[0] or 0
            
            return {
                "invitation_links": link_stats,
                "shares": share_stats,
                "total_invitation_rewards": total_rewards,
                "total_share_rewards": total_share_rewards,
                "total_rewards": total_rewards + total_share_rewards
            }
    
    def get_user_invitation_links(self, user_id: str) -> List[Dict]:
        """获取用户的邀请链接"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM invitation_links 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            
            links = []
            for row in cursor.fetchall():
                link_data = dict(row)
                config = self.INVITATION_CONFIGS.get(link_data["link_type"], {})
                link_data["config"] = config
                link_data["share_url"] = self._generate_share_url(link_data["invite_code"], link_data["link_type"])
                links.append(link_data)
            
            return links
    
    def generate_vip_invitation_page(self, invite_code: str) -> str:
        """生成VIP专属邀请页面HTML"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT il.*, u.username 
                FROM invitation_links il
                JOIN users u ON il.user_id = u.id
                WHERE il.invite_code = ?
            """, (invite_code,))
            
            link_data = cursor.fetchone()
            if not link_data:
                return self._generate_error_page("邀请链接不存在")
            
            link_dict = dict(zip([col[0] for col in cursor.description], link_data))
            config = self.INVITATION_CONFIGS.get(link_dict["link_type"], {})
            
            # 根据VIP等级生成不同样式的页面
            if link_dict["link_type"] == "vip_ultimate":
                return self._generate_ultimate_invitation_page(link_dict, config)
            elif link_dict["link_type"] == "vip_premium":
                return self._generate_premium_invitation_page(link_dict, config)
            else:
                return self._generate_standard_invitation_page(link_dict, config)
    
    def _generate_share_url(self, invite_code: str, link_type: str) -> str:
        """生成分享链接"""
        base_url = "https://ai-nexus.com"  # 你的域名
        if link_type.startswith("vip_"):
            return f"{base_url}/vip-invite/{invite_code}"
        else:
            return f"{base_url}/invite/{invite_code}"
    
    def _generate_invite_code(self, user_id: str, link_type: str) -> str:
        """生成邀请码"""
        # 基于用户ID和时间戳生成唯一邀请码
        timestamp = str(int(time.time()))
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:6]
        
        if link_type == "vip_ultimate":
            prefix = "VU"
        elif link_type == "vip_premium":
            prefix = "VP"
        else:
            prefix = "AI"
        
        return f"{prefix}{user_hash}{timestamp[-6:]}"
    
    def _calculate_fraud_score(self, invite_code: str, user_id: str, 
                              ip_address: str, device_fingerprint: str) -> float:
        """计算作弊风险分数"""
        score = 0.0
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查IP地址重复使用
            ip_usage = conn.execute("""
                SELECT COUNT(*) FROM invitation_verifications 
                WHERE ip_address = ? AND created_at >= ?
            """, (ip_address, (datetime.now() - timedelta(days=1)).isoformat())).fetchone()[0]
            
            if ip_usage > 3:
                score += 0.3
            
            # 检查设备指纹
            device_usage = conn.execute("""
                SELECT COUNT(*) FROM invitation_verifications 
                WHERE device_fingerprint = ? AND created_at >= ?
            """, (device_fingerprint, (datetime.now() - timedelta(days=7)).isoformat())).fetchone()[0]
            
            if device_usage > 1:
                score += 0.4
            
            # 检查注册时间间隔
            recent_registrations = conn.execute("""
                SELECT COUNT(*) FROM invitation_verifications 
                WHERE invite_code = ? AND created_at >= ?
            """, (invite_code, (datetime.now() - timedelta(hours=1)).isoformat())).fetchone()[0]
            
            if recent_registrations > 5:
                score += 0.3
        
        return min(score, 1.0)
    
    def _generate_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """生成设备指纹"""
        fingerprint_data = f"{ip_address}_{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def _issue_invitation_reward(self, link_data: Dict, invited_user_id: str):
        """发放邀请奖励"""
        reward_id = self._generate_id()
        
        with sqlite3.connect(self.db_path) as conn:
            # 记录奖励
            conn.execute("""
                INSERT INTO invitation_rewards 
                (reward_id, inviter_id, invited_user_id, invite_code, 
                 reward_type, reward_amount, issued_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reward_id, link_data["user_id"], invited_user_id, link_data["invite_code"],
                "invitation_bonus", link_data["bonus_quota"], datetime.now().isoformat(), "issued"
            ))
            
            # 发放配额给邀请者
            conn.execute("""
                UPDATE users 
                SET api_balance = COALESCE(api_balance, 0) + ?,
                    total_invitations = COALESCE(total_invitations, 0) + 1,
                    total_rewards = COALESCE(total_rewards, 0) + ?
                WHERE id = ?
            """, (link_data["bonus_quota"], link_data["bonus_quota"], link_data["user_id"]))
            
            # 给被邀请者发放欢迎奖励
            welcome_bonus = 20 if link_data["link_type"].startswith("vip_") else 10
            conn.execute("""
                UPDATE users 
                SET api_balance = COALESCE(api_balance, 0) + ?
                WHERE id = ?
            """, (welcome_bonus, invited_user_id))
        
        logger.info(f"发放邀请奖励: 邀请者 {link_data['user_id']} +{link_data['bonus_quota']}配额, 被邀请者 {invited_user_id} +{welcome_bonus}配额")
    
    def _generate_ultimate_invitation_page(self, link_data: Dict, config: Dict) -> str:
        """生成至尊会员邀请页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-NEXUS 至尊会员专属邀请</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #8A2BE2, #9370DB, #DDA0DD);
            font-family: 'Arial', sans-serif;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(138, 43, 226, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            border: 2px solid rgba(138, 43, 226, 0.3);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        .vip-badge {{
            font-size: 3rem;
            margin-bottom: 20px;
            color: #DDA0DD;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        .benefits {{
            margin: 30px 0;
            text-align: left;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }}
        .benefit {{
            margin: 15px 0;
            font-size: 1.1rem;
        }}
        .join-btn {{
            background: linear-gradient(135deg, #8A2BE2, #9370DB);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 30px;
        }}
        .join-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(138, 43, 226, 0.5);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="vip-badge">💎</div>
        <h1>AI-NEXUS 至尊会员专属邀请</h1>
        <p>尊贵的 {link_data["username"]} 邀请您加入AI开发革命</p>
        
        <div class="benefits">
            <div class="benefit">🎁 注册即获得 {config["bonus_quota"]} 个配额</div>
            <div class="benefit">👑 尊贵的VIP体验</div>
            <div class="benefit">⚡ 免费AI开发服务</div>
            <div class="benefit">🔗 免费区块链部署</div>
            <div class="benefit">💰 更高的分享收益</div>
        </div>
        
        <button class="join-btn" onclick="window.location.href='/register?invite={link_data["invite_code"]}'">
            立即加入至尊体验
        </button>
        
        <p style="margin-top: 30px; font-size: 0.9rem; opacity: 0.8;">
            {link_data.get("custom_message", "体验未来AI开发的无限可能")}
        </p>
    </div>
</body>
</html>
        """
    
    def _generate_premium_invitation_page(self, link_data: Dict, config: Dict) -> str:
        """生成高级会员邀请页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-NEXUS 高级会员专属邀请</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            font-family: 'Arial', sans-serif;
            color: #333;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(255, 215, 0, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            border: 2px solid rgba(255, 215, 0, 0.3);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        .vip-badge {{
            font-size: 3rem;
            margin-bottom: 20px;
            color: #FF8C00;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .join-btn {{
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #333;
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 30px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="vip-badge">👑</div>
        <h1>AI-NEXUS 高级会员邀请</h1>
        <p>优秀的 {link_data["username"]} 邀请您体验高级AI服务</p>
        
        <button class="join-btn" onclick="window.location.href='/register?invite={link_data["invite_code"]}'">
            获得 {config["bonus_quota"]} 配额奖励
        </button>
    </div>
</body>
</html>
        """
    
    def _generate_standard_invitation_page(self, link_data: Dict, config: Dict) -> str:
        """生成标准邀请页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-NEXUS 邀请</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            font-family: 'Arial', sans-serif;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(20px);
        }}
        .join-btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            border-radius: 30px;
            cursor: pointer;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>加入AI-NEXUS</h1>
        <p>{link_data["username"]} 邀请您体验AI开发平台</p>
        
        <button class="join-btn" onclick="window.location.href='/register?invite={link_data["invite_code"]}'">
            立即注册获得 {config["bonus_quota"]} 配额
        </button>
    </div>
</body>
</html>
        """
    
    def _generate_error_page(self, error_message: str) -> str:
        """生成错误页面"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>邀请链接无效</title>
</head>
<body>
    <div style="text-align: center; padding: 50px;">
        <h1>邀请链接无效</h1>
        <p>{error_message}</p>
        <a href="/">返回首页</a>
    </div>
</body>
</html>
        """
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())