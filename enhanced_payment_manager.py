#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强支付管理系统
支持国内外各种支付方式 + 区块链钱包支付
"""

import sqlite3
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import random
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PaymentMethod:
    """支付方式"""
    method_id: str
    name: str
    type: str  # traditional, crypto, digital_wallet
    currency: str
    icon: str
    enabled: bool
    min_amount: float
    max_amount: float
    fee_rate: float
    countries: List[str]

@dataclass
class PaymentRecord:
    """支付记录"""
    payment_id: str
    user_id: str
    amount: float
    currency: str
    api_quota: int
    payment_method: str
    status: str  # pending, completed, failed, refunded
    transaction_id: str
    created_at: str
    completed_at: str
    metadata: Dict

class EnhancedPaymentManager:
    """增强支付管理器"""
    
    # 支持的支付方式
    PAYMENT_METHODS = {
        # 国内支付
        "wechat_pay": PaymentMethod(
            "wechat_pay", "微信支付", "digital_wallet", "CNY",
            "fab fa-weixin", True, 1.0, 50000.0, 0.006, ["CN"]
        ),
        "alipay": PaymentMethod(
            "alipay", "支付宝", "digital_wallet", "CNY",
            "fab fa-alipay", True, 1.0, 50000.0, 0.006, ["CN"]
        ),
        "unionpay": PaymentMethod(
            "unionpay", "银联支付", "traditional", "CNY",
            "fas fa-credit-card", True, 1.0, 100000.0, 0.008, ["CN"]
        ),
        
        # 国际支付
        "paypal": PaymentMethod(
            "paypal", "PayPal", "digital_wallet", "USD",
            "fab fa-paypal", True, 1.0, 10000.0, 0.035, ["US", "EU", "Global"]
        ),
        "stripe": PaymentMethod(
            "stripe", "Stripe", "traditional", "USD",
            "fab fa-stripe", True, 1.0, 999999.0, 0.029, ["US", "EU", "Global"]
        ),
        "apple_pay": PaymentMethod(
            "apple_pay", "Apple Pay", "digital_wallet", "USD",
            "fab fa-apple-pay", True, 1.0, 10000.0, 0.03, ["US", "EU", "Global"]
        ),
        "google_pay": PaymentMethod(
            "google_pay", "Google Pay", "digital_wallet", "USD",
            "fab fa-google-pay", True, 1.0, 10000.0, 0.03, ["US", "EU", "Global"]
        ),
        
        # 区块链钱包
        "metamask": PaymentMethod(
            "metamask", "MetaMask", "crypto", "ETH",
            "fas fa-wallet", True, 0.001, 1000.0, 0.001, ["Global"]
        ),
        "coinbase": PaymentMethod(
            "coinbase", "Coinbase Wallet", "crypto", "ETH",
            "fas fa-coins", True, 0.001, 1000.0, 0.001, ["Global"]
        ),
        "trust_wallet": PaymentMethod(
            "trust_wallet", "Trust Wallet", "crypto", "BNB",
            "fas fa-shield-alt", True, 0.001, 1000.0, 0.0005, ["Global"]
        ),
        "phantom": PaymentMethod(
            "phantom", "Phantom Wallet", "crypto", "SOL",
            "fas fa-ghost", True, 0.01, 10000.0, 0.0001, ["Global"]
        ),
        
        # 其他支付方式
        "bank_transfer": PaymentMethod(
            "bank_transfer", "银行转账", "traditional", "CNY",
            "fas fa-university", True, 100.0, 1000000.0, 0.001, ["CN", "Global"]
        ),
        "crypto_direct": PaymentMethod(
            "crypto_direct", "直接转账", "crypto", "USDT",
            "fab fa-bitcoin", True, 1.0, 100000.0, 0.0, ["Global"]
        )
    }
    
    # 汇率配置（相对于人民币）
    EXCHANGE_RATES = {
        "CNY": 1.0,
        "USD": 7.2,
        "EUR": 7.8,
        "ETH": 16800.0,
        "BNB": 1680.0,
        "SOL": 720.0,
        "USDT": 7.2
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_payment_tables()
    
    def init_payment_tables(self):
        """初始化支付相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # 支付记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_payment_records (
                    payment_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    amount_cny REAL NOT NULL,
                    api_quota INTEGER NOT NULL,
                    payment_method TEXT NOT NULL,
                    status TEXT NOT NULL,
                    transaction_id TEXT,
                    gateway_response TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    failed_at TEXT,
                    failure_reason TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # 钱包地址表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_wallet_addresses (
                    user_id TEXT NOT NULL,
                    wallet_type TEXT NOT NULL,
                    address TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    verified BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    PRIMARY KEY (user_id, wallet_type)
                )
            """)
            
            # 支付方式偏好表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_payment_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferred_methods TEXT DEFAULT '[]',
                    country_code TEXT DEFAULT 'CN',
                    currency_preference TEXT DEFAULT 'CNY',
                    auto_recharge_enabled BOOLEAN DEFAULT FALSE,
                    auto_recharge_threshold INTEGER DEFAULT 10,
                    auto_recharge_amount INTEGER DEFAULT 100
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_payment_user_id ON enhanced_payment_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_payment_status ON enhanced_payment_records(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wallet_addresses_user ON user_wallet_addresses(user_id)")
            
        logger.info("增强支付表初始化完成")
    
    def get_available_payment_methods(self, user_country: str = "CN", amount: float = 100.0) -> List[Dict]:
        """获取可用支付方式"""
        available_methods = []
        
        for method_id, method in self.PAYMENT_METHODS.items():
            # 检查地区支持
            if user_country not in method.countries and "Global" not in method.countries:
                continue
            
            # 检查金额限制
            amount_in_method_currency = self._convert_currency(amount, "CNY", method.currency)
            if amount_in_method_currency < method.min_amount or amount_in_method_currency > method.max_amount:
                continue
            
            # 检查是否启用
            if not method.enabled:
                continue
            
            available_methods.append({
                "method_id": method_id,
                "name": method.name,
                "type": method.type,
                "currency": method.currency,
                "icon": method.icon,
                "amount": amount_in_method_currency,
                "fee_rate": method.fee_rate,
                "fee_amount": amount_in_method_currency * method.fee_rate,
                "total_amount": amount_in_method_currency * (1 + method.fee_rate)
            })
        
        # 按类型和费用排序
        available_methods.sort(key=lambda x: (x["type"], x["fee_rate"]))
        return available_methods
    
    def initiate_payment(self, user_id: str, amount: float, api_quota: int, 
                        payment_method: str, currency: str = "CNY", **kwargs) -> Dict:
        """发起支付"""
        if payment_method not in self.PAYMENT_METHODS:
            raise ValueError(f"不支持的支付方式: {payment_method}")
        
        method_info = self.PAYMENT_METHODS[payment_method]
        
        # 转换为目标货币金额
        amount_in_currency = self._convert_currency(amount, "CNY", currency)
        
        # 计算手续费
        fee = amount_in_currency * method_info.fee_rate
        total_amount = amount_in_currency + fee
        
        # 生成支付记录
        payment_id = self._generate_payment_id()
        transaction_id = self._generate_transaction_id(payment_method)
        
        payment_record = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount_in_currency,
            "currency": currency,
            "amount_cny": amount,
            "api_quota": api_quota,
            "payment_method": payment_method,
            "status": "pending",
            "transaction_id": transaction_id,
            "created_at": datetime.now().isoformat(),
            "metadata": json.dumps(kwargs)
        }
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO enhanced_payment_records 
                (payment_id, user_id, amount, currency, amount_cny, api_quota, 
                 payment_method, status, transaction_id, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_id, user_id, amount_in_currency, currency, amount,
                api_quota, payment_method, "pending", transaction_id,
                datetime.now().isoformat(), json.dumps(kwargs)
            ))
        
        # 根据支付方式生成支付URL或二维码
        payment_data = self._generate_payment_data(payment_method, payment_record)
        
        logger.info(f"发起支付: {payment_id}, 用户: {user_id}, 金额: {total_amount} {currency}")
        
        return {
            "payment_id": payment_id,
            "status": "pending",
            "amount": amount_in_currency,
            "currency": currency,
            "fee": fee,
            "total_amount": total_amount,
            "payment_method": method_info.name,
            "transaction_id": transaction_id,
            **payment_data
        }
    
    def _generate_payment_data(self, payment_method: str, payment_record: Dict) -> Dict:
        """生成支付数据（模拟各种支付方式的响应）"""
        method_info = self.PAYMENT_METHODS[payment_method]
        
        if method_info.type == "crypto":
            # 区块链钱包支付
            return self._generate_crypto_payment_data(payment_method, payment_record)
        elif payment_method in ["wechat_pay", "alipay"]:
            # 二维码支付
            return self._generate_qr_payment_data(payment_method, payment_record)
        elif payment_method == "paypal":
            # PayPal重定向
            return {
                "payment_url": f"https://www.paypal.com/checkout?token={payment_record['transaction_id']}",
                "redirect_required": True
            }
        elif payment_method == "stripe":
            # Stripe支付
            return {
                "client_secret": f"pi_{payment_record['transaction_id']}_secret_test",
                "publishable_key": "pk_test_51234567890abcdef",
                "payment_intent_id": f"pi_{payment_record['transaction_id']}"
            }
        else:
            # 默认银行转账等
            return {
                "payment_instructions": f"请向账户 {self._generate_account_number()} 转账 {payment_record['amount']} {payment_record['currency']}",
                "account_number": self._generate_account_number(),
                "reference_code": payment_record['transaction_id']
            }
    
    def _generate_crypto_payment_data(self, payment_method: str, payment_record: Dict) -> Dict:
        """生成加密货币支付数据"""
        method_info = self.PAYMENT_METHODS[payment_method]
        
        # 生成收款地址
        if method_info.currency == "ETH":
            receive_address = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
            network = "ethereum"
            gas_fee = 0.003  # ETH
        elif method_info.currency == "BNB":
            receive_address = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
            network = "bsc"
            gas_fee = 0.001  # BNB
        elif method_info.currency == "SOL":
            receive_address = f"{''.join([random.choice('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz') for _ in range(44)])}"
            network = "solana"
            gas_fee = 0.000005  # SOL
        else:
            receive_address = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
            network = "ethereum"
            gas_fee = 0.001
        
        return {
            "wallet_type": payment_method,
            "receive_address": receive_address,
            "amount": payment_record['amount'],
            "currency": method_info.currency,
            "network": network,
            "gas_fee": gas_fee,
            "qr_code": f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "explorer_url": f"https://etherscan.io/address/{receive_address}",
            "timeout_minutes": 30
        }
    
    def _generate_qr_payment_data(self, payment_method: str, payment_record: Dict) -> Dict:
        """生成二维码支付数据"""
        qr_data = f"{payment_method}://pay?amount={payment_record['amount']}&order_id={payment_record['transaction_id']}"
        
        return {
            "qr_code_data": qr_data,
            "qr_code_url": f"/api/payment/qr/{payment_record['payment_id']}",
            "deep_link": qr_data,
            "timeout_minutes": 15,
            "instructions": f"请使用{self.PAYMENT_METHODS[payment_method].name}扫描二维码完成支付"
        }
    
    def complete_payment(self, payment_id: str, gateway_response: Dict = None) -> Dict:
        """完成支付"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取支付记录
            cursor = conn.execute("""
                SELECT * FROM enhanced_payment_records WHERE payment_id = ?
            """, (payment_id,))
            
            payment = cursor.fetchone()
            if not payment:
                raise ValueError("支付记录不存在")
            
            if payment[7] != "pending":  # status字段
                raise ValueError("支付已完成或已失败")
            
            # 更新支付状态
            conn.execute("""
                UPDATE enhanced_payment_records 
                SET status = 'completed', 
                    completed_at = ?, 
                    gateway_response = ?
                WHERE payment_id = ?
            """, (datetime.now().isoformat(), json.dumps(gateway_response or {}), payment_id))
            
            # 增加用户API配额
            conn.execute("""
                UPDATE users 
                SET api_balance = COALESCE(api_balance, 0) + ?,
                    total_recharge = COALESCE(total_recharge, 0) + ?
                WHERE id = ?
            """, (payment[5], payment[4], payment[1]))  # api_quota, amount_cny, user_id
        
        logger.info(f"支付完成: {payment_id}")
        
        return {
            "status": "success",
            "payment_id": payment_id,
            "api_quota_added": payment[5],
            "completed_at": datetime.now().isoformat()
        }
    
    def get_user_payment_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取用户支付历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM enhanced_payment_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            payments = []
            for row in cursor.fetchall():
                payment = dict(row)
                payment['metadata'] = json.loads(payment.get('metadata', '{}'))
                payments.append(payment)
            
            return payments
    
    def get_payment_statistics(self, days: int = 30) -> Dict:
        """获取支付统计"""
        from datetime import datetime, timedelta
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # 总支付金额
            total_amount = conn.execute("""
                SELECT SUM(amount_cny) FROM enhanced_payment_records 
                WHERE status = 'completed' AND created_at >= ?
            """, (start_date,)).fetchone()[0] or 0
            
            # 支付次数
            total_count = conn.execute("""
                SELECT COUNT(*) FROM enhanced_payment_records 
                WHERE status = 'completed' AND created_at >= ?
            """, (start_date,)).fetchone()[0]
            
            # 按支付方式统计
            method_stats = {}
            cursor = conn.execute("""
                SELECT payment_method, COUNT(*) as count, SUM(amount_cny) as amount 
                FROM enhanced_payment_records 
                WHERE status = 'completed' AND created_at >= ?
                GROUP BY payment_method
            """, (start_date,))
            
            for row in cursor.fetchall():
                method_stats[row[0]] = {
                    "count": row[1],
                    "amount": row[2],
                    "name": self.PAYMENT_METHODS.get(row[0], {}).name
                }
            
            return {
                "total_amount": total_amount,
                "total_count": total_count,
                "average_amount": total_amount / total_count if total_count > 0 else 0,
                "method_statistics": method_stats,
                "period_days": days
            }
    
    def setup_auto_recharge(self, user_id: str, enabled: bool, threshold: int = 10, amount: int = 100, method: str = "wechat_pay") -> Dict:
        """设置自动充值"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_payment_preferences 
                (user_id, auto_recharge_enabled, auto_recharge_threshold, auto_recharge_amount, preferred_methods)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, enabled, threshold, amount, json.dumps([method])))
        
        return {
            "status": "success",
            "auto_recharge_enabled": enabled,
            "threshold": threshold,
            "amount": amount,
            "method": method
        }
    
    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """货币转换"""
        if from_currency == to_currency:
            return amount
        
        # 先转换为人民币基准
        amount_cny = amount / self.EXCHANGE_RATES.get(from_currency, 1.0)
        # 再转换为目标货币
        return amount_cny * self.EXCHANGE_RATES.get(to_currency, 1.0)
    
    def _generate_payment_id(self) -> str:
        """生成支付ID"""
        import uuid
        return f"pay_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    def _generate_transaction_id(self, payment_method: str) -> str:
        """生成交易ID"""
        timestamp = str(int(time.time()))
        random_str = ''.join([random.choice('0123456789ABCDEF') for _ in range(8)])
        return f"{payment_method.upper()}_{timestamp}_{random_str}"
    
    def _generate_account_number(self) -> str:
        """生成银行账号"""
        return ''.join([random.choice('0123456789') for _ in range(16)])

# 支付网关集成器
class PaymentGatewayIntegrator:
    """支付网关集成器"""
    
    @staticmethod
    def simulate_wechat_callback(payment_id: str, success: bool = True) -> Dict:
        """模拟微信支付回调"""
        if success:
            return {
                "return_code": "SUCCESS",
                "result_code": "SUCCESS",
                "out_trade_no": payment_id,
                "transaction_id": f"4200{random.randint(100000000000, 999999999999)}",
                "time_end": datetime.now().strftime("%Y%m%d%H%M%S")
            }
        else:
            return {
                "return_code": "FAIL",
                "err_code": "ORDERPAID",
                "err_code_des": "订单已支付"
            }
    
    @staticmethod
    def simulate_alipay_callback(payment_id: str, success: bool = True) -> Dict:
        """模拟支付宝回调"""
        if success:
            return {
                "code": "10000",
                "msg": "Success",
                "out_trade_no": payment_id,
                "trade_no": f"2023{random.randint(100000000000000, 999999999999999)}",
                "trade_status": "TRADE_SUCCESS",
                "gmt_payment": datetime.now().isoformat()
            }
        else:
            return {
                "code": "40004",
                "msg": "Business Failed",
                "sub_code": "ACQ.TRADE_HAS_SUCCESS_AND_CLOSE_PAYMENT",
                "sub_msg": "交易已完成"
            }
    
    @staticmethod
    def simulate_crypto_confirmation(payment_id: str, tx_hash: str, confirmations: int = 12) -> Dict:
        """模拟加密货币确认"""
        return {
            "status": "confirmed" if confirmations >= 12 else "pending",
            "transaction_hash": tx_hash,
            "confirmations": confirmations,
            "block_number": random.randint(18000000, 19000000),
            "gas_used": random.randint(21000, 100000),
            "gas_price": random.randint(10, 50),
            "network_fee": 0.003
        }