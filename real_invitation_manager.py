#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实邀请分享管理系统
实现邀请码、分享链接、社交平台分享等功能
"""

import sqlite3
import logging
import json
import hashlib
import time
import uuid
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InvitationCode:
    """邀请码"""
    code: str
    user_id: str
    vip_level: int
    created_at: str
    uses_count: int
    max_uses: int
    is_active: bool

@dataclass
class SharePlatform:
    """分享平台配置"""
    platform: str
    name: str
    share_url_template: str
    icon: str
    enabled: bool

class RealInvitationManager:
    """真实邀请分享管理器"""
    
    # 分享平台配置
    SHARE_PLATFORMS = {
        "wechat": SharePlatform(
            platform="wechat",
            name="微信",
            share_url_template="",  # 微信需要特殊处理
            icon="fab fa-weixin",
            enabled=True
        ),
        "weibo": SharePlatform(
            platform="weibo",
            name="微博",
            share_url_template="https://service.weibo.com/share/share.php?url={url}&title={title}&pic={pic}",
            icon="fab fa-weibo",
            enabled=True
        ),
        "qq": SharePlatform(
            platform="qq",
            name="QQ空间",
            share_url_template="https://sns.qzone.qq.com/cgi-bin/qzshare/cgi_qzshare_onekey?url={url}&title={title}&pics={pic}",
            icon="fab fa-qq",
            enabled=True
        ),
        "telegram": SharePlatform(
            platform="telegram",
            name="Telegram",
            share_url_template="https://t.me/share/url?url={url}&text={title}",
            icon="fab fa-telegram",
            enabled=True
        ),
        "facebook": SharePlatform(
            platform="facebook", 
            name="Facebook",
            share_url_template="https://www.facebook.com/sharer/sharer.php?u={url}&quote={title}",
            icon="fab fa-facebook",
            enabled=True
        ),
        "twitter": SharePlatform(
            platform="twitter",
            name="X (Twitter)",
            share_url_template="https://twitter.com/intent/tweet?url={url}&text={title}&hashtags=AI,NEXUS",
            icon="fab fa-twitter",
            enabled=True
        ),
        "linkedin": SharePlatform(
            platform="linkedin",
            name="LinkedIn", 
            share_url_template="https://www.linkedin.com/sharing/share-offsite/?url={url}",
            icon="fab fa-linkedin",
            enabled=True
        ),
        "reddit": SharePlatform(
            platform="reddit",
            name="Reddit",
            share_url_template="https://reddit.com/submit?url={url}&title={title}",
            icon="fab fa-reddit",
            enabled=True
        )
    }
    
    # 邀请奖励配置
    INVITATION_REWARDS = {
        "register": 30,      # 成功邀请注册奖励30配额
        "recharge_rate": 0.15,  # 被邀请人充值15%返佣
        "share_daily": 5,    # 每日分享奖励5配额
        "vip_bonus": 20      # VIP邀请额外奖励20配额
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_invitation_tables()
    
    def init_invitation_tables(self):
        """初始化邀请相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # 检查并升级现有表结构
            self._upgrade_invitation_tables(conn)
            
            # 邀请码表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_codes (
                    code TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    vip_level INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    uses_count INTEGER DEFAULT 0,
                    max_uses INTEGER DEFAULT 1000,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # 邀请记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invitation_records (
                    record_id TEXT PRIMARY KEY,
                    inviter_id TEXT NOT NULL,
                    invitee_id TEXT NOT NULL,
                    invitation_code TEXT NOT NULL,
                    invitee_username TEXT NOT NULL,
                    reward_amount INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    first_recharge_at TEXT,
                    total_recharge REAL DEFAULT 0.0,
                    commission_earned REAL DEFAULT 0.0
                )
            """)
            
            # 分享记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS share_records (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    share_type TEXT NOT NULL,
                    share_url TEXT NOT NULL,
                    reward_amount INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    click_count INTEGER DEFAULT 0,
                    conversion_count INTEGER DEFAULT 0
                )
            """)
            
            # 每日分享奖励记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_share_rewards (
                    reward_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    reward_date TEXT NOT NULL,
                    platforms_shared TEXT NOT NULL,
                    reward_amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, reward_date)
                )
            """)
            
            conn.commit()
            logger.info("邀请分享表初始化完成")
    
    def _upgrade_invitation_tables(self, conn):
        """升级邀请相关表结构"""
        try:
            # 检查现有share_records表
            cursor = conn.execute("PRAGMA table_info(share_records)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 如果表存在但缺少字段，添加字段
            if 'user_id' in columns and 'record_id' not in columns:
                # 重建share_records表
                conn.execute("DROP TABLE IF EXISTS share_records")
                logger.info("重建share_records表以修复结构")
            
            # 检查现有invitation_records表
            cursor = conn.execute("PRAGMA table_info(invitation_records)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'inviter_id' in columns and 'reward_amount' not in columns:
                # 添加缺失字段
                conn.execute("ALTER TABLE invitation_records ADD COLUMN reward_amount INTEGER DEFAULT 0")
                logger.info("添加reward_amount字段到invitation_records表")
            
        except sqlite3.OperationalError as e:
            # 表不存在，跳过升级
            logger.info(f"表不存在，跳过升级: {e}")
    
    def generate_invitation_code(self, user_id: str, vip_level: int = 0) -> str:
        """生成邀请码"""
        try:
            # 检查是否已有邀请码
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT code FROM invitation_codes 
                    WHERE user_id = ? AND is_active = TRUE
                """, (user_id,))
                
                existing_code = cursor.fetchone()
                if existing_code:
                    return existing_code[0]
            
            # 生成新邀请码
            timestamp = str(int(time.time()))[-6:]  # 时间戳后6位
            user_hash = hashlib.md5(user_id.encode()).hexdigest()[:6]  # 用户ID哈希前6位
            
            if vip_level > 0:
                code = f"VIP{vip_level}{timestamp}{user_hash}".upper()
            else:
                code = f"INV{timestamp}{user_hash}".upper()
            
            # 保存邀请码
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO invitation_codes 
                    (code, user_id, vip_level, created_at)
                    VALUES (?, ?, ?, ?)
                """, (code, user_id, vip_level, datetime.now().isoformat()))
            
            logger.info(f"生成邀请码: {code} for 用户: {user_id}")
            return code
            
        except Exception as e:
            logger.error(f"生成邀请码失败: {e}")
            raise
    
    def validate_invitation_code(self, code: str) -> Optional[Dict]:
        """验证邀请码"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM invitation_codes 
                    WHERE code = ? AND is_active = TRUE
                """, (code,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"验证邀请码失败: {e}")
            return None
    
    def process_invitation_registration(self, inviter_code: str, invitee_id: str, 
                                      invitee_username: str) -> Dict:
        """处理邀请注册"""
        try:
            # 验证邀请码
            invitation_info = self.validate_invitation_code(inviter_code)
            if not invitation_info:
                return {"success": False, "message": "无效的邀请码"}
            
            inviter_id = invitation_info["user_id"]
            vip_level = invitation_info["vip_level"]
            
            # 计算奖励
            base_reward = self.INVITATION_REWARDS["register"]
            vip_bonus = self.INVITATION_REWARDS["vip_bonus"] if vip_level > 0 else 0
            total_reward = base_reward + vip_bonus
            
            with sqlite3.connect(self.db_path) as conn:
                # 更新邀请码使用次数
                conn.execute("""
                    UPDATE invitation_codes 
                    SET uses_count = uses_count + 1
                    WHERE code = ?
                """, (inviter_code,))
                
                # 记录邀请记录
                record_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO invitation_records 
                    (record_id, inviter_id, invitee_id, invitation_code, 
                     invitee_username, reward_amount, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_id, inviter_id, invitee_id, inviter_code,
                    invitee_username, total_reward, datetime.now().isoformat()
                ))
                
                # 给邀请人添加配额奖励
                conn.execute("""
                    UPDATE users 
                    SET api_balance = api_balance + ?, 
                        total_invitations = total_invitations + 1,
                        total_rewards = total_rewards + ?
                    WHERE id = ?
                """, (total_reward, total_reward, inviter_id))
                
                conn.commit()
                
                logger.info(f"邀请注册成功: {inviter_id} 邀请 {invitee_id}, 奖励 {total_reward} 配额")
                
                return {
                    "success": True,
                    "inviter_id": inviter_id,
                    "reward_amount": total_reward,
                    "vip_bonus": vip_bonus
                }
                
        except Exception as e:
            logger.error(f"处理邀请注册失败: {e}")
            return {"success": False, "message": str(e)}
    
    def process_invitation_recharge(self, invitee_id: str, recharge_amount: float) -> Dict:
        """处理被邀请人充值返佣"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 查找邀请记录
                cursor = conn.execute("""
                    SELECT inviter_id, commission_earned FROM invitation_records 
                    WHERE invitee_id = ?
                """, (invitee_id,))
                
                record = cursor.fetchone()
                if not record:
                    return {"success": False, "message": "未找到邀请记录"}
                
                inviter_id = record[0]
                current_commission = record[1] or 0.0
                
                # 计算返佣
                commission_rate = self.INVITATION_REWARDS["recharge_rate"]
                commission_amount = recharge_amount * commission_rate
                commission_quota = int(commission_amount * 2.5)  # 转换为配额
                
                # 更新邀请记录
                conn.execute("""
                    UPDATE invitation_records 
                    SET total_recharge = total_recharge + ?,
                        commission_earned = commission_earned + ?,
                        first_recharge_at = COALESCE(first_recharge_at, ?)
                    WHERE invitee_id = ?
                """, (recharge_amount, commission_amount, datetime.now().isoformat(), invitee_id))
                
                # 给邀请人添加返佣配额
                conn.execute("""
                    UPDATE users 
                    SET api_balance = api_balance + ?,
                        total_rewards = total_rewards + ?
                    WHERE id = ?
                """, (commission_quota, commission_quota, inviter_id))
                
                conn.commit()
                
                logger.info(f"邀请返佣: {inviter_id} 从 {invitee_id} 充值 {recharge_amount} 获得 {commission_quota} 配额")
                
                return {
                    "success": True,
                    "inviter_id": inviter_id,
                    "commission_amount": commission_amount,
                    "commission_quota": commission_quota
                }
                
        except Exception as e:
            logger.error(f"处理邀请返佣失败: {e}")
            return {"success": False, "message": str(e)}
    
    def create_share_link(self, user_id: str, share_type: str = "platform") -> str:
        """创建分享链接"""
        try:
            # 获取邀请码
            invitation_code = self.get_user_invitation_code(user_id)
            
            # 获取用户VIP状态
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT vip_level FROM users WHERE id = ?
                """, (user_id,))
                
                user = cursor.fetchone()
                vip_level = user[0] if user else 0
            
            # 构建分享链接
            base_url = "http://localhost:8892"
            
            if vip_level > 0:
                # VIP专属链接
                share_url = f"{base_url}/vip-invite?code={invitation_code}&vip={vip_level}"
            else:
                # 普通分享链接
                share_url = f"{base_url}?invite={invitation_code}"
            
            return share_url
            
        except Exception as e:
            logger.error(f"创建分享链接失败: {e}")
            return "http://localhost:8892"
    
    def get_user_invitation_code(self, user_id: str) -> str:
        """获取用户邀请码"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT code FROM invitation_codes 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    return result[0]
                
                # 如果没有邀请码，生成一个
                return self.generate_invitation_code(user_id)
                
        except Exception as e:
            logger.error(f"获取用户邀请码失败: {e}")
            return ""
    
    def share_to_platform(self, user_id: str, platform: str) -> Dict:
        """分享到指定平台"""
        try:
            platform_config = self.SHARE_PLATFORMS.get(platform)
            if not platform_config or not platform_config.enabled:
                return {"success": False, "message": "不支持的分享平台"}
            
            # 创建分享链接
            share_url = self.create_share_link(user_id, "platform")
            
            # 分享内容配置
            share_title = "🚀 AI-NEXUS - 未来AI开发平台，邀请你一起体验！"
            share_description = "全智能AI协作开发，一键生成项目，快来体验未来的开发方式！"
            share_image = "http://localhost:8892/static/images/share_banner.jpg"
            
            if platform == "wechat":
                # 微信分享需要特殊处理，复制链接到剪贴板
                final_url = share_url
            else:
                # 其他平台使用模板生成分享链接
                final_url = platform_config.share_url_template.format(
                    url=urllib.parse.quote(share_url),
                    title=urllib.parse.quote(share_title),
                    pic=urllib.parse.quote(share_image)
                )
            
            # 记录分享
            record_id = str(uuid.uuid4())
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO share_records 
                    (record_id, user_id, platform, share_type, share_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record_id, user_id, platform, "platform", 
                    share_url, datetime.now().isoformat()
                ))
                
                conn.commit()
            
            logger.info(f"用户 {user_id} 分享到 {platform}")
            
            return {
                "success": True,
                "platform": platform,
                "share_url": final_url,
                "original_url": share_url,
                "platform_name": platform_config.name
            }
            
        except Exception as e:
            logger.error(f"分享到平台失败: {e}")
            return {"success": False, "message": str(e)}
    
    def process_daily_share_reward(self, user_id: str, platforms_shared: List[str]) -> Dict:
        """处理每日分享奖励"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                # 检查今天是否已经获得奖励
                cursor = conn.execute("""
                    SELECT reward_id FROM daily_share_rewards 
                    WHERE user_id = ? AND reward_date = ?
                """, (user_id, today))
                
                if cursor.fetchone():
                    return {"success": False, "message": "今日已获得分享奖励"}
                
                # 计算奖励（分享到多个平台可以获得更多奖励）
                base_reward = self.INVITATION_REWARDS["share_daily"]
                platform_bonus = min(len(platforms_shared) - 1, 3) * 2  # 最多额外6配额
                total_reward = base_reward + platform_bonus
                
                # 记录分享奖励
                reward_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO daily_share_rewards 
                    (reward_id, user_id, reward_date, platforms_shared, 
                     reward_amount, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    reward_id, user_id, today, json.dumps(platforms_shared),
                    total_reward, datetime.now().isoformat()
                ))
                
                # 给用户添加配额
                conn.execute("""
                    UPDATE users 
                    SET api_balance = api_balance + ?,
                        total_rewards = total_rewards + ?
                    WHERE id = ?
                """, (total_reward, total_reward, user_id))
                
                conn.commit()
                
                logger.info(f"每日分享奖励: 用户 {user_id} 获得 {total_reward} 配额")
                
                return {
                    "success": True,
                    "reward_amount": total_reward,
                    "base_reward": base_reward,
                    "platform_bonus": platform_bonus,
                    "platforms_count": len(platforms_shared)
                }
                
        except Exception as e:
            logger.error(f"处理每日分享奖励失败: {e}")
            return {"success": False, "message": str(e)}
    
    def get_invitation_statistics(self, user_id: str) -> Dict:
        """获取邀请统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总邀请数
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM invitation_records 
                    WHERE inviter_id = ?
                """, (user_id,))
                total_invitations = cursor.fetchone()[0] or 0
                
                # 总奖励
                cursor = conn.execute("""
                    SELECT SUM(reward_amount) FROM invitation_records 
                    WHERE inviter_id = ?
                """, (user_id,))
                total_rewards = cursor.fetchone()[0] or 0
                
                # 总返佣
                cursor = conn.execute("""
                    SELECT SUM(commission_earned) FROM invitation_records 
                    WHERE inviter_id = ?
                """, (user_id,))
                total_commission = cursor.fetchone()[0] or 0.0
                
                # 本月邀请
                this_month = datetime.now().strftime("%Y-%m")
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM invitation_records 
                    WHERE inviter_id = ? AND created_at LIKE ?
                """, (user_id, f"{this_month}%"))
                month_invitations = cursor.fetchone()[0] or 0
                
                return {
                    "total_invitations": total_invitations,
                    "total_rewards": total_rewards,
                    "total_commission": total_commission,
                    "month_invitations": month_invitations,
                    "invitation_code": self.get_user_invitation_code(user_id)
                }
                
        except Exception as e:
            logger.error(f"获取邀请统计失败: {e}")
            return {
                "total_invitations": 0,
                "total_rewards": 0,
                "total_commission": 0.0,
                "month_invitations": 0,
                "invitation_code": ""
            }
    
    def get_share_statistics(self, user_id: str) -> Dict:
        """获取分享统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总分享次数
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM share_records 
                    WHERE user_id = ?
                """, (user_id,))
                total_shares = cursor.fetchone()[0] or 0
                
                # 总点击数
                cursor = conn.execute("""
                    SELECT SUM(click_count) FROM share_records 
                    WHERE user_id = ?
                """, (user_id,))
                total_clicks = cursor.fetchone()[0] or 0
                
                # 每日分享奖励总额
                cursor = conn.execute("""
                    SELECT SUM(reward_amount) FROM daily_share_rewards 
                    WHERE user_id = ?
                """, (user_id,))
                share_rewards = cursor.fetchone()[0] or 0
                
                # 本月分享
                this_month = datetime.now().strftime("%Y-%m")
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM share_records 
                    WHERE user_id = ? AND created_at LIKE ?
                """, (user_id, f"{this_month}%"))
                month_shares = cursor.fetchone()[0] or 0
                
                return {
                    "total_shares": total_shares,
                    "total_clicks": total_clicks,
                    "share_rewards": share_rewards,
                    "month_shares": month_shares
                }
                
        except Exception as e:
            logger.error(f"获取分享统计失败: {e}")
            return {
                "total_shares": 0,
                "total_clicks": 0,
                "share_rewards": 0,
                "month_shares": 0
            }
    
    def get_available_platforms(self) -> List[Dict]:
        """获取可用的分享平台"""
        return [
            {
                "platform": platform,
                "name": config.name,
                "icon": config.icon,
                "enabled": config.enabled
            }
            for platform, config in self.SHARE_PLATFORMS.items()
            if config.enabled
        ]