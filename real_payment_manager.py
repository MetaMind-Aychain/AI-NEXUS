#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实支付管理系统
支持国内外多种支付方式和区块链钱包支付
"""

import sqlite3
import logging
import json
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests

logger = logging.getLogger(__name__)

@dataclass
class PaymentConfig:
    """支付配置"""
    provider: str
    api_key: str
    secret_key: str
    app_id: str
    merchant_id: str
    callback_url: str
    notify_url: str
    enabled: bool

@dataclass
class PaymentOrder:
    """支付订单"""
    order_id: str
    user_id: str
    amount: float
    payment_method: str
    payment_provider: str
    status: str  # pending, processing, success, failed, cancelled
    quota_amount: int
    discount_rate: float
    final_amount: float
    created_at: str
    paid_at: str
    callback_data: Dict
    order_type: str  # recharge, vip_upgrade, vip_renew

class RealPaymentManager:
    """真实支付管理器"""
    
    # 支付配置
    PAYMENT_CONFIGS = {
        # 国内支付
        "alipay": PaymentConfig(
            provider="alipay",
            api_key="YOUR_ALIPAY_API_KEY",
            secret_key="YOUR_ALIPAY_SECRET_KEY", 
            app_id="YOUR_ALIPAY_APP_ID",
            merchant_id="YOUR_ALIPAY_MERCHANT_ID",
            callback_url="http://localhost:8892/payment/alipay/callback",
            notify_url="http://localhost:8892/payment/alipay/notify",
            enabled=True
        ),
        "wechat": PaymentConfig(
            provider="wechat",
            api_key="YOUR_WECHAT_API_KEY",
            secret_key="YOUR_WECHAT_SECRET_KEY",
            app_id="YOUR_WECHAT_APP_ID", 
            merchant_id="YOUR_WECHAT_MERCHANT_ID",
            callback_url="http://localhost:8892/payment/wechat/callback",
            notify_url="http://localhost:8892/payment/wechat/notify",
            enabled=True
        ),
        # 国际支付
        "paypal": PaymentConfig(
            provider="paypal",
            api_key="YOUR_PAYPAL_CLIENT_ID",
            secret_key="YOUR_PAYPAL_CLIENT_SECRET",
            app_id="",
            merchant_id="YOUR_PAYPAL_MERCHANT_ID",
            callback_url="http://localhost:8892/payment/paypal/callback",
            notify_url="http://localhost:8892/payment/paypal/notify",
            enabled=True
        ),
        "stripe": PaymentConfig(
            provider="stripe",
            api_key="YOUR_STRIPE_PUBLISHABLE_KEY",
            secret_key="YOUR_STRIPE_SECRET_KEY",
            app_id="",
            merchant_id="YOUR_STRIPE_ACCOUNT_ID",
            callback_url="http://localhost:8892/payment/stripe/callback",
            notify_url="http://localhost:8892/payment/stripe/notify", 
            enabled=True
        ),
        # 区块链支付
        "metamask": PaymentConfig(
            provider="metamask",
            api_key="",
            secret_key="",
            app_id="",
            merchant_id="YOUR_WALLET_ADDRESS",
            callback_url="http://localhost:8892/payment/metamask/callback",
            notify_url="http://localhost:8892/payment/metamask/notify",
            enabled=True
        ),
        "phantom": PaymentConfig(
            provider="phantom",
            api_key="",
            secret_key="", 
            app_id="",
            merchant_id="YOUR_SOLANA_WALLET_ADDRESS",
            callback_url="http://localhost:8892/payment/phantom/callback",
            notify_url="http://localhost:8892/payment/phantom/notify",
            enabled=True
        )
    }
    
    # 充值档位配置
    RECHARGE_TIERS = {
        20: 50,     # 20元 = 50配额
        50: 100,    # 50元 = 100配额  
        100: 220,   # 100元 = 220配额
        500: 1200,  # 500元 = 1200配额
        1000: 2500  # 1000元 = 2500配额
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_payment_tables()
    
    def init_payment_tables(self):
        """初始化支付相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # 支付订单表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_provider TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    quota_amount INTEGER NOT NULL,
                    discount_rate REAL DEFAULT 0.0,
                    final_amount REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    paid_at TEXT,
                    callback_data TEXT DEFAULT '{}',
                    order_type TEXT DEFAULT 'recharge'
                )
            """)
            
            # 支付记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_records (
                    record_id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    provider_order_id TEXT,
                    provider_response TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            
            # 支付配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_configs (
                    config_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL UNIQUE,
                    config_data TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("支付表初始化完成")
    
    def create_payment_order(self, user_id: str, amount: float, payment_method: str, 
                           order_type: str = "recharge", discount_rate: float = 0.0) -> Dict:
        """创建支付订单"""
        try:
            order_id = f"order_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            # 计算配额和最终金额
            if order_type == "recharge":
                quota_amount = self.RECHARGE_TIERS.get(int(amount), int(amount * 2.5))
                final_amount = amount * (1 - discount_rate)
            elif order_type in ["vip_upgrade", "vip_renew"]:
                quota_amount = 0  # VIP升级不直接给配额
                final_amount = amount * (1 - discount_rate)
            else:
                quota_amount = 0
                final_amount = amount
            
            # 获取支付提供商
            payment_provider = self._get_payment_provider(payment_method)
            
            # 保存订单
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO payment_orders 
                    (order_id, user_id, amount, payment_method, payment_provider, 
                     quota_amount, discount_rate, final_amount, created_at, order_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id, user_id, amount, payment_method, payment_provider,
                    quota_amount, discount_rate, final_amount, 
                    datetime.now().isoformat(), order_type
                ))
            
            # 生成支付链接
            payment_url = self._generate_payment_url(order_id, payment_method, final_amount)
            
            logger.info(f"创建支付订单: {order_id}, 用户: {user_id}, 金额: {final_amount}")
            
            return {
                "order_id": order_id,
                "payment_url": payment_url,
                "amount": amount,
                "final_amount": final_amount,
                "quota_amount": quota_amount,
                "payment_method": payment_method,
                "payment_provider": payment_provider,
                "qr_code": self._generate_qr_code(payment_url) if payment_method in ["alipay", "wechat"] else None
            }
            
        except Exception as e:
            logger.error(f"创建支付订单失败: {e}")
            raise
    
    def _get_payment_provider(self, payment_method: str) -> str:
        """根据支付方式获取支付提供商"""
        provider_map = {
            "alipay": "alipay",
            "wechat": "wechat", 
            "paypal": "paypal",
            "stripe": "stripe",
            "metamask": "metamask",
            "phantom": "phantom",
            "usdt": "metamask",
            "sol": "phantom"
        }
        return provider_map.get(payment_method, "unknown")
    
    def _generate_payment_url(self, order_id: str, payment_method: str, amount: float) -> str:
        """生成支付链接"""
        config = self.PAYMENT_CONFIGS.get(self._get_payment_provider(payment_method))
        if not config:
            return f"http://localhost:8892/payment/demo?order_id={order_id}"
        
        if payment_method == "alipay":
            return self._generate_alipay_url(order_id, amount, config)
        elif payment_method == "wechat":
            return self._generate_wechat_url(order_id, amount, config)
        elif payment_method == "paypal":
            return self._generate_paypal_url(order_id, amount, config)
        elif payment_method == "stripe":
            return self._generate_stripe_url(order_id, amount, config)
        elif payment_method in ["metamask", "usdt"]:
            return self._generate_metamask_url(order_id, amount, config)
        elif payment_method in ["phantom", "sol"]:
            return self._generate_phantom_url(order_id, amount, config)
        else:
            # 模拟支付链接
            return f"http://localhost:8892/payment/demo?order_id={order_id}&method={payment_method}&amount={amount}"
    
    def _generate_alipay_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成支付宝支付链接"""
        # 这里应该调用支付宝API生成真实支付链接
        # 现在返回模拟链接
        params = {
            "app_id": config.app_id,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": config.notify_url,
            "return_url": config.callback_url,
            "biz_content": json.dumps({
                "out_trade_no": order_id,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "total_amount": str(amount),
                "subject": "AI-NEXUS平台充值"
            })
        }
        
        # 实际应该生成签名并返回真实支付宝链接
        return f"https://openapi.alipay.com/gateway.do?{self._build_query_string(params)}"
    
    def _generate_wechat_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成微信支付链接"""
        # 这里应该调用微信支付API
        return f"weixin://pay?order_id={order_id}&amount={amount}"
    
    def _generate_paypal_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成PayPal支付链接"""
        # 这里应该调用PayPal API
        return f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={config.merchant_id}&item_name=AI-NEXUS%20Recharge&amount={amount}&currency_code=USD&custom={order_id}"
    
    def _generate_stripe_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成Stripe支付链接"""
        # 这里应该调用Stripe API创建支付会话
        return f"https://checkout.stripe.com/pay?order_id={order_id}&amount={int(amount * 100)}"
    
    def _generate_metamask_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成MetaMask支付链接"""
        # 返回Web3支付页面
        return f"http://localhost:8892/payment/metamask?order_id={order_id}&amount={amount}&to={config.merchant_id}"
    
    def _generate_phantom_url(self, order_id: str, amount: float, config: PaymentConfig) -> str:
        """生成Phantom钱包支付链接"""
        # 返回Solana支付页面
        return f"http://localhost:8892/payment/phantom?order_id={order_id}&amount={amount}&to={config.merchant_id}"
    
    def _generate_qr_code(self, url: str) -> str:
        """生成二维码（Base64编码）"""
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            return base64.b64encode(buffer.getvalue()).decode()
        except ImportError:
            # 如果没有qrcode库，返回空
            return ""
    
    def _build_query_string(self, params: Dict) -> str:
        """构建查询字符串"""
        return "&".join([f"{k}={v}" for k, v in params.items()])
    
    def process_payment_callback(self, order_id: str, provider_data: Dict) -> Dict:
        """处理支付回调"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取订单信息
                cursor = conn.execute("""
                    SELECT * FROM payment_orders WHERE order_id = ?
                """, (order_id,))
                
                order = cursor.fetchone()
                if not order:
                    return {"success": False, "message": "订单不存在"}
                
                order_dict = dict(zip([d[0] for d in cursor.description], order))
                
                # 更新订单状态
                conn.execute("""
                    UPDATE payment_orders 
                    SET status = 'success', paid_at = ?, callback_data = ?
                    WHERE order_id = ?
                """, (datetime.now().isoformat(), json.dumps(provider_data), order_id))
                
                # 记录支付记录
                record_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO payment_records 
                    (record_id, order_id, user_id, action, amount, status, 
                     provider_order_id, provider_response, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_id, order_id, order_dict["user_id"], "payment_success",
                    order_dict["final_amount"], "success",
                    provider_data.get("transaction_id", ""), 
                    json.dumps(provider_data), datetime.now().isoformat()
                ))
                
                conn.commit()
                
                logger.info(f"支付成功: {order_id}, 金额: {order_dict['final_amount']}")
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "user_id": order_dict["user_id"],
                    "quota_amount": order_dict["quota_amount"],
                    "order_type": order_dict["order_type"]
                }
                
        except Exception as e:
            logger.error(f"处理支付回调失败: {e}")
            return {"success": False, "message": str(e)}
    
    def get_payment_order(self, order_id: str) -> Optional[Dict]:
        """获取支付订单"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM payment_orders WHERE order_id = ?
                """, (order_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"获取支付订单失败: {e}")
            return None
    
    def get_user_payment_orders(self, user_id: str) -> List[Dict]:
        """获取用户支付订单列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM payment_orders 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                """, (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取用户支付订单失败: {e}")
            return []
    
    def simulate_payment_success(self, order_id: str) -> Dict:
        """模拟支付成功（测试用）"""
        provider_data = {
            "transaction_id": f"mock_txn_{int(time.time())}",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
        
        return self.process_payment_callback(order_id, provider_data)
    
    def get_payment_statistics(self) -> Dict:
        """获取支付统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总收入
                cursor = conn.execute("""
                    SELECT SUM(final_amount) FROM payment_orders 
                    WHERE status = 'success'
                """)
                total_revenue = cursor.fetchone()[0] or 0.0
                
                # 总订单数
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM payment_orders
                """)
                total_orders = cursor.fetchone()[0] or 0
                
                # 成功率
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM payment_orders 
                    WHERE status = 'success'
                """)
                success_orders = cursor.fetchone()[0] or 0
                
                success_rate = (success_orders / total_orders * 100) if total_orders > 0 else 0
                
                return {
                    "total_revenue": total_revenue,
                    "total_orders": total_orders,
                    "success_orders": success_orders,
                    "success_rate": success_rate,
                    "avg_order_amount": total_revenue / success_orders if success_orders > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"获取支付统计失败: {e}")
            return {
                "total_revenue": 0.0,
                "total_orders": 0,
                "success_orders": 0,
                "success_rate": 0.0,
                "avg_order_amount": 0.0
            }

# 支付工具类
class PaymentUtils:
    """支付工具类"""
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """验证支付金额"""
        return amount > 0 and amount <= 10000
    
    @staticmethod
    def format_currency(amount: float, currency: str = "CNY") -> str:
        """格式化货币显示"""
        if currency == "CNY":
            return f"¥{amount:.2f}"
        elif currency == "USD":
            return f"${amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"
    
    @staticmethod
    def calculate_discount(amount: float, discount_rate: float) -> float:
        """计算折扣后金额"""
        return amount * (1 - discount_rate)
    
    @staticmethod
    def is_payment_method_available(method: str) -> bool:
        """检查支付方式是否可用"""
        available_methods = [
            "alipay", "wechat", "paypal", "stripe", 
            "metamask", "phantom", "usdt", "sol"
        ]
        return method in available_methods