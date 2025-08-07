#!/usr/bin/env python3
"""
测试增强多用户AI协作开发平台
"""

import asyncio
import json
import time
import requests
from datetime import datetime

# 平台配置
BASE_URL = "http://127.0.0.1:8892"
API_URL = f"{BASE_URL}/api"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 平台状态: {data['status']}")
            print(f"📊 版本: {data['version']}")
            print(f"👥 多用户: {data['multi_user']}")
            print(f"⚡ 优化: {data['optimization_enabled']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_user_login():
    """测试用户登录"""
    print("\n👤 测试用户登录...")
    try:
        user_data = {
            "username": "测试用户",
            "email": "test@example.com"
        }
        
        response = requests.post(f"{API_URL}/login", json=user_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data["user_id"]
            print(f"✅ 登录成功! 用户ID: {user_id}")
            return user_id
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def test_user_stats(user_id):
    """测试用户统计"""
    print(f"\n📊 测试用户统计...")
    try:
        response = requests.get(f"{API_URL}/user-stats/{user_id}")
        if response.status_code == 200:
            data = response.json()
            user_info = data["user"]
            print(f"✅ 用户名: {user_info['username']}")
            print(f"💰 API余额: {user_info['api_balance']}")
            print(f"📊 订阅等级: {user_info['subscription_tier']}")
            print(f"📈 项目总数: {data['projects']['total']}")
            return True
        else:
            print(f"❌ 获取统计失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 统计异常: {e}")
        return False

def test_ai_development(user_id):
    """测试AI开发功能"""
    print(f"\n🤖 测试AI开发功能...")
    try:
        # 使用测试模式
        development_data = {
            "user_id": user_id,
            "requirement": "我需要一个简单的社交平台，包含用户注册登录、发布动态、关注好友、点赞评论等功能。要求界面简洁美观，支持移动端访问。",
            "test_mode": True  # 使用测试模式
        }
        
        response = requests.post(f"{API_URL}/start-integrated-ai-development", json=development_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI开发启动成功!")
            print(f"📋 状态: {data['status']}")
            print(f"🧪 测试模式: {data['test_mode']}")
            print(f"💎 需要配额: {data['required_quota']}")
            print("⏳ 正在等待AI处理结果...")
            
            # 等待一段时间让AI处理
            time.sleep(3)
            return True
        else:
            print(f"❌ AI开发启动失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ AI开发异常: {e}")
        return False

def test_share_reward(user_id):
    """测试分享奖励"""
    print(f"\n🎁 测试分享奖励...")
    try:
        share_data = {
            "user_id": user_id,
            "share_type": "platform",
            "share_platform": "wechat",
            "share_content": "分享AI协作开发平台测试"
        }
        
        response = requests.post(f"{API_URL}/share", json=share_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 分享成功!")
            print(f"🎁 奖励配额: {data['reward_quota']}")
            print(f"💰 新余额: {data['new_balance']}")
            return True
        else:
            print(f"❌ 分享失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 分享异常: {e}")
        return False

def test_mock_recharge(user_id):
    """测试模拟充值"""
    print(f"\n💳 测试模拟充值...")
    try:
        recharge_data = {
            "user_id": user_id,
            "amount": 19.0,
            "api_quota": 100,
            "payment_method": "wechat"
        }
        
        response = requests.post(f"{API_URL}/recharge", json=recharge_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 充值成功!")
            print(f"💰 金额: ¥{recharge_data['amount']}")
            print(f"💎 获得配额: {recharge_data['api_quota']}")
            print(f"📋 交易ID: {data['transaction_id']}")
            print(f"💰 新余额: {data['new_balance']}")
            return True
        else:
            print(f"❌ 充值失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 充值异常: {e}")
        return False

def test_projects(user_id):
    """测试项目列表"""
    print(f"\n📁 测试项目管理...")
    try:
        response = requests.get(f"{API_URL}/user-projects/{user_id}")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ 项目列表获取成功!")
            print(f"📊 项目总数: {len(projects)}")
            
            for i, project in enumerate(projects):
                print(f"  [{i+1}] {project['name']}")
                print(f"      状态: {project['status']}")
                print(f"      完成度: {project['completion_percentage']}%")
                if project.get('deployment_url'):
                    print(f"      访问链接: {project['deployment_url']}")
            
            return True
        else:
            print(f"❌ 获取项目失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 项目异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试增强多用户AI协作开发平台")
    print("=" * 60)
    
    # 等待平台启动
    print("⏳ 等待平台启动...")
    time.sleep(3)
    
    # 测试健康检查
    if not test_health():
        print("❌ 平台未启动，测试终止")
        return
    
    # 测试用户登录
    user_id = test_user_login()
    if not user_id:
        print("❌ 用户登录失败，测试终止")
        return
    
    # 测试用户统计
    test_user_stats(user_id)
    
    # 测试分享奖励
    test_share_reward(user_id)
    
    # 测试模拟充值
    test_mock_recharge(user_id)
    
    # 重新获取用户统计（查看余额变化）
    print(f"\n📊 充值后用户统计:")
    test_user_stats(user_id)
    
    # 测试AI开发功能
    test_ai_development(user_id)
    
    # 等待AI处理完成
    print("⏳ 等待AI处理完成...")
    time.sleep(5)
    
    # 测试项目管理
    test_projects(user_id)
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print(f"🌐 前端界面: {BASE_URL}")
    print(f"📚 API文档: {BASE_URL}/docs")
    print("=" * 60)

if __name__ == "__main__":
    main()