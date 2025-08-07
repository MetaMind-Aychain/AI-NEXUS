#!/usr/bin/env python3
"""
真实多AI协作开发测试

模拟完整的用户使用流程：
1. 用户输入需求
2. 文档AI分析需求生成开发文档
3. 用户确认文档
4. 开发AI（集成GPT-ENGINEER）真正开发代码
5. 监督AI持续监督
6. 测试AI进行测试
7. 前端AI开发界面
8. 部署AI进行部署
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "web_platform" / "backend"))

# 导入多AI系统组件
from multi_ai_system.core.deep_integration import DeepIntegratedDevAI, DeepIntegrationManager
from multi_ai_system.ai.advanced_document_ai import AdvancedDocumentAI
from multi_ai_system.ai.advanced_supervisor_ai import AdvancedSupervisorAI
from multi_ai_system.ai.advanced_test_ai import AdvancedTestAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager
from web_platform.backend.ai_coordinator import AICoordinator
from web_platform.backend.database import DatabaseManager
from web_platform.backend.models import CreateProjectDTO, ProjectStatus

# GPT-Engineer 组件
from gpt_engineer.core.ai import AI
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv


class RealMultiAITest:
    """真实多AI协作测试系统"""
    
    def __init__(self):
        print("🚀 初始化真实多AI协作系统...")
        
        # 初始化共享记忆
        self.shared_memory = SharedMemoryManager("./real_ai_memory")
        
        # 初始化数据库
        self.db = DatabaseManager()
        
        # 初始化AI协调器
        self.ai_coordinator = AICoordinator()
        
        # 初始化AI引擎
        ai_engine = AI()
        
        # 初始化各个AI
        self.document_ai = AdvancedDocumentAI(ai_engine, self.shared_memory)
        self.supervisor_ai = AdvancedSupervisorAI(ai_engine, self.shared_memory)
        self.test_ai = AdvancedTestAI(ai_engine, self.shared_memory)
        
        # 初始化深度集成的开发AI
        self.init_development_ai()
        
        print("✅ 真实多AI协作系统初始化完成")
    
    def init_development_ai(self):
        """初始化深度集成的开发AI"""
        print("🔧 初始化深度集成的开发AI...")
        
        # 创建项目目录
        project_dir = Path("real_ai_projects")
        project_dir.mkdir(exist_ok=True)
        
        # 初始化GPT-Engineer组件
        memory = DiskMemory(str(project_dir))
        execution_env = DiskExecutionEnv()
        ai = AI()
        
        # 创建深度集成的开发AI
        self.development_ai = DeepIntegratedDevAI(
            memory=memory,
            execution_env=execution_env,
            ai=ai,
            supervisor_ai=self.supervisor_ai,
            test_ai=self.test_ai,
            shared_memory=self.shared_memory
        )
        
        print("✅ 深度集成开发AI初始化完成")
    
    async def simulate_user_workflow(self, user_requirement: str):
        """模拟完整的用户工作流程"""
        print(f"\n{'='*80}")
        print(f"🎯 开始真实AI协作开发流程")
        print(f"{'='*80}")
        
        project_id = f"ai_project_{int(time.time())}"
        
        try:
            # 第1步：用户输入需求
            print(f"\n📝 第1步：用户输入需求")
            print(f"需求内容：{user_requirement}")
            
            # 保存到共享记忆
            await self.shared_memory.store_project_context(project_id, {
                "user_requirement": user_requirement,
                "start_time": datetime.now().isoformat(),
                "status": "需求收集"
            })
            
            # 第2步：文档AI分析需求生成开发文档
            print(f"\n📋 第2步：文档AI分析需求...")
            document_result = await self.document_ai.analyze_requirements(user_requirement)
            
            print(f"✅ 文档AI生成结果：")
            print(f"   - 项目名称：{document_result.get('project_name', 'N/A')}")
            print(f"   - 技术栈：{', '.join(document_result.get('tech_stack', []))}")
            print(f"   - 功能模块：{len(document_result.get('features', []))} 个")
            
            # 保存文档到共享记忆
            await self.shared_memory.store_project_context(project_id, {
                "document": document_result,
                "status": "文档生成完成"
            })
            
            # 第3步：用户确认文档（模拟自动确认）
            print(f"\n✅ 第3步：用户确认文档")
            print(f"模拟用户确认文档内容...")
            
            await self.shared_memory.store_project_context(project_id, {
                "document_confirmed": True,
                "status": "文档已确认"
            })
            
            # 第4步：开发AI开始真实开发
            print(f"\n💻 第4步：开发AI开始真实代码开发...")
            print(f"使用深度集成的GPT-ENGINEER进行开发...")
            
            # 启动监督AI
            supervision_task = asyncio.create_task(
                self.supervisor_ai.monitor_development_process(project_id, document_result)
            )
            
            # 开发AI开始工作
            development_result = await self.development_ai.develop_project_from_document(
                project_id, document_result
            )
            
            print(f"✅ 开发AI完成代码生成：")
            print(f"   - 生成文件数：{len(development_result.get('files', {}))}")
            print(f"   - 项目路径：{development_result.get('project_path', 'N/A')}")
            
            # 第5步：测试AI进行测试
            print(f"\n🧪 第5步：测试AI执行测试...")
            test_result = await self.test_ai.comprehensive_test(
                project_id, development_result
            )
            
            print(f"✅ 测试完成：")
            print(f"   - 测试通过率：{test_result.get('pass_rate', 0):.1%}")
            print(f"   - 发现问题：{len(test_result.get('issues', []))} 个")
            
            # 如果有问题，让开发AI修复
            if test_result.get('issues'):
                print(f"\n🔧 发现问题，开发AI开始修复...")
                fix_result = await self.development_ai.fix_issues(
                    project_id, test_result.get('issues', [])
                )
                print(f"✅ 问题修复完成")
            
            # 第6步：前端AI开发界面（如果需要）
            if "frontend" in document_result.get('tech_stack', []):
                print(f"\n🎨 第6步：前端AI开发用户界面...")
                frontend_result = await self.ai_coordinator.develop_frontend(
                    project_id, development_result
                )
                print(f"✅ 前端开发完成")
            
            # 第7步：集成测试
            print(f"\n🔗 第7步：系统集成测试...")
            integration_result = await self.test_ai.integration_test(
                project_id, development_result
            )
            
            print(f"✅ 集成测试完成：")
            print(f"   - 集成成功：{integration_result.get('success', False)}")
            
            # 第8步：部署准备
            print(f"\n🚀 第8步：准备项目部署...")
            deployment_result = await self.ai_coordinator.prepare_deployment(
                project_id, development_result
            )
            
            print(f"✅ 部署准备完成：")
            print(f"   - 部署包：{deployment_result.get('package_path', 'N/A')}")
            print(f"   - 访问地址：{deployment_result.get('url', 'N/A')}")
            
            # 停止监督任务
            supervision_task.cancel()
            
            # 保存最终结果
            final_result = {
                "project_id": project_id,
                "user_requirement": user_requirement,
                "document": document_result,
                "development": development_result,
                "test_result": test_result,
                "integration_result": integration_result,
                "deployment_result": deployment_result,
                "completion_time": datetime.now().isoformat(),
                "status": "项目完成"
            }
            
            await self.shared_memory.store_project_context(project_id, final_result)
            
            # 显示完成摘要
            self.show_completion_summary(final_result)
            
            return final_result
            
        except Exception as e:
            print(f"❌ AI协作开发过程中发生错误：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def show_completion_summary(self, result: dict):
        """显示项目完成摘要"""
        print(f"\n{'='*80}")
        print(f"🎉 真实AI协作开发完成！")
        print(f"{'='*80}")
        
        print(f"📊 项目信息：")
        print(f"   项目ID：{result['project_id']}")
        print(f"   项目名称：{result.get('document', {}).get('project_name', 'N/A')}")
        print(f"   开始时间：{result.get('start_time', 'N/A')}")
        print(f"   完成时间：{result.get('completion_time', 'N/A')}")
        
        print(f"\n🤖 AI协作结果：")
        print(f"   📋 文档AI：需求分析完成")
        print(f"   💻 开发AI：代码生成完成 ({len(result.get('development', {}).get('files', {}))} 个文件)")
        print(f"   👁️ 监督AI：开发过程监督完成")
        print(f"   🧪 测试AI：测试执行完成 (通过率 {result.get('test_result', {}).get('pass_rate', 0):.1%})")
        print(f"   🚀 部署AI：部署准备完成")
        
        if result.get('development', {}).get('project_path'):
            print(f"\n📁 项目文件：")
            print(f"   本地路径：{result['development']['project_path']}")
        
        if result.get('deployment_result', {}).get('url'):
            print(f"\n🌐 在线访问：")
            print(f"   访问地址：{result['deployment_result']['url']}")
        
        print(f"\n✨ AI协作开发流程完全自动化完成！")


async def main():
    """主函数"""
    print("🎯 真实多AI协作开发测试")
    print("使用文档AI、开发AI（GPT-ENGINEER）、监督AI、测试AI等真实协作")
    
    # 创建测试系统
    test_system = RealMultiAITest()
    
    # 用户需求示例
    user_requirements = [
        "我需要一个电商平台，包含用户注册登录、商品管理、购物车、订单处理、支付系统等功能，要有管理后台和用户前端",
        "创建一个博客系统，支持文章发布、评论、分类、标签、用户管理，要有响应式设计",
        "开发一个任务管理系统，包含项目管理、任务分配、进度跟踪、团队协作功能"
    ]
    
    print(f"\n📝 请选择测试需求：")
    for i, req in enumerate(user_requirements, 1):
        print(f"  {i}. {req[:50]}...")
    print(f"  {len(user_requirements) + 1}. 自定义输入")
    
    # 获取用户选择
    while True:
        try:
            choice = input(f"\n请选择 (1-{len(user_requirements) + 1}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(user_requirements):
                selected_requirement = user_requirements[int(choice) - 1]
                break
            elif choice == str(len(user_requirements) + 1):
                selected_requirement = input("请输入您的需求: ").strip()
                if selected_requirement:
                    break
            print("请输入有效选项")
        except KeyboardInterrupt:
            print("\n👋 退出测试")
            return
    
    print(f"\n🚀 开始真实AI协作开发...")
    print(f"用户需求：{selected_requirement}")
    
    # 执行真实AI协作开发
    result = await test_system.simulate_user_workflow(selected_requirement)
    
    if result:
        print(f"\n🎉 真实AI协作开发测试成功完成！")
        
        # 询问是否查看生成的文件
        if result.get('development', {}).get('project_path'):
            view_files = input(f"\n是否查看生成的项目文件？(y/n): ").strip().lower()
            if view_files in ['y', 'yes', '是']:
                project_path = Path(result['development']['project_path'])
                if project_path.exists():
                    print(f"\n📂 项目文件列表：")
                    for file_path in project_path.rglob('*'):
                        if file_path.is_file():
                            print(f"   - {file_path.relative_to(project_path)}")
    else:
        print(f"\n❌ 真实AI协作开发测试失败")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试发生错误：{e}")
        import traceback
        traceback.print_exc()