#!/usr/bin/env python3
"""
快速功能验证测试 - 不依赖平台启动
测试数据库操作、模块导入、核心功能逻辑
"""

import logging
import sys
import traceback
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_module_imports():
    """测试模块导入"""
    logger.info("🧪 测试模块导入...")
    
    try:
        from multi_user_database import MultiUserDatabaseManager, User, Project
        from real_blockchain_manager import RealBlockchainManager
        from real_payment_manager import RealPaymentManager
        from real_invitation_manager import RealInvitationManager
        from vip_manager import VIPManager
        logger.info("✅ 所有模块导入成功")
        return True
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False

def test_database_operations():
    """测试数据库操作"""
    logger.info("🧪 测试数据库操作...")
    
    try:
        from multi_user_database import MultiUserDatabaseManager
        # 初始化数据库
        db = MultiUserDatabaseManager("test_platform.db")
        
        # 创建测试用户
        user_id = db.create_user("test_user", "test@example.com", "basic")
        logger.info(f"✅ 创建用户成功: {user_id}")
        
        # 获取用户
        user = db.get_user(user_id)
        if user:
            logger.info(f"✅ 获取用户成功: {user.username}")
        
        # 测试API余额
        db.deduct_api_balance(user_id, 10)
        user = db.get_user(user_id)
        logger.info(f"✅ API余额操作成功: {user.api_balance}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据库操作失败: {e}")
        traceback.print_exc()
        return False

def test_blockchain_operations():
    """测试区块链操作"""
    logger.info("🧪 测试区块链操作...")
    
    try:
        from real_blockchain_manager import RealBlockchainManager
        manager = RealBlockchainManager("test_platform.db")
        
        # 创建钱包
        result = manager.create_user_wallet("test_user", "solana-devnet")
        logger.info(f"✅ 创建钱包成功: {result['address'][:20]}...")
        
        # 获取钱包
        wallet = manager.get_user_wallet("test_user", "solana-devnet")
        if wallet:
            logger.info(f"✅ 获取钱包成功: {wallet['address'][:20]}...")
        
        return True
    except Exception as e:
        logger.error(f"❌ 区块链操作失败: {e}")
        traceback.print_exc()
        return False

def test_payment_operations():
    """测试支付操作"""
    logger.info("🧪 测试支付操作...")
    
    try:
        from real_payment_manager import RealPaymentManager
        manager = RealPaymentManager("test_platform.db")
        
        # 创建支付订单
        result = manager.create_payment_order(
            user_id="test_user",
            amount=100.0,
            payment_method="alipay",
            order_type="recharge"
        )
        logger.info(f"✅ 创建支付订单成功: {result['order_id']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 支付操作失败: {e}")
        traceback.print_exc()
        return False

def test_invitation_operations():
    """测试邀请分享操作"""
    logger.info("🧪 测试邀请分享操作...")
    
    try:
        from real_invitation_manager import RealInvitationManager
        manager = RealInvitationManager("test_platform.db")
        
        # 生成邀请码
        code = manager.get_user_invitation_code("test_user")
        logger.info(f"✅ 生成邀请码成功: {code}")
        
        # 分享到平台
        result = manager.share_to_platform("test_user", "wechat")
        logger.info(f"✅ 分享功能测试成功: {result['platform_name']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 邀请分享操作失败: {e}")
        traceback.print_exc()
        return False

def test_vip_operations():
    """测试VIP操作"""
    logger.info("🧪 测试VIP操作...")
    
    try:
        from vip_manager import VIPManager
        manager = VIPManager("test_platform.db")
        
        # 获取VIP信息
        vip_info = manager.get_user_vip_info("test_user")
        logger.info(f"✅ 获取VIP信息成功: {vip_info['name']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ VIP操作失败: {e}")
        traceback.print_exc()
        return False

def cleanup():
    """清理测试文件"""
    try:
        test_db = Path("test_platform.db")
        if test_db.exists():
            test_db.unlink()
            logger.info("✅ 测试数据库清理完成")
    except Exception as e:
        logger.warning(f"⚠️ 清理失败: {e}")

def main():
    """主测试函数"""
    logger.info("🚀 开始快速功能验证测试...")
    logger.info("=" * 60)
    
    tests = [
        ("模块导入", test_module_imports),
        ("数据库操作", test_database_operations),
        ("区块链操作", test_blockchain_operations),
        ("支付操作", test_payment_operations),
        ("邀请分享操作", test_invitation_operations),
        ("VIP操作", test_vip_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 执行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 测试报告:")
    logger.info(f"总测试数: {total}")
    logger.info(f"通过: {passed} ✅")
    logger.info(f"失败: {total - passed} ❌")
    logger.info(f"成功率: {(passed/total)*100:.1f}%")
    
    # 清理
    cleanup()
    
    if passed == total:
        logger.info("🎉 所有核心功能测试通过！")
        return 0
    else:
        logger.error("💥 部分功能测试失败，需要修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())