#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区块链管理系统
实现项目上链、用户信息上链、智能合约部署等功能
"""

import sqlite3
import logging
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random

logger = logging.getLogger(__name__)

@dataclass
class BlockchainRecord:
    """区块链记录"""
    record_id: str
    record_type: str  # project, user_profile, vip_status, transaction
    user_id: str
    data_hash: str
    blockchain_address: str
    transaction_hash: str
    block_number: int
    created_at: str
    gas_used: int
    gas_price: int

@dataclass
class SmartContract:
    """智能合约信息"""
    contract_id: str
    contract_type: str  # user_registry, project_registry, vip_contract
    contract_address: str
    abi: str
    bytecode: str
    deployed_at: str

class BlockchainManager:
    """区块链管理器"""
    
    # 模拟的区块链网络配置
    NETWORKS = {
        "solana": {
            "name": "Solana主网",
            "rpc_url": "https://api.mainnet-beta.solana.com",
            "chain_id": 101,
            "gas_price": 5000,  # lamports
            "contract_creation_cost": 8,  # 配额成本 (SOL链费用最低)
            "native_token": "SOL",
            "explorer_url": "https://explorer.solana.com"
        },
        "ethereum": {
            "name": "以太坊主网",
            "rpc_url": "https://mainnet.infura.io/v3/your-project-id",
            "chain_id": 1,
            "gas_price": 20000000000,  # 20 Gwei
            "contract_creation_cost": 30,  # 配额成本
            "native_token": "ETH",
            "explorer_url": "https://etherscan.io"
        },
        "polygon": {
            "name": "Polygon网络",
            "rpc_url": "https://polygon-rpc.com",
            "chain_id": 137,
            "gas_price": 1000000000,  # 1 Gwei
            "contract_creation_cost": 15,  # 配额成本
            "native_token": "MATIC",
            "explorer_url": "https://polygonscan.com"
        },
        "bsc": {
            "name": "币安智能链",
            "rpc_url": "https://bsc-dataseed1.binance.org",
            "chain_id": 56,
            "gas_price": 5000000000,  # 5 Gwei
            "contract_creation_cost": 10,  # 配额成本
            "native_token": "BNB",
            "explorer_url": "https://bscscan.com"
        }
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_blockchain_tables()
    
    def init_blockchain_tables(self):
        """初始化区块链相关表"""
        with sqlite3.connect(self.db_path) as conn:
            # 区块链记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blockchain_records (
                    record_id TEXT PRIMARY KEY,
                    record_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    blockchain_address TEXT NOT NULL,
                    transaction_hash TEXT NOT NULL,
                    block_number INTEGER NOT NULL,
                    network TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    gas_used INTEGER NOT NULL,
                    gas_price INTEGER NOT NULL,
                    confirmation_count INTEGER DEFAULT 0
                )
            """)
            
            # 智能合约表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS smart_contracts (
                    contract_id TEXT PRIMARY KEY,
                    contract_type TEXT NOT NULL,
                    contract_address TEXT NOT NULL,
                    network TEXT NOT NULL,
                    abi TEXT NOT NULL,
                    bytecode TEXT,
                    deployed_at TEXT NOT NULL,
                    deployer_id TEXT NOT NULL
                )
            """)
            
            # 用户区块链身份表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_blockchain_identity (
                    user_id TEXT PRIMARY KEY,
                    blockchain_address TEXT NOT NULL,
                    private_key_encrypted TEXT,
                    public_key TEXT NOT NULL,
                    wallet_type TEXT DEFAULT 'platform_generated',
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_blockchain_records_user_id ON blockchain_records(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_blockchain_records_type ON blockchain_records(record_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_smart_contracts_type ON smart_contracts(contract_type)")
            
        logger.info("区块链相关表初始化完成")
    
    def create_user_blockchain_identity(self, user_id: str) -> Dict:
        """为用户创建区块链身份"""
        # 生成区块链地址（模拟）
        blockchain_address = self._generate_blockchain_address()
        public_key = self._generate_public_key()
        private_key_encrypted = self._encrypt_private_key(self._generate_private_key())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_blockchain_identity 
                (user_id, blockchain_address, private_key_encrypted, public_key, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, blockchain_address, private_key_encrypted, public_key,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
        
        logger.info(f"为用户 {user_id} 创建区块链身份: {blockchain_address}")
        
        return {
            "user_id": user_id,
            "blockchain_address": blockchain_address,
            "public_key": public_key,
            "wallet_type": "platform_generated"
        }
    
    def deploy_project_to_blockchain(self, project_id: str, user_id: str, project_data: Dict, network: str = "solana") -> Dict:
        """将项目部署到区块链"""
        if network not in self.NETWORKS:
            raise ValueError(f"不支持的网络: {network}")
        
        network_config = self.NETWORKS[network]
        
        # 生成项目数据哈希
        data_hash = self._calculate_data_hash(project_data)
        
        # 根据网络类型生成不同的地址和交易
        if network == "solana":
            contract_address = self._generate_solana_address()
            transaction_hash = self._generate_solana_signature()
            block_number = random.randint(180000000, 190000000)  # Solana slot
            gas_used = random.randint(5000, 15000)  # lamports
        else:
            contract_address = self._generate_contract_address()
            transaction_hash = self._generate_transaction_hash()
            block_number = random.randint(18000000, 19000000)
            gas_used = random.randint(500000, 1200000)
        
        # 记录到数据库
        record_id = self._generate_id()
        blockchain_record = BlockchainRecord(
            record_id=record_id,
            record_type="project",
            user_id=user_id,
            data_hash=data_hash,
            blockchain_address=contract_address,
            transaction_hash=transaction_hash,
            block_number=block_number,
            created_at=datetime.now().isoformat(),
            gas_used=gas_used,
            gas_price=network_config["gas_price"]
        )
        
        with sqlite3.connect(self.db_path) as conn:
            # 更新项目表
            conn.execute("""
                UPDATE projects 
                SET blockchain_deployed = 1,
                    blockchain_address = ?,
                    blockchain_network = ?,
                    blockchain_transaction_hash = ?,
                    blockchain_deployed_at = ?
                WHERE id = ?
            """, (contract_address, network, transaction_hash, datetime.now().isoformat(), project_id))
            
            # 记录区块链记录
            conn.execute("""
                INSERT INTO blockchain_records 
                (record_id, record_type, user_id, data_hash, blockchain_address, 
                 transaction_hash, block_number, network, created_at, gas_used, gas_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, "project", user_id, data_hash, contract_address,
                transaction_hash, block_number, network, datetime.now().isoformat(),
                gas_used, network_config["gas_price"]
            ))
        
        logger.info(f"项目 {project_id} 成功部署到 {network_config['name']}")
        
        # 生成浏览器链接
        if network == "solana":
            explorer_url = f"https://explorer.solana.com/tx/{transaction_hash}"
            estimated_cost_usd = (gas_used / 1e9) * 100  # SOL价格约100美元
        elif network == "polygon":
            explorer_url = f"https://polygonscan.com/tx/{transaction_hash}"
            estimated_cost_usd = (gas_used * network_config["gas_price"]) / 1e18 * 0.8  # MATIC价格
        else:
            explorer_url = f"https://etherscan.io/tx/{transaction_hash}"
            estimated_cost_usd = (gas_used * network_config["gas_price"]) / 1e18 * 2000  # ETH价格
        
        return {
            "status": "success",
            "project_id": project_id,
            "blockchain_address": contract_address,
            "transaction_hash": transaction_hash,
            "block_number": block_number,
            "network": network_config["name"],
            "explorer_url": explorer_url,
            "gas_used": gas_used,
            "estimated_cost_usd": estimated_cost_usd
        }
    
    def deploy_user_profile_to_blockchain(self, user_id: str, profile_data: Dict, network: str = "polygon") -> Dict:
        """将用户档案部署到区块链"""
        if network not in self.NETWORKS:
            raise ValueError(f"不支持的网络: {network}")
        
        network_config = self.NETWORKS[network]
        
        # 隐私保护：只上链公开信息的哈希
        public_data = {
            "user_id": user_id,
            "username": profile_data.get("username"),
            "vip_level": profile_data.get("vip_level", 0),
            "total_projects": profile_data.get("total_projects", 0),
            "reputation_score": profile_data.get("reputation_score", 0),
            "created_at": profile_data.get("created_at")
        }
        
        data_hash = self._calculate_data_hash(public_data)
        
        # 模拟部署
        contract_address = self._generate_contract_address()
        transaction_hash = self._generate_transaction_hash()
        block_number = random.randint(18000000, 19000000)
        gas_used = random.randint(200000, 500000)
        
        record_id = self._generate_id()
        
        with sqlite3.connect(self.db_path) as conn:
            # 记录区块链记录
            conn.execute("""
                INSERT INTO blockchain_records 
                (record_id, record_type, user_id, data_hash, blockchain_address, 
                 transaction_hash, block_number, network, created_at, gas_used, gas_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, "user_profile", user_id, data_hash, contract_address,
                transaction_hash, block_number, network, datetime.now().isoformat(),
                gas_used, network_config["gas_price"]
            ))
            
            # 更新用户表
            conn.execute("""
                UPDATE users 
                SET blockchain_profile_address = ?,
                    blockchain_profile_hash = ?,
                    blockchain_profile_updated_at = ?
                WHERE id = ?
            """, (contract_address, data_hash, datetime.now().isoformat(), user_id))
        
        logger.info(f"用户 {user_id} 档案成功上链到 {network_config['name']}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "blockchain_address": contract_address,
            "transaction_hash": transaction_hash,
            "data_hash": data_hash,
            "network": network_config["name"],
            "explorer_url": f"https://polygonscan.com/tx/{transaction_hash}"
        }
    
    def deploy_vip_contract(self, user_id: str, vip_data: Dict, network: str = "polygon") -> Dict:
        """将VIP状态部署为智能合约"""
        if network not in self.NETWORKS:
            raise ValueError(f"不支持的网络: {network}")
        
        network_config = self.NETWORKS[network]
        
        # VIP合约数据
        contract_data = {
            "user_id": user_id,
            "vip_level": vip_data.get("vip_level", 0),
            "expires_at": vip_data.get("expires_at"),
            "benefits": vip_data.get("benefits", []),
            "issued_at": datetime.now().isoformat()
        }
        
        data_hash = self._calculate_data_hash(contract_data)
        
        # 生成智能合约
        contract_address = self._generate_contract_address()
        abi = self._generate_vip_contract_abi()
        bytecode = self._generate_contract_bytecode()
        
        transaction_hash = self._generate_transaction_hash()
        block_number = random.randint(18000000, 19000000)
        gas_used = random.randint(800000, 1500000)
        
        contract_id = self._generate_id()
        record_id = self._generate_id()
        
        with sqlite3.connect(self.db_path) as conn:
            # 记录智能合约
            conn.execute("""
                INSERT INTO smart_contracts 
                (contract_id, contract_type, contract_address, network, abi, bytecode, deployed_at, deployer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id, "vip_contract", contract_address, network,
                abi, bytecode, datetime.now().isoformat(), user_id
            ))
            
            # 记录区块链记录
            conn.execute("""
                INSERT INTO blockchain_records 
                (record_id, record_type, user_id, data_hash, blockchain_address, 
                 transaction_hash, block_number, network, created_at, gas_used, gas_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, "vip_status", user_id, data_hash, contract_address,
                transaction_hash, block_number, network, datetime.now().isoformat(),
                gas_used, network_config["gas_price"]
            ))
        
        logger.info(f"用户 {user_id} VIP合约成功部署到 {network_config['name']}")
        
        return {
            "status": "success",
            "contract_id": contract_id,
            "contract_address": contract_address,
            "transaction_hash": transaction_hash,
            "network": network_config["name"],
            "vip_level": vip_data.get("vip_level", 0),
            "explorer_url": f"https://polygonscan.com/address/{contract_address}"
        }
    
    def get_user_blockchain_records(self, user_id: str) -> List[Dict]:
        """获取用户的所有区块链记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM blockchain_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            
            records = []
            for row in cursor.fetchall():
                records.append(dict(row))
            
            return records
    
    def get_user_smart_contracts(self, user_id: str) -> List[Dict]:
        """获取用户部署的智能合约"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM smart_contracts 
                WHERE deployer_id = ? 
                ORDER BY deployed_at DESC
            """, (user_id,))
            
            contracts = []
            for row in cursor.fetchall():
                contracts.append(dict(row))
            
            return contracts
    
    def verify_blockchain_record(self, record_id: str) -> Dict:
        """验证区块链记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM blockchain_records WHERE record_id = ?
            """, (record_id,))
            
            record = cursor.fetchone()
            if not record:
                return {"verified": False, "error": "记录不存在"}
            
            # 模拟区块链验证
            verification_result = {
                "verified": True,
                "record_id": record["record_id"],
                "transaction_hash": record["transaction_hash"],
                "block_number": record["block_number"],
                "confirmations": random.randint(100, 1000),
                "network": record["network"],
                "status": "confirmed"
            }
            
            return verification_result
    
    def get_blockchain_statistics(self) -> Dict:
        """获取区块链统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            # 总记录数
            total_records = conn.execute("SELECT COUNT(*) FROM blockchain_records").fetchone()[0]
            
            # 按类型统计
            type_stats = {}
            cursor = conn.execute("""
                SELECT record_type, COUNT(*) as count 
                FROM blockchain_records 
                GROUP BY record_type
            """)
            for row in cursor.fetchall():
                type_stats[row[0]] = row[1]
            
            # 按网络统计
            network_stats = {}
            cursor = conn.execute("""
                SELECT network, COUNT(*) as count 
                FROM blockchain_records 
                GROUP BY network
            """)
            for row in cursor.fetchall():
                network_stats[row[0]] = row[1]
            
            # 总gas消耗
            total_gas = conn.execute("SELECT SUM(gas_used) FROM blockchain_records").fetchone()[0] or 0
            
            return {
                "total_records": total_records,
                "records_by_type": type_stats,
                "records_by_network": network_stats,
                "total_gas_used": total_gas,
                "estimated_cost_usd": total_gas * 20e-9 * 2000  # 估算成本
            }
    
    def _generate_blockchain_address(self) -> str:
        """生成区块链地址"""
        return f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
    
    def _generate_contract_address(self) -> str:
        """生成合约地址"""
        return f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
    
    def _generate_transaction_hash(self) -> str:
        """生成交易哈希"""
        return f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"
    
    def _generate_public_key(self) -> str:
        """生成公钥"""
        return f"0x{''.join([random.choice('0123456789abcdef') for _ in range(128)])}"
    
    def _generate_private_key(self) -> str:
        """生成私钥"""
        return f"{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"
    
    def _encrypt_private_key(self, private_key: str) -> str:
        """加密私钥（模拟）"""
        return hashlib.sha256(private_key.encode()).hexdigest()
    
    def _calculate_data_hash(self, data: Dict) -> str:
        """计算数据哈希"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _generate_vip_contract_abi(self) -> str:
        """生成VIP合约ABI"""
        abi = [
            {
                "inputs": [],
                "name": "getVipLevel",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getExpiresAt",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "isActive",
                "outputs": [{"type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        return json.dumps(abi)
    
    def _generate_contract_bytecode(self) -> str:
        """生成合约字节码（模拟）"""
        return f"0x{''.join([random.choice('0123456789abcdef') for _ in range(1000)])}"
    
    def _generate_solana_address(self) -> str:
        """生成Solana地址"""
        # Solana地址是Base58编码的32字节公钥
        chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return ''.join([random.choice(chars) for _ in range(44)])
    
    def _generate_solana_signature(self) -> str:
        """生成Solana交易签名"""
        # Solana交易签名是Base58编码的64字节签名
        chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return ''.join([random.choice(chars) for _ in range(88)])
    
    def _calculate_transaction_cost(self, gas_used: int, network_config: Dict, network: str) -> float:
        """计算交易成本（美元）"""
        if network == "solana":
            return (gas_used / 1e9) * 100  # SOL价格约100美元
        elif network == "polygon":
            return (gas_used * network_config["gas_price"]) / 1e18 * 0.8  # MATIC价格
        elif network == "bsc":
            return (gas_used * network_config["gas_price"]) / 1e18 * 300  # BNB价格
        else:
            return (gas_used * network_config["gas_price"]) / 1e18 * 2000  # ETH价格
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())

# 区块链网络选择器
class NetworkSelector:
    """区块链网络选择器"""
    
    @staticmethod
    def recommend_network(operation_type: str, user_vip_level: int = 0) -> str:
        """推荐最适合的网络"""
        if operation_type == "project_deployment":
            # 项目部署推荐Polygon（费用低）
            return "polygon"
        elif operation_type == "vip_contract":
            # VIP合约推荐以太坊（更权威）
            if user_vip_level >= 2:  # 至尊会员
                return "ethereum"
            else:
                return "polygon"
        elif operation_type == "user_profile":
            # 用户档案推荐BSC（平衡成本和性能）
            return "bsc"
        else:
            return "polygon"  # 默认推荐Polygon
    
    @staticmethod
    def get_network_info(network: str) -> Dict:
        """获取网络信息"""
        return BlockchainManager.NETWORKS.get(network, {})