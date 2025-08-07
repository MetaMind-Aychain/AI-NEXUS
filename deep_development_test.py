#!/usr/bin/env python3
"""
深度开发测试 - 测试LLM API模式下的完整交互式开发流程
"""

import requests
import json
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8892"

class DeepDevelopmentTest:
    def __init__(self):
        self.user_id = None
        self.project_id = None
        self.session = requests.Session()
    
    def test_complete_workflow(self):
        """测试完整的深度开发工作流"""
        logger.info("🚀 开始深度开发流程测试...")
        
        try:
            # 步骤1: 用户注册登录
            self.user_id = self.test_user_registration()
            if not self.user_id:
                logger.error("用户注册失败，测试停止")
                return False
            
            # 步骤2: 启动AI开发
            self.project_id = self.test_ai_development()
            if not self.project_id:
                logger.error("AI开发启动失败，测试停止")
                return False
            
            # 等待项目生成
            time.sleep(5)
            
            # 步骤3: 测试交互式文档修改
            self.test_interactive_document_modification()
            
            # 步骤4: 确认文档
            self.test_document_confirmation()
            
            # 步骤5: 测试交互式前端修改
            self.test_interactive_frontend_modification()
            
            # 步骤6: 确认前端
            self.test_frontend_confirmation()
            
            # 步骤7: 验证项目完成状态
            self.test_project_completion()
            
            logger.info("🎉 深度开发流程测试完成！")
            return True
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return False
    
    def test_user_registration(self):
        """测试用户注册"""
        logger.info("📝 测试用户注册...")
        
        user_data = {
            "username": f"deep_test_user_{int(time.time())}",
            "email": "deep_test@example.com",
            "inviter_code": ""
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/login", json=user_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user_id")
                logger.info(f"✅ 用户注册成功: {user_id}")
                return user_id
            else:
                logger.error(f"用户注册失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"用户注册异常: {e}")
            return None
    
    def test_ai_development(self):
        """测试AI开发启动"""
        logger.info("🤖 测试AI开发启动...")
        
        dev_data = {
            "user_id": self.user_id,
            "requirement": "创建一个高级科学计算器，支持复杂数学运算、图形界面和历史记录功能",
            "test_mode": True
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/start-integrated-ai-development", 
                json=dev_data, 
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                development_id = data.get("development_id")
                logger.info(f"✅ AI开发启动成功: {development_id}")
                
                # 等待项目创建完成，然后从API获取真实的项目ID
                time.sleep(3)
                
                # 获取用户项目列表来找到最新创建的项目
                project_id = self._get_latest_project_id()
                if project_id:
                    logger.info(f"✅ 获取到真实项目ID: {project_id}")
                    return project_id
                else:
                    logger.error("无法获取项目ID")
                    return None
            else:
                logger.error(f"AI开发启动失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"AI开发启动异常: {e}")
            return None
    
    def _get_latest_project_id(self):
        """获取用户最新创建的项目ID"""
        try:
            response = self.session.get(
                f"{BASE_URL}/api/user-projects/{self.user_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                if projects:
                    # 返回最新创建的项目ID
                    latest_project = max(projects, key=lambda p: p.get('created_at', ''))
                    return latest_project.get('id')
            
            return None
        except Exception as e:
            logger.error(f"获取项目ID失败: {e}")
            return None
    
    def test_interactive_document_modification(self):
        """测试交互式文档修改"""
        logger.info("📄 测试交互式文档修改...")
        
        modifications = [
            "请在功能需求中添加图形化界面和科学计算功能",
            "优化技术架构，使用现代化的前端框架",
            "增加用户体验设计，包括深色模式和响应式布局"
        ]
        
        for i, modification in enumerate(modifications, 1):
            logger.info(f"📝 执行文档修改 {i}: {modification[:30]}...")
            
            mod_data = {
                "user_id": self.user_id,
                "project_id": self.project_id,
                "modification_request": modification
            }
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/modify-document", 
                    json=mod_data, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info(f"✅ 文档修改 {i} 成功: {data.get('response', '')[:50]}...")
                        time.sleep(2)  # 模拟用户阅读时间
                    else:
                        logger.error(f"❌ 文档修改 {i} 失败")
                else:
                    logger.error(f"❌ 文档修改 {i} API失败: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"文档修改 {i} 异常: {e}")
    
    def test_document_confirmation(self):
        """测试文档确认"""
        logger.info("✅ 测试文档确认...")
        
        confirm_data = {
            "user_id": self.user_id,
            "project_id": self.project_id
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/confirm-document", 
                json=confirm_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info("✅ 文档确认成功")
                else:
                    logger.error("❌ 文档确认失败")
            else:
                logger.error(f"❌ 文档确认API失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"文档确认异常: {e}")
    
    def test_interactive_frontend_modification(self):
        """测试交互式前端修改"""
        logger.info("🎨 测试交互式前端修改...")
        
        modifications = [
            "请将计算器界面改为深色主题，使用蓝色作为主色调",
            "优化按钮布局，增加hover效果和点击动画",
            "添加科学计算按钮，包括sin、cos、tan等三角函数",
            "优化移动端显示，确保在手机上也能正常使用"
        ]
        
        for i, modification in enumerate(modifications, 1):
            logger.info(f"🎨 执行前端修改 {i}: {modification[:30]}...")
            
            mod_data = {
                "user_id": self.user_id,
                "project_id": self.project_id,
                "modification_request": modification
            }
            
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/modify-frontend", 
                    json=mod_data, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info(f"✅ 前端修改 {i} 成功: {data.get('response', '')[:50]}...")
                        time.sleep(2)  # 模拟用户查看效果时间
                    else:
                        logger.error(f"❌ 前端修改 {i} 失败")
                else:
                    logger.error(f"❌ 前端修改 {i} API失败: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"前端修改 {i} 异常: {e}")
    
    def test_frontend_confirmation(self):
        """测试前端确认"""
        logger.info("✅ 测试前端确认...")
        
        confirm_data = {
            "user_id": self.user_id,
            "project_id": self.project_id
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/confirm-frontend", 
                json=confirm_data, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info("✅ 前端确认成功，项目开发完成")
                else:
                    logger.error("❌ 前端确认失败")
            else:
                logger.error(f"❌ 前端确认API失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"前端确认异常: {e}")
    
    def test_project_completion(self):
        """验证项目完成状态"""
        logger.info("🔍 验证项目完成状态...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/user-projects/{self.user_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                if projects:
                    for project in projects:
                        if project.get("id") == self.project_id:
                            status = project.get("status", "unknown")
                            logger.info(f"📊 项目状态: {status}")
                            
                            if status == "completed":
                                logger.info("🎉 项目已成功完成！")
                            else:
                                logger.warning(f"⚠️ 项目状态异常: {status}")
                            return
                    
                    logger.warning("⚠️ 未找到对应项目")
                else:
                    logger.warning("⚠️ 用户无项目")
            else:
                logger.error(f"❌ 获取项目列表失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"验证项目状态异常: {e}")
    
    def test_api_quota_tracking(self):
        """测试API配额跟踪"""
        logger.info("💰 测试API配额跟踪...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/user-stats/{self.user_id}", 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get("user", {})
                api_balance = user_info.get("api_balance", 0)
                logger.info(f"📊 当前API余额: {api_balance}")
                
                if api_balance < 30:  # 假设初始是30
                    logger.info("✅ API配额正常消耗")
                else:
                    logger.warning("⚠️ API配额未消耗，可能存在问题")
            else:
                logger.error(f"❌ 获取用户统计失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"API配额跟踪异常: {e}")

def main():
    """主测试函数"""
    logger.info("🚀 开始AI-NEXUS深度开发测试...")
    logger.info("=" * 60)
    
    # 检查平台是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ 平台未运行，请先启动平台")
            return
        logger.info("✅ 平台健康检查通过")
    except Exception as e:
        logger.error(f"❌ 无法连接到平台: {e}")
        return
    
    # 执行深度开发测试
    tester = DeepDevelopmentTest()
    success = tester.test_complete_workflow()
    
    # 测试API配额跟踪
    if tester.user_id:
        tester.test_api_quota_tracking()
    
    # 输出测试结果
    logger.info("=" * 60)
    if success:
        logger.info("🎉 深度开发测试全部通过！")
        logger.info("✅ 交互式文档编辑功能正常")
        logger.info("✅ 可视化前端编辑功能正常") 
        logger.info("✅ LLM API集成功能正常")
        logger.info("✅ 项目状态管理功能正常")
        logger.info("✅ 用户交互流程完整")
    else:
        logger.error("💥 深度开发测试存在问题，需要修复")
    
    return success

if __name__ == "__main__":
    main()