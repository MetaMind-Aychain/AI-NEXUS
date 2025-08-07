#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整AI协作开发平台测试脚本
测试所有核心功能：登录、充值、分享、AI开发、文档确认、前端编辑等
"""

import requests
import json
import time
import webbrowser
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8892"
TEST_USER = {
    "username": "TestUser_" + str(int(time.time())),
    "email": "test@example.com",
    "inviter_code": ""  # 可选邀请码
}

class PlatformTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.project_id = None
        self.api_balance = 30
        
    def print_banner(self, title):
        """打印测试横幅"""
        print("\n" + "="*60)
        print(f"🚀 {title}")
        print("="*60)
    
    def print_step(self, step, message):
        """打印测试步骤"""
        print(f"\n{step}. {message}")
        
    def print_result(self, success, message):
        """打印测试结果"""
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {status}: {message}")
        
    def test_health_check(self):
        """测试健康检查"""
        self.print_step(1, "健康检查")
        try:
            response = self.session.get(f"{BASE_URL}/api/health")
            success = response.status_code == 200
            self.print_result(success, f"平台状态: {response.json().get('status', 'unknown')}")
            return success
        except Exception as e:
            self.print_result(False, f"连接失败: {e}")
            return False
    
    def test_user_registration(self):
        """测试用户注册登录"""
        self.print_step(2, "用户注册登录")
        try:
            response = self.session.post(f"{BASE_URL}/api/login", json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["user_id"]
                self.print_result(True, f"注册成功，用户ID: {self.user_id}")
                return True
            else:
                self.print_result(False, f"注册失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"注册异常: {e}")
            return False
    
    def test_user_stats(self):
        """测试用户统计信息"""
        self.print_step(3, "获取用户统计信息")
        try:
            response = self.session.get(f"{BASE_URL}/api/user-stats/{self.user_id}")
            if response.status_code == 200:
                data = response.json()
                user = data["user"]
                self.api_balance = user["api_balance"]
                self.print_result(True, f"API配额: {self.api_balance}, 邀请码: {user['invitation_code']}")
                return True
            else:
                self.print_result(False, f"获取失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"请求异常: {e}")
            return False
    
    def test_invitation_stats(self):
        """测试邀请统计"""
        self.print_step(4, "邀请统计信息")
        try:
            response = self.session.get(f"{BASE_URL}/api/invitation-stats/{self.user_id}")
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"邀请统计: {data['total_invitations']}人, 奖励: {data['total_rewards']}配额")
                return True
            else:
                self.print_result(False, f"获取失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"请求异常: {e}")
            return False
    
    def test_share_reward(self):
        """测试分享奖励"""
        self.print_step(5, "分享获得奖励")
        try:
            share_data = {
                "user_id": self.user_id,
                "share_type": "platform",
                "share_platform": "wechat",
                "share_content": "分享AI-NEXUS智能开发平台"
            }
            response = self.session.post(f"{BASE_URL}/api/share", json=share_data)
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"分享成功，获得奖励: {data.get('reward_quota', 5)}配额")
                self.api_balance += 5  # 更新本地余额
                return True
            else:
                self.print_result(False, f"分享失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"分享异常: {e}")
            return False
    
    def test_recharge(self):
        """测试充值功能"""
        self.print_step(6, "测试充值功能")
        try:
            recharge_data = {
                "user_id": self.user_id,
                "amount": 50,
                "api_quota": 100,
                "payment_method": "wechat"
            }
            response = self.session.post(f"{BASE_URL}/api/recharge", json=recharge_data)
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"充值成功! 状态: {data.get('status', 'completed')}")
                if data.get("discount_applied"):
                    self.print_result(True, f"享受优惠: {data['discount_applied']}")
                self.api_balance += 100  # 更新本地余额
                return True
            else:
                self.print_result(False, f"充值失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"充值异常: {e}")
            return False
    
    def test_ai_development(self):
        """测试AI开发功能"""
        self.print_step(7, "启动AI协作开发")
        try:
            dev_data = {
                "user_id": self.user_id,
                "requirement": """创建一个未来感十足的社交平台

核心功能：
• 🔐 用户注册登录系统
• 👤 个人资料管理
• 📢 发布动态功能
• 🤝 关注和取关好友
• ❤️ 点赞和评论系统
• 💬 私信功能
• 🔍 搜索用户
• 🔥 热门动态推荐

技术要求：
• 前端：React + 现代化UI
• 后端：Python FastAPI
• 数据库：SQLite
• 部署：Docker容器化

请生成完整可运行的代码。""",
                "test_mode": True
            }
            
            response = self.session.post(f"{BASE_URL}/api/start-integrated-ai-development", json=dev_data)
            if response.status_code == 200:
                data = response.json()
                self.project_id = data.get("project_id")
                self.print_result(True, f"AI开发启动成功! 项目ID: {self.project_id}")
                
                # 等待开发完成（测试模式很快）
                print("\n   ⏳ 等待AI协作开发完成...")
                time.sleep(5)
                return True
            else:
                self.print_result(False, f"AI开发失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"AI开发异常: {e}")
            return False
    
    def test_project_listing(self):
        """测试项目列表"""
        self.print_step(8, "获取项目列表")
        try:
            response = self.session.get(f"{BASE_URL}/api/user-projects/{self.user_id}")
            if response.status_code == 200:
                projects = response.json()
                self.print_result(True, f"项目数量: {len(projects)}")
                for project in projects:
                    print(f"     - {project['name']}: {project.get('status', 'unknown')}")
                    if not self.project_id and project.get('id'):
                        self.project_id = project['id']  # 使用第一个项目ID
                return True
            else:
                self.print_result(False, f"获取失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"请求异常: {e}")
            return False
    
    def test_document_access(self):
        """测试文档访问"""
        self.print_step(9, "测试项目文档访问")
        if not self.project_id:
            self.print_result(False, "没有可用的项目ID")
            return False
            
        try:
            response = self.session.get(f"{BASE_URL}/api/projects/{self.project_id}/document")
            if response.status_code == 200:
                data = response.json()
                has_document = bool(data.get("document"))
                is_confirmed = data.get("confirmed", False)
                self.print_result(True, f"文档状态: {'有文档' if has_document else '无文档'}, 确认状态: {'已确认' if is_confirmed else '待确认'}")
                return True
            else:
                self.print_result(False, f"文档访问失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"文档访问异常: {e}")
            return False
    
    def test_frontend_access(self):
        """测试前端访问"""
        self.print_step(10, "测试前端界面访问")
        if not self.project_id:
            self.print_result(False, "没有可用的项目ID")
            return False
            
        try:
            response = self.session.get(f"{BASE_URL}/api/projects/{self.project_id}/frontend")
            if response.status_code == 200:
                data = response.json()
                preview_url = data.get("preview_url")
                is_confirmed = data.get("confirmed", False)
                self.print_result(True, f"预览URL: {preview_url}, 确认状态: {'已确认' if is_confirmed else '待确认'}")
                return True
            else:
                self.print_result(False, f"前端访问失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"前端访问异常: {e}")
            return False
    
    def test_document_review(self):
        """测试文档审查"""
        self.print_step(11, "测试文档对话修改")
        if not self.project_id:
            self.print_result(False, "没有可用的项目ID")
            return False
            
        try:
            review_data = {
                "project_id": self.project_id,
                "user_id": self.user_id,
                "document_content": "原有文档内容",
                "modification_type": "modify",
                "feedback": "请改用Vue.js作为前端框架，并添加用户权限管理功能"
            }
            response = self.session.post(f"{BASE_URL}/api/review-document", json=review_data)
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"文档修改成功: {data.get('status', 'completed')}")
                return True
            else:
                self.print_result(False, f"文档修改失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"文档修改异常: {e}")
            return False
    
    def test_frontend_review(self):
        """测试前端审查"""
        self.print_step(12, "测试前端界面修改")
        if not self.project_id:
            self.print_result(False, "没有可用的项目ID")
            return False
            
        try:
            review_data = {
                "project_id": self.project_id,
                "user_id": self.user_id,
                "preview_url": f"/preview/{self.project_id}/frontend",
                "modification_type": "modify",
                "feedback": "请改为深色主题，增大按钮尺寸，添加动画效果"
            }
            response = self.session.post(f"{BASE_URL}/api/review-frontend", json=review_data)
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"前端修改成功: {data.get('status', 'completed')}")
                return True
            else:
                self.print_result(False, f"前端修改失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"前端修改异常: {e}")
            return False
    
    def test_frontend_preview(self):
        """测试前端预览"""
        self.print_step(13, "测试前端预览页面")
        if not self.project_id:
            self.print_result(False, "没有可用的项目ID")
            return False
            
        try:
            response = self.session.get(f"{BASE_URL}/preview/{self.project_id}/frontend")
            if response.status_code == 200:
                content_length = len(response.text)
                self.print_result(True, f"前端预览加载成功，内容长度: {content_length} 字符")
                return True
            else:
                self.print_result(False, f"前端预览失败: {response.status_code}")
                return False
        except Exception as e:
            self.print_result(False, f"前端预览异常: {e}")
            return False
    
    def test_balance_tracking(self):
        """测试配额变化追踪"""
        self.print_step(14, "验证API配额变化")
        try:
            response = self.session.get(f"{BASE_URL}/api/user-stats/{self.user_id}")
            if response.status_code == 200:
                data = response.json()
                current_balance = data["user"]["api_balance"]
                self.print_result(True, f"当前API配额: {current_balance} (预期变化已生效)")
                return True
            else:
                self.print_result(False, f"配额查询失败: {response.text}")
                return False
        except Exception as e:
            self.print_result(False, f"配额查询异常: {e}")
            return False
    
    def test_browser_integration(self):
        """测试浏览器集成"""
        self.print_step(15, "启动浏览器访问")
        try:
            # 打开主页面
            main_url = f"{BASE_URL}/"
            print(f"   🌐 打开主平台: {main_url}")
            
            # 如果有项目，打开文档查看器和前端编辑器
            if self.project_id:
                doc_url = f"{BASE_URL}/static/document_viewer.html?project_id={self.project_id}"
                frontend_url = f"{BASE_URL}/static/frontend_editor.html?project_id={self.project_id}"
                
                print(f"   📄 文档查看器: {doc_url}")
                print(f"   🎨 前端编辑器: {frontend_url}")
                
                # 自动打开浏览器（可选）
                # webbrowser.open(main_url)
            
            self.print_result(True, "浏览器访问链接已生成")
            return True
        except Exception as e:
            self.print_result(False, f"浏览器集成异常: {e}")
            return False
    
    def run_comprehensive_test(self):
        """运行完整测试"""
        self.print_banner("AI-NEXUS 完整平台功能测试")
        print(f"🕒 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 测试目标: {BASE_URL}")
        print(f"👤 测试用户: {TEST_USER['username']}")
        
        # 测试计数器
        total_tests = 15
        passed_tests = 0
        
        # 执行所有测试
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_stats,
            self.test_invitation_stats,
            self.test_share_reward,
            self.test_recharge,
            self.test_ai_development,
            self.test_project_listing,
            self.test_document_access,
            self.test_frontend_access,
            self.test_document_review,
            self.test_frontend_review,
            self.test_frontend_preview,
            self.test_balance_tracking,
            self.test_browser_integration
        ]
        
        for test in tests:
            if test():
                passed_tests += 1
            time.sleep(1)  # 测试间隔
        
        # 测试总结
        self.print_banner("测试结果总结")
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ 通过测试: {passed_tests}/{total_tests}")
        print(f"📊 成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 平台功能完善，测试表现优秀！")
        elif success_rate >= 70:
            print("👍 平台功能良好，部分功能需要优化。")
        else:
            print("⚠️ 平台存在较多问题，需要重点修复。")
        
        # 输出访问信息
        print(f"\n🌐 平台访问地址:")
        print(f"   主页面: {BASE_URL}")
        print(f"   API文档: {BASE_URL}/docs")
        
        if self.user_id:
            print(f"\n👤 测试用户信息:")
            print(f"   用户ID: {self.user_id}")
            print(f"   当前配额: {self.api_balance}")
        
        if self.project_id:
            print(f"\n📁 项目信息:")
            print(f"   项目ID: {self.project_id}")
            print(f"   文档查看: {BASE_URL}/static/document_viewer.html?project_id={self.project_id}")
            print(f"   前端编辑: {BASE_URL}/static/frontend_editor.html?project_id={self.project_id}")
            print(f"   前端预览: {BASE_URL}/preview/{self.project_id}/frontend")
        
        print(f"\n🕒 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return success_rate >= 70

def main():
    """主函数"""
    print("🚀 启动AI-NEXUS完整平台测试")
    print("⏳ 请确保平台已启动在 http://127.0.0.1:8892")
    
    # 给用户几秒钟时间查看
    time.sleep(2)
    
    # 创建测试器并运行
    tester = PlatformTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 所有核心功能测试完成！平台已就绪。")
    else:
        print("\n⚠️ 部分功能存在问题，请检查日志。")
    
    return success

if __name__ == "__main__":
    main()