#!/usr/bin/env python3
"""
Web平台集成测试

验证Web平台是否正确深度集成现有的多AI协作系统
"""

import asyncio
import aiohttp
import json
import time
import uuid
from pathlib import Path
import sys
import os

# 添加路径以导入项目模块
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入要测试的组件
from backend.main import app
from backend.database import DatabaseManager
from backend.ai_coordinator import AICoordinator
from backend.models import User, Project, ProjectDocument
from multi_ai_system.orchestrator import MultiAIOrchestrator
from multi_ai_system.memory.shared_memory import SharedMemoryManager

class WebPlatformIntegrationTest:
    """Web平台集成测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api/v1"
        self.session = None
        
        # 测试数据
        self.test_user_id = "test_user_" + str(uuid.uuid4())
        self.test_project_id = None
        self.test_auth_token = "test_token_123"
        
        # 测试结果
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
    
    async def setup(self):
        """设置测试环境"""
        print("🛠️ 设置测试环境...")
        
        # 创建HTTP会话
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.test_auth_token}"
            }
        )
        
        # 等待服务器启动
        await self.wait_for_server()
        
    async def teardown(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        
        if self.session:
            await self.session.close()
    
    async def wait_for_server(self, max_retries=30):
        """等待服务器启动"""
        print("⏳ 等待服务器启动...")
        
        for i in range(max_retries):
            try:
                async with self.session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        print("✅ 服务器已启动")
                        return True
            except:
                pass
            
            await asyncio.sleep(1)
            print(f"   重试 {i+1}/{max_retries}...")
        
        raise Exception("❌ 服务器启动超时")
    
    def log_test_result(self, test_name, success, message="", details=None):
        """记录测试结果"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
        
        if details:
            print(f"     详情: {details}")
    
    async def test_api_health(self):
        """测试API健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                data = await response.json()
                
                success = response.status == 200 and "多AI协作开发平台" in data.get("message", "")
                self.log_test_result(
                    "API健康检查",
                    success,
                    f"状态码: {response.status}",
                    data
                )
                
        except Exception as e:
            self.log_test_result("API健康检查", False, f"请求失败: {str(e)}")
    
    async def test_project_creation(self):
        """测试项目创建 - 核心功能"""
        try:
            project_data = {
                "description": "测试项目：一个简单的博客系统，用户可以发布和管理文章",
                "requirements": {
                    "project_type": "blog_cms",
                    "complexity_level": "medium",
                    "features": ["用户注册登录", "文章发布", "评论系统"],
                    "target_audience": "个人博主"
                },
                "technology_preference": "react_node",
                "domain_preference": "test-blog.com"
            }
            
            async with self.session.post(
                f"{self.api_base}/projects/create",
                json=project_data
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.test_project_id = data.get("project_id")
                    
                    success = (
                        data.get("success") and 
                        self.test_project_id and
                        "document" in data
                    )
                    
                    self.log_test_result(
                        "项目创建",
                        success,
                        f"项目ID: {self.test_project_id}",
                        data
                    )
                else:
                    response_text = await response.text()
                    self.log_test_result(
                        "项目创建", 
                        False, 
                        f"HTTP {response.status}",
                        response_text
                    )
                    
        except Exception as e:
            self.log_test_result("项目创建", False, f"请求异常: {str(e)}")
    
    async def test_document_ai_integration(self):
        """测试文档AI集成"""
        if not self.test_project_id:
            self.log_test_result("文档AI集成", False, "项目ID不存在，跳过测试")
            return
        
        try:
            # 测试文档更新
            update_data = {
                "project_id": self.test_project_id,
                "document_content": "更新后的项目文档内容",
                "update_type": "ai_generated",
                "user_feedback": "请添加用户权限管理功能"
            }
            
            async with self.session.post(
                f"{self.api_base}/projects/{self.test_project_id}/document/update",
                json=update_data
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        data.get("success") and
                        "document" in data and
                        data["document"].get("version", 0) > 1
                    )
                    
                    self.log_test_result(
                        "文档AI集成",
                        success,
                        f"文档版本: {data['document'].get('version', 0)}",
                        data
                    )
                else:
                    response_text = await response.text()
                    self.log_test_result(
                        "文档AI集成", 
                        False, 
                        f"HTTP {response.status}",
                        response_text
                    )
                    
        except Exception as e:
            self.log_test_result("文档AI集成", False, f"请求异常: {str(e)}")
    
    async def test_development_workflow(self):
        """测试开发工作流程 - 深度集成多AI系统"""
        if not self.test_project_id:
            self.log_test_result("开发工作流程", False, "项目ID不存在，跳过测试")
            return
        
        try:
            # 启动开发流程
            async with self.session.post(
                f"{self.api_base}/projects/{self.test_project_id}/development/start"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        data.get("success") and
                        "task_id" in data
                    )
                    
                    self.log_test_result(
                        "开发工作流程启动",
                        success,
                        f"任务ID: {data.get('task_id')}",
                        data
                    )
                    
                    # 等待一段时间让开发流程运行
                    await asyncio.sleep(5)
                    
                    # 检查开发状态
                    await self.test_development_status()
                    
                else:
                    response_text = await response.text()
                    self.log_test_result(
                        "开发工作流程启动", 
                        False, 
                        f"HTTP {response.status}",
                        response_text
                    )
                    
        except Exception as e:
            self.log_test_result("开发工作流程启动", False, f"请求异常: {str(e)}")
    
    async def test_development_status(self):
        """测试开发状态查询"""
        if not self.test_project_id:
            self.log_test_result("开发状态查询", False, "项目ID不存在，跳过测试")
            return
        
        try:
            async with self.session.get(
                f"{self.api_base}/projects/{self.test_project_id}/development/status"
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    success = (
                        data.get("success") and
                        "status" in data
                    )
                    
                    self.log_test_result(
                        "开发状态查询",
                        success,
                        f"状态: {data.get('status', {}).get('status', 'unknown')}",
                        data
                    )
                else:
                    response_text = await response.text()
                    self.log_test_result(
                        "开发状态查询", 
                        False, 
                        f"HTTP {response.status}",
                        response_text
                    )
                    
        except Exception as e:
            self.log_test_result("开发状态查询", False, f"请求异常: {str(e)}")
    
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        try:
            import websockets
            
            ws_url = f"ws://localhost:8000/ws/{self.test_user_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # 发送ping消息
                ping_message = json.dumps({
                    "type": "ping",
                    "timestamp": time.time()
                })
                
                await websocket.send(ping_message)
                
                # 等待响应
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                success = response_data.get("type") == "pong"
                self.log_test_result(
                    "WebSocket连接",
                    success,
                    f"响应类型: {response_data.get('type')}",
                    response_data
                )
                
        except Exception as e:
            self.log_test_result("WebSocket连接", False, f"连接异常: {str(e)}")
    
    async def test_ai_coordinator_integration(self):
        """测试AI协调器集成"""
        try:
            # 直接测试AI协调器
            work_dir = current_dir / "test_workspace"
            work_dir.mkdir(exist_ok=True)
            
            ai_coordinator = AICoordinator(str(work_dir))
            await ai_coordinator.initialize()
            
            # 测试AI服务是否正确初始化
            success = (
                ai_coordinator.document_ai is not None and
                ai_coordinator.frontend_ai is not None and
                ai_coordinator.transfer_ai is not None
            )
            
            self.log_test_result(
                "AI协调器集成",
                success,
                "AI服务初始化完成",
                {
                    "document_ai": ai_coordinator.document_ai is not None,
                    "frontend_ai": ai_coordinator.frontend_ai is not None,
                    "transfer_ai": ai_coordinator.transfer_ai is not None
                }
            )
            
            await ai_coordinator.cleanup()
            
        except Exception as e:
            self.log_test_result("AI协调器集成", False, f"初始化异常: {str(e)}")
    
    async def test_shared_memory_integration(self):
        """测试共享记忆系统集成"""
        try:
            memory_path = current_dir / "test_memory"
            memory_path.mkdir(exist_ok=True)
            
            shared_memory = SharedMemoryManager(str(memory_path))
            
            # 测试记忆存储和检索
            test_key = "test_project_memory"
            test_data = {
                "project_id": self.test_project_id or "test_project",
                "development_history": ["初始化", "文档生成", "开发启动"],
                "ai_interactions": 5
            }
            
            # 存储记忆
            await shared_memory.store_memory(test_key, test_data)
            
            # 检索记忆
            retrieved_data = await shared_memory.get_memory(test_key)
            
            success = (
                retrieved_data is not None and
                retrieved_data.get("project_id") == test_data["project_id"] and
                len(retrieved_data.get("development_history", [])) == 3
            )
            
            self.log_test_result(
                "共享记忆系统集成",
                success,
                "记忆存储和检索成功",
                {
                    "stored": test_data,
                    "retrieved": retrieved_data
                }
            )
            
        except Exception as e:
            self.log_test_result("共享记忆系统集成", False, f"操作异常: {str(e)}")
    
    async def test_multi_ai_orchestrator_integration(self):
        """测试多AI编排器集成"""
        try:
            work_dir = current_dir / "test_orchestrator"
            work_dir.mkdir(exist_ok=True)
            
            # 创建编排器实例
            orchestrator = MultiAIOrchestrator(
                work_dir=str(work_dir),
                ai_config={'model_name': 'gpt-4o', 'temperature': 0.1},
                workflow_config={
                    'max_dev_iterations': 2,
                    'package_type': 'zip',
                    'include_frontend': False,
                    'auto_deploy': False
                }
            )
            
            # 测试组件初始化
            success = (
                orchestrator.dev_ai is not None and
                orchestrator.supervisor_ai is not None and
                orchestrator.test_ai is not None and
                orchestrator.deploy_ai is not None
            )
            
            self.log_test_result(
                "多AI编排器集成",
                success,
                "编排器组件初始化完成",
                {
                    "dev_ai": orchestrator.dev_ai is not None,
                    "supervisor_ai": orchestrator.supervisor_ai is not None,
                    "test_ai": orchestrator.test_ai is not None,
                    "deploy_ai": orchestrator.deploy_ai is not None
                }
            )
            
        except Exception as e:
            self.log_test_result("多AI编排器集成", False, f"初始化异常: {str(e)}")
    
    async def test_database_integration(self):
        """测试数据库集成"""
        try:
            # 测试数据库连接和操作
            db_manager = DatabaseManager("test_platform.db")
            await db_manager.initialize()
            
            # 创建测试用户
            test_user = User(
                id=self.test_user_id,
                username="test_user",
                email="test@example.com"
            )
            
            user_saved = await db_manager.save_user(test_user)
            retrieved_user = await db_manager.get_user(self.test_user_id)
            
            success = (
                user_saved and
                retrieved_user is not None and
                retrieved_user.username == "test_user"
            )
            
            self.log_test_result(
                "数据库集成",
                success,
                f"用户操作成功，用户名: {retrieved_user.username if retrieved_user else 'None'}",
                {
                    "user_saved": user_saved,
                    "user_retrieved": retrieved_user is not None
                }
            )
            
            await db_manager.cleanup()
            
        except Exception as e:
            self.log_test_result("数据库集成", False, f"数据库异常: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有集成测试"""
        print("🚀 开始Web平台集成测试")
        print("=" * 50)
        
        await self.setup()
        
        # 运行测试套件
        test_methods = [
            self.test_api_health,
            self.test_database_integration,
            self.test_ai_coordinator_integration,
            self.test_shared_memory_integration,
            self.test_multi_ai_orchestrator_integration,
            self.test_websocket_connection,
            self.test_project_creation,
            self.test_document_ai_integration,
            self.test_development_workflow,
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(1)  # 测试间隔
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ')
                self.log_test_result(test_name, False, f"测试异常: {str(e)}")
        
        await self.teardown()
        
        # 输出测试结果摘要
        self.print_test_summary()
    
    def print_test_summary(self):
        """输出测试结果摘要"""
        print("\n" + "=" * 50)
        print("🏁 测试结果摘要")
        print("=" * 50)
        
        print(f"总测试数: {self.total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.total_tests - self.passed_tests}")
        print(f"通过率: {(self.passed_tests / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "0%")
        
        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']}")
        
        # 判断整体测试结果
        if self.passed_tests == self.total_tests:
            print("\n🎉 所有测试通过！Web平台已正确集成多AI协作系统。")
            return True
        else:
            print(f"\n⚠️ 有 {self.total_tests - self.passed_tests} 个测试失败，请检查集成问题。")
            return False

async def main():
    """主函数"""
    print("多AI协作开发平台 - 集成测试")
    print("验证Web平台是否正确深度集成现有的多AI系统")
    print("")
    
    # 检查环境
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ 警告: 未设置 OPENAI_API_KEY 环境变量")
        print("某些AI功能测试可能会失败")
        print("")
    
    # 运行测试
    tester = WebPlatformIntegrationTest()
    success = await tester.run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())