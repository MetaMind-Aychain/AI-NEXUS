#!/usr/bin/env python3
"""
最终功能验证 - 通过HTTP API测试
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8892"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data.get('version')}")
            return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    return False

def test_user_registration():
    """测试用户注册"""
    try:
        user_data = {
            "username": f"final_test_user_{int(time.time())}",
            "email": "final_test@example.com",
            "inviter_code": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/login", json=user_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("user_id")
            print(f"✅ 用户注册成功: {user_id}")
            return user_id
    except Exception as e:
        print(f"❌ 用户注册失败: {e}")
    return None

def test_user_stats(user_id):
    """测试用户统计"""
    try:
        response = requests.get(f"{BASE_URL}/api/user-stats/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            api_balance = data.get("user", {}).get("api_balance", 0)
            print(f"✅ 用户统计获取成功: API余额 {api_balance}")
            return True
    except Exception as e:
        print(f"❌ 用户统计获取失败: {e}")
    return False

def test_blockchain_wallet(user_id):
    """测试区块链钱包创建"""
    try:
        wallet_data = {
            "user_id": user_id,
            "network": "solana-devnet"
        }
        
        response = requests.post(f"{BASE_URL}/api/blockchain/create-wallet", 
                               json=wallet_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", "")
            print(f"✅ 钱包创建成功: {address[:20]}...")
            return True
    except Exception as e:
        print(f"❌ 钱包创建失败: {e}")
    return False

def test_ai_development(user_id):
    """测试AI开发"""
    try:
        dev_data = {
            "user_id": user_id,
            "requirement": "创建一个简单的计算器应用",
            "test_mode": True
        }
        
        response = requests.post(f"{BASE_URL}/api/start-integrated-ai-development", 
                               json=dev_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            development_id = data.get("development_id")
            if development_id:
                print(f"✅ AI开发启动成功: {development_id}")
                return True
    except Exception as e:
        print(f"❌ AI开发启动失败: {e}")
    return False

def main():
    """主测试函数"""
    print("🚀 开始最终功能验证...")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health),
        ("用户注册", test_user_registration),
    ]
    
    # 执行基础测试
    user_id = None
    for test_name, test_func in tests:
        print(f"\n🧪 执行: {test_name}")
        if test_name == "用户注册":
            user_id = test_func()
            if user_id:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                return
        else:
            if test_func():
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                return
    
    # 执行用户相关测试
    if user_id:
        user_tests = [
            ("用户统计", lambda: test_user_stats(user_id)),
            ("区块链钱包", lambda: test_blockchain_wallet(user_id)),
            ("AI开发", lambda: test_ai_development(user_id)),
        ]
        
        passed = 0
        for test_name, test_func in user_tests:
            print(f"\n🧪 执行: {test_name}")
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        
        total = len(user_tests) + 2  # 加上基础测试
        passed += 2  # 基础测试都通过了
        
        print("\n" + "=" * 50)
        print(f"📊 最终验证报告:")
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {total - passed} ❌")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 所有功能验证通过！平台运行完全正常！")
        else:
            print("\n⚠️ 部分功能需要进一步检查")

if __name__ == "__main__":
    main()