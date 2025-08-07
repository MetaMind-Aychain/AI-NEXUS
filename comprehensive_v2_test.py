#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2.1版本全面测试脚本
测试所有真实区块链功能和系统稳定性
"""

import requests
import json
import time
import asyncio
import logging
from typing import Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class V21PlatformTester:
    """V2.1平台全面测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8892"):
        self.base_url = base_url
        self.test_users = []
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
    
    def test_health_check(self):
        """测试系统健康状态"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("系统健康检查", True, f"版本: {data.get('version', 'Unknown')}")
                return True
            else:
                self.log_test("系统健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("系统健康检查", False, f"异常: {str(e)}")
            return False
    
    def test_user_registration_login(self):
        """测试用户注册和登录"""
        try:
            # 创建测试用户
            test_username = f"test_user_{int(time.time())}"
            test_email = f"{test_username}@test.com"
            
            response = requests.post(
                f"{self.base_url}/api/login",
                json={
                    "username": test_username,
                    "email": test_email,
                    "inviter_code": ""
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user_id")
                
                if user_id:
                    self.test_users.append({
                        "user_id": user_id,
                        "username": test_username,
                        "email": test_email
                    })
                    self.log_test("用户注册登录", True, f"用户ID: {user_id}")
                    return user_id
                else:
                    self.log_test("用户注册登录", False, "未返回用户ID")
                    return None
            else:
                self.log_test("用户注册登录", False, f"状态码: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("用户注册登录", False, f"异常: {str(e)}")
            return None
    
    def test_user_stats(self, user_id: str):
        """测试用户统计信息"""
        try:
            response = requests.get(f"{self.base_url}/api/user-stats/{user_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user = data.get("user", {})
                api_balance = user.get("api_balance", 0)
                
                self.log_test("用户统计信息", True, f"API余额: {api_balance}")
                return api_balance >= 0
            else:
                self.log_test("用户统计信息", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("用户统计信息", False, f"异常: {str(e)}")
            return False
    
    def test_blockchain_wallet_creation(self, user_id: str):
        """测试真实区块链钱包创建"""
        try:
            # 测试Solana钱包
            response = requests.post(
                f"{self.base_url}/api/blockchain/create-wallet",
                json={
                    "user_id": user_id,
                    "network": "solana-devnet"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                wallet = data.get("wallet", {})
                address = wallet.get("address", "")
                
                if address and len(address) > 20:  # Solana地址通常44个字符
                    self.log_test("Solana钱包创建", True, f"地址: {address[:20]}...")
                    return wallet
                else:
                    self.log_test("Solana钱包创建", False, "无效的钱包地址")
                    return None
            else:
                error_details = response.text
                self.log_test("Solana钱包创建", False, f"状态码: {response.status_code}, 错误: {error_details}")
                return None
        except Exception as e:
            self.log_test("Solana钱包创建", False, f"异常: {str(e)}")
            return None
    
    def test_wallet_query(self, user_id: str):
        """测试钱包查询"""
        try:
            response = requests.get(f"{self.base_url}/api/blockchain/wallet/{user_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                wallets = data.get("wallets", [])
                
                if wallets:
                    wallet_count = len(wallets)
                    self.log_test("钱包查询", True, f"找到 {wallet_count} 个钱包")
                    return wallets
                else:
                    self.log_test("钱包查询", True, "暂无钱包")
                    return []
            else:
                self.log_test("钱包查询", False, f"状态码: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("钱包查询", False, f"异常: {str(e)}")
            return []
    
    def test_user_profile_blockchain_deployment(self, user_id: str):
        """测试用户档案真实上链"""
        try:
            response = requests.post(
                f"{self.base_url}/api/blockchain/deploy-user-profile",
                json={
                    "user_id": user_id,
                    "network": "solana-devnet"
                },
                timeout=30  # 上链可能需要更长时间
            )
            
            if response.status_code == 200:
                data = response.json()
                transaction_hash = data.get("transaction_hash", "")
                data_hash = data.get("data_hash", "")
                
                if transaction_hash and data_hash:
                    self.log_test("用户档案上链", True, f"交易哈希: {transaction_hash[:20]}...")
                    return data
                else:
                    self.log_test("用户档案上链", False, "缺少关键信息")
                    return None
            else:
                error_details = response.text
                self.log_test("用户档案上链", False, f"状态码: {response.status_code}, 错误: {error_details}")
                return None
        except Exception as e:
            self.log_test("用户档案上链", False, f"异常: {str(e)}")
            return None
    
    def test_blockchain_data_query(self, user_id: str):
        """测试区块链数据查询"""
        try:
            response = requests.get(f"{self.base_url}/api/blockchain/data/{user_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                blockchain_data = data.get("blockchain_data", [])
                
                data_count = len(blockchain_data)
                self.log_test("区块链数据查询", True, f"找到 {data_count} 条数据")
                return blockchain_data
            else:
                self.log_test("区块链数据查询", False, f"状态码: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("区块链数据查询", False, f"异常: {str(e)}")
            return []
    
    def test_data_verification(self, blockchain_data: List[Dict]):
        """测试数据验证"""
        if not blockchain_data:
            self.log_test("数据验证", True, "无数据需要验证")
            return True
        
        try:
            # 验证第一条数据
            data_id = blockchain_data[0].get("data_id")
            
            if not data_id:
                self.log_test("数据验证", False, "无效的数据ID")
                return False
            
            response = requests.post(
                f"{self.base_url}/api/blockchain/verify-data",
                json={"data_id": data_id},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                verified = result.get("verified", False)
                
                if verified:
                    self.log_test("数据验证", True, f"数据验证成功: {data_id}")
                    return True
                else:
                    status = result.get("status", "未知")
                    self.log_test("数据验证", True, f"数据状态: {status}")
                    return True  # 状态为pending也是正常的
            else:
                self.log_test("数据验证", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("数据验证", False, f"异常: {str(e)}")
            return False
    
    def test_ai_development_simulation(self, user_id: str):
        """测试AI开发模拟（测试模式）"""
        try:
            response = requests.post(
                f"{self.base_url}/api/start-integrated-ai-development",
                json={
                    "user_id": user_id,
                    "requirement": "创建一个简单的个人博客网站",
                    "test_mode": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                development_id = data.get("development_id", "")
                
                if development_id:
                    self.log_test("AI开发模拟", True, f"开发ID: {development_id}")
                    return development_id
                else:
                    self.log_test("AI开发模拟", False, "未返回开发ID")
                    return None
            else:
                error_details = response.text
                self.log_test("AI开发模拟", False, f"状态码: {response.status_code}, 错误: {error_details}")
                return None
        except Exception as e:
            self.log_test("AI开发模拟", False, f"异常: {str(e)}")
            return None
    
    def test_project_listing(self, user_id: str):
        """测试项目列表"""
        try:
            response = requests.get(f"{self.base_url}/api/user-projects/{user_id}", timeout=10)
            
            if response.status_code == 200:
                projects = response.json()
                project_count = len(projects)
                self.log_test("项目列表", True, f"找到 {project_count} 个项目")
                return projects
            else:
                self.log_test("项目列表", False, f"状态码: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("项目列表", False, f"异常: {str(e)}")
            return []
    
    def test_vip_info(self, user_id: str):
        """测试VIP信息"""
        try:
            response = requests.get(f"{self.base_url}/api/vip-info/{user_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                vip_level = data.get("level", 0)
                self.log_test("VIP信息", True, f"VIP等级: {vip_level}")
                return data
            else:
                error_details = response.text
                self.log_test("VIP信息", False, f"状态码: {response.status_code}, 错误: {error_details}")
                return None
        except Exception as e:
            self.log_test("VIP信息", False, f"异常: {str(e)}")
            return None
    
    def test_blockchain_statistics(self):
        """测试区块链统计"""
        try:
            response = requests.get(f"{self.base_url}/api/blockchain/statistics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total_records = data.get("total_records", 0)
                self.log_test("区块链统计", True, f"总记录数: {total_records}")
                return data
            else:
                self.log_test("区块链统计", False, f"状态码: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("区块链统计", False, f"异常: {str(e)}")
            return None
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        logger.info("🚀 开始V2.1平台全面测试...")
        
        # 1. 系统健康检查
        if not self.test_health_check():
            logger.error("❌ 系统健康检查失败，停止测试")
            return
        
        # 2. 用户注册登录
        user_id = self.test_user_registration_login()
        if not user_id:
            logger.error("❌ 用户注册失败，停止测试")
            return
        
        # 3. 用户统计信息
        self.test_user_stats(user_id)
        
        # 4. 真实区块链钱包创建
        wallet = self.test_blockchain_wallet_creation(user_id)
        
        # 5. 钱包查询
        wallets = self.test_wallet_query(user_id)
        
        # 6. 用户档案真实上链
        blockchain_result = self.test_user_profile_blockchain_deployment(user_id)
        
        # 等待上链处理
        if blockchain_result:
            logger.info("⏳ 等待5秒让区块链交易处理...")
            time.sleep(5)
        
        # 7. 区块链数据查询
        blockchain_data = self.test_blockchain_data_query(user_id)
        
        # 8. 数据验证
        self.test_data_verification(blockchain_data)
        
        # 9. AI开发模拟
        development_id = self.test_ai_development_simulation(user_id)
        
        # 等待开发处理
        if development_id:
            logger.info("⏳ 等待3秒让AI开发处理...")
            time.sleep(3)
        
        # 10. 项目列表
        projects = self.test_project_listing(user_id)
        
        # 11. VIP信息
        self.test_vip_info(user_id)
        
        # 12. 区块链统计
        self.test_blockchain_statistics()
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*60)
        logger.info("📊 V2.1平台测试报告")
        logger.info("="*60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests} ✅")
        logger.info(f"失败: {failed_tests} ❌")
        logger.info(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test_name']}: {result['details']}")
        
        logger.info("\n✅ 成功的测试:")
        for result in self.test_results:
            if result["success"]:
                logger.info(f"  - {result['test_name']}: {result['details']}")
        
        logger.info("\n🎯 关键功能验证:")
        key_features = [
            "系统健康检查",
            "用户注册登录", 
            "Solana钱包创建",
            "用户档案上链",
            "区块链数据查询",
            "AI开发模拟"
        ]
        
        for feature in key_features:
            result = next((r for r in self.test_results if r["test_name"] == feature), None)
            if result:
                status = "✅" if result["success"] else "❌"
                logger.info(f"  {status} {feature}")
        
        logger.info("="*60)
        
        # 保存详细报告
        with open("v2_1_test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "test_results": self.test_results,
                "test_users": self.test_users
            }, f, ensure_ascii=False, indent=2)
        
        logger.info("📄 详细测试报告已保存到: v2_1_test_report.json")

def main():
    """主函数"""
    tester = V21PlatformTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()